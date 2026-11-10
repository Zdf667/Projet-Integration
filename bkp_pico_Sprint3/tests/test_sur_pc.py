# Tests sur PC (sans Pico) : python3 tests/test_sur_pc.py   (depuis le dossier pico/)
# Les broches sont simulées, les durées sont raccourcies avec de très grands débits.
import asyncio
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app import admin, catalogue, config, conseil, ingredients, led, nettoyage, pages_admin, pompes, recettes, reseau  # noqa: E402
from app import sequenceur, serveur  # noqa: E402

# Petit jeu de recettes (le test ne dépend pas du vrai data/recettes.json)
RECETTES = {
    "version": 1,
    "ingredients": ["Vodka", "Rhum", "Jus d'orange", "Jus de cranberry", "Cola"],
    "recettes": [
        {"nom": "Screwdriver", "ingredients": [{"ingredient": "Vodka", "ml": 50}, {"ingredient": "Jus d'orange", "ml": 150}],
         "conseil": ["Glaçons", "Tranche d'orange"]},
        {"nom": "Cape Codder", "ingredients": [{"ingredient": "Vodka", "ml": 50}, {"ingredient": "Jus de cranberry", "ml": 150}],
         "conseil": ["Glaçons"]},
        {"nom": "Madras", "ingredients": [{"ingredient": "Vodka", "ml": 40}, {"ingredient": "Jus d'orange", "ml": 100},
                                          {"ingredient": "Jus de cranberry", "ml": 50}], "conseil": []},
        {"nom": "Cuba libre", "ingredients": [{"ingredient": "Rhum", "ml": 50}, {"ingredient": "Cola", "ml": 150}],
         "conseil": ["Citron vert"]},
    ],
}
TMP = tempfile.mkdtemp()
os.makedirs(TMP + "/data")
with open(TMP + "/data/recettes.json", "w", encoding="utf-8") as f:
    json.dump(RECETTES, f)
config.DOSSIER = TMP + "/"
RAPIDE = (5000.0, 5000.0, 5000.0, 5000.0)
LENT = (100.0, 100.0, 100.0, 100.0)
ok = 0


def verifie(condition, message):
    global ok
    if not condition:
        raise AssertionError(message)
    ok += 1


class Ecrivain:
    def __init__(self):
        self.octets = b""

    def write(self, b):
        self.octets += b

    async def drain(self):
        pass

    def code(self):
        return int(self.octets.split(b" ", 2)[1])

    def texte(self):
        return self.octets.decode("utf-8", "replace")


async def requete(methode, cible, corps="", cookie=""):
    w = Ecrivain()
    await serveur._router(w, methode, cible, corps, cookie)
    return w


def lire_jeton(w):
    for ligne in w.texte().split("\r\n"):
        if ligne.startswith("Set-Cookie: sid="):
            return ligne.split("sid=")[1].split(";")[0]
    return ""


async def attendre_fin(delai=3):
    for _ in range(int(delai * 100)):
        if sequenceur.etat()["etat"] != "en_cours":
            return
        await asyncio.sleep(0.01)
    raise AssertionError("préparation trop longue")


def test_pompes():
    pompes.init()
    verifie(all(not pompes.est_allumee(n) for n in range(1, 5)), "les pompes démarrent éteintes")
    verifie(all(b.value() == 1 for b in pompes._broches), "relais actif bas : éteint = 1")
    pompes.pump_on(2)
    verifie(pompes._broches[1].value() == 0 and pompes.est_allumee(2), "pump_on(2) met la broche à 0")
    verifie(not pompes.est_allumee(1), "les autres pompes restent éteintes")
    pompes.stop_all()
    verifie(not pompes.est_allumee(2), "stop_all éteint tout")
    for mauvais in (0, 5, "1"):
        try:
            pompes.pump_on(mauvais)
            verifie(False, "pompe inconnue refusée")
        except ValueError:
            verifie(True, "")
    verifie(abs(pompes.duree_pour(1, 100) - 100 / 2.23) < 1e-9, "durée = ml / débit")
    try:
        pompes.duree_pour(1, 10000)
        verifie(False, "durée maximale")
    except ValueError:
        verifie(True, "")


def test_planification(data):
    r = data["recettes"][0]                       # Screwdriver : Vodka 50, Jus d'orange 150
    plan = sequenceur.planifier(r, ["Jus d'orange", None, "Vodka", None])
    verifie([(p[0], p[1]) for p in plan] == [(3, 50), (1, 150)], "chaque ingrédient va sur la bonne pompe")
    try:
        sequenceur.planifier(r, ["Vodka", None, None, None])
        verifie(False, "ingrédient absent")
    except ValueError:
        verifie(True, "")
    verifie(len(nettoyage.plan()) == 4, "le nettoyage rince 4 lignes")


async def test_sequenceur(data):
    r = data["recettes"][0]
    recipients = ["Vodka", "Jus d'orange", None, None]
    config.DEBITS_ML_S = RAPIDE
    vus = []
    sequenceur.ecouter(lambda e: vus.append(e["etat"]))
    sequenceur.servir(r, recipients)
    verifie(sequenceur.etat()["etat"] == "en_cours", "en cours juste après servir")
    try:
        sequenceur.servir(r, recipients)
        verifie(False, "une seule préparation à la fois")
    except sequenceur.Occupe:
        verifie(True, "")
    await attendre_fin()
    e = sequenceur.etat()
    verifie(e["etat"] == "termine" and e["pct"] == 100 and e["conseil"] == r["conseil"], "terminé avec conseil")
    verifie(all(not pompes.est_allumee(n) for n in range(1, 5)), "pompes éteintes à la fin")
    verifie("en_cours" in vus and vus[-1] == "termine", "les écouteurs reçoivent les changements")
    sequenceur.acquitter()
    verifie(sequenceur.etat()["etat"] == "attente", "retour à attente")

    # arrêt en cours de route
    config.DEBITS_ML_S = LENT
    sequenceur.servir(r, recipients)
    await asyncio.sleep(0.2)
    verifie(pompes.est_allumee(1), "la pompe 1 tourne")
    verifie(sequenceur.arreter(), "arrêt accepté")
    verifie(all(not pompes.est_allumee(n) for n in range(1, 5)), "arrêt immédiat des pompes")
    await asyncio.sleep(0.1)
    verifie(sequenceur.etat()["etat"] == "erreur" and not sequenceur.occupe(), "état erreur après arrêt")
    sequenceur.acquitter()
    config.DEBITS_ML_S = RAPIDE


def test_admin():
    verifie(admin.pin_correct("1234"), "PIN par défaut")
    try:
        admin.connecter("0000")
        verifie(False, "mauvais PIN")
    except ValueError:
        verifie(True, "")
    jeton = admin.connecter("1234")
    verifie(admin.verifier(jeton) and not admin.verifier("faux") and not admin.verifier(""), "jeton vérifié")
    admin.deconnecter()
    verifie(not admin.verifier(jeton), "déconnexion")
    for _ in range(config.ESSAIS_MAX):
        try:
            admin.connecter("9999")
        except ValueError:
            pass
    try:
        admin.connecter("1234")
        verifie(False, "bloqué après trop d'essais")
    except ValueError as e:
        verifie("Trop d'essais" in str(e), "message de blocage")
    admin._echecs.update(n=0, jusqua=None)
    jeton = admin.connecter("1234")
    ancien = config.DELAI_INACTIVITE_S
    config.DELAI_INACTIVITE_S = 0
    import time
    time.sleep(0.01)
    verifie(not admin.verifier(jeton), "session expirée par inactivité")
    config.DELAI_INACTIVITE_S = ancien
    for nouveau, conf in (("12", "12"), ("1234", "4321"), ("abcd", "abcd")):
        try:
            admin.definir_pin(nouveau, conf)
            verifie(False, "PIN refusé")
        except ValueError:
            verifie(True, "")
    admin.definir_pin("4321", "4321")
    verifie(admin.pin_correct("4321") and not admin.pin_correct("1234") and "4321" not in open(config.chemin_data(config.FICHIER_ADMIN)).read(), "nouveau PIN enregistré")
    admin.definir_pin("1234", "1234")


def test_reseau():
    for ssid, mdp in (("", ""), ("x" * 33, ""), ("Box", "court")):
        try:
            reseau.enregistrer_identifiants(ssid, mdp)
            verifie(False, "Wi-Fi refusé")
        except ValueError:
            verifie(True, "")
    verifie(reseau.lire_reseaux() == [], "rien d'enregistré")
    reseau.enregistrer_identifiants("MaBox", "motdepasse1")
    reseau.enregistrer_identifiants("Ecole", "")
    verifie([r["ssid"] for r in reseau.lire_reseaux()] == ["MaBox", "Ecole"], "le nouveau réseau s'ajoute aux anciens")
    reseau.enregistrer_identifiants("MaBox", "autremotdepasse")
    verifie(len(reseau.lire_reseaux()) == 2 and reseau.lire_reseaux()[1]["mot_de_passe"] == "autremotdepasse", "même réseau : mot de passe mis à jour")
    reseau.oublier_reseau("Ecole")
    verifie([r["ssid"] for r in reseau.lire_reseaux()] == ["MaBox"], "oubli d'un seul réseau")
    try:
        reseau.oublier_reseau("Inconnu")
        verifie(False, "réseau inconnu")
    except ValueError:
        verifie(True, "")
    from app import storage
    storage.ecrire_json(config.chemin_data(config.FICHIER_WIFI), {"ssid": "Ancien", "mot_de_passe": "12345678"})
    verifie(reseau.lire_reseaux() == [{"ssid": "Ancien", "mot_de_passe": "12345678"}], "ancien format relu")
    reseau.oublier_identifiants()
    verifie(reseau.lire_reseaux() == [], "tout oublier")
    for i in range(config.WIFI_MAX):
        reseau.enregistrer_identifiants("R{}".format(i), "")
    try:
        reseau.enregistrer_identifiants("Trop", "")
        verifie(False, "limite de réseaux")
    except ValueError:
        verifie(True, "")
    reseau.oublier_identifiants()


def test_led():
    base = {"etat": "attente", "mode": "", "pct": 0}
    n = config.LED_NB
    verifie(led.nom_motif(base) == "attente" and led.couleurs(base, 0) == [led.VERT_DOUX] * n, "prête : ruban vert doux")
    cours = {"etat": "en_cours", "mode": "cocktail", "pct": 50}
    image = led.couleurs(cours, 0)
    verifie(len(image) == n and image[:13] == [led.ORANGE] * 13 and image[14:] == [led.ETEINT] * (n - 14), "en cours : barre à 50 %")
    verifie(led.couleurs(dict(cours, pct=100), 0) == [led.ORANGE] * n, "en cours : barre pleine à 100 %")
    verifie(led.couleurs(dict(cours, pct=0), 0).count(led.ORANGE) == 0, "en cours : barre vide à 0 %")
    net = {"etat": "en_cours", "mode": "nettoyage", "pct": 10}
    verifie(led.nom_motif(net) == "nettoyage" and led.couleurs(net, 0).count(led.VIOLET) == 5, "nettoyage : train de 5 LED")
    verifie(led.couleurs(net, 0) != led.couleurs(net, 400), "nettoyage : le train avance")
    fini = {"etat": "termine", "mode": "cocktail", "pct": 100}
    verifie(led.couleurs(fini, 0)[0] == led.VERT and led.couleurs(fini, 200)[0] == led.ETEINT, "verre prêt : flashs verts")
    err = {"etat": "erreur", "mode": "", "pct": 0}
    verifie(led.couleurs(err, 0)[0] == led.ETEINT and led.couleurs(err, 200)[0] == led.ROUGE, "erreur : clignotement rouge")
    verifie(all(len(led.couleurs(e, t)) == n for e in (base, cours, net, fini, err) for t in (0, 100, 999)), "toujours 26 LED")
    verifie(led._echelle((255, 100, 0)) == (int(255 * config.LED_LUMINOSITE), int(100 * config.LED_LUMINOSITE), 0), "luminosité limitée")


async def test_web(data):
    ingredients.enregistrer(["Vodka", "Jus d'orange", None, None], data["ingredients"])
    w = await requete("GET", "/")
    verifie(w.code() == 200 and "Screwdriver" in w.texte() and "/cocktail?id=0" in w.texte(), "liste des cocktails")
    w = await requete("GET", "/cocktail?id=0")
    verifie(w.code() == 200 and "Lancer la préparation" in w.texte() and "récipient 1" in w.texte(), "détail avant lancement")
    w = await requete("GET", "/cocktail?id=abc")
    verifie("Cocktail introuvable" in w.texte(), "id invalide")

    w = await requete("GET", "/admin")
    verifie(w.code() == 303 and "Location: /connexion" in w.texte(), "/admin demande le PIN")
    w = await requete("POST", "/ingredients", "r1=Rhum&r2=&r3=&r4=")
    verifie(w.code() == 303 and "/connexion" in w.texte(), "POST /ingredients protégé")
    w = await requete("POST", "/connexion", "pin=0000")
    verifie(w.code() == 400 and "Code incorrect" in w.texte(), "mauvais PIN refusé")
    w = await requete("POST", "/connexion", "pin=1234")
    jeton = lire_jeton(w)
    verifie(w.code() == 303 and jeton, "bon PIN : cookie de session")
    cookie = "sid=" + jeton
    w = await requete("GET", "/admin", cookie=cookie)
    verifie(w.code() == 200 and "Ingrédients des récipients" in w.texte() and "Nettoyage" in w.texte(), "admin connecté")
    w = await requete("POST", "/ingredients", "r1=Vodka&r2=Vodka&r3=&r4=", cookie=cookie)
    verifie(w.code() == 400 and "déjà" in w.texte(), "doublon refusé")
    w = await requete("POST", "/ingredients", "r1=Vodka&r2=Jus+d%27orange&r3=&r4=", cookie=cookie)
    verifie(w.code() == 303 and ingredients.charger()[1] == "Jus d'orange", "enregistrement des ingrédients")
    w = await requete("GET", "/admin/nettoyage", cookie=cookie)
    verifie("étape 1 sur 4" in w.texte(), "assistant de nettoyage")
    w = await requete("GET", "/admin/wifi", cookie=cookie)
    verifie(w.code() == 200 and "Ajouter un réseau" in w.texte() and "Tout oublier" in w.texte(), "page Wi-Fi")
    w = await requete("POST", "/admin/wifi", "ssid=&ssid_liste=&mdp=", cookie=cookie)
    verifie(w.code() == 400, "Wi-Fi vide refusé")
    w = await requete("POST", "/admin/pin", "nouveau=1&confirmation=1", cookie=cookie)
    verifie(w.code() == 400, "PIN trop court refusé")

    # servir un cocktail depuis la page web
    config.DEBITS_ML_S = RAPIDE
    w = await requete("POST", "/servir", "id=0")
    verifie(w.code() == 303 and "Location: /suivi" in w.texte(), "servir redirige vers le suivi")
    w = await requete("POST", "/servir", "id=0")
    verifie(w.code() == 409, "second cocktail refusé pendant la préparation")
    w = await requete("POST", "/ingredients", "r1=&r2=&r3=&r4=", cookie=cookie)
    verifie(w.code() == 409, "pas de changement d'ingrédient pendant une préparation")
    w = await requete("GET", "/suivi")
    verifie("Screwdriver" in w.texte(), "page de suivi")
    await attendre_fin()
    w = await requete("GET", "/status")
    verifie('"termine"' in w.texte(), "/status : terminé")
    w = await requete("GET", "/suivi")
    verifie("Verre prêt" in w.texte() and "Glaçons" in w.texte(), "verre prêt + conseil de service")
    w = await requete("POST", "/acquitter")
    verifie(w.code() == 303 and sequenceur.etat()["etat"] == "attente", "acquittement")
    w = await requete("POST", "/servir", "id=999")
    verifie(w.code() == 404, "cocktail inconnu")
    w = await requete("POST", "/servir", "id=3")           # ingrédients non chargés
    verifie(w.code() == 400 and "aucun récipient" in w.texte(), "ingrédient absent refusé")

    # nettoyage
    w = await requete("POST", "/admin/nettoyage", "action=lancer&etape=2", cookie=cookie)
    verifie(w.code() == 303 and sequenceur.etat()["mode"] == "nettoyage", "rinçage lancé")
    await attendre_fin()
    verifie(sequenceur.etat()["etat"] == "termine", "rinçage terminé")
    w = await requete("POST", "/admin/nettoyage", "action=suite&etape=2", cookie=cookie)
    verifie("etape=3" in w.texte() and sequenceur.etat()["etat"] == "attente", "étape suivante")

    w = await requete("GET", "/deconnexion")
    verifie("Max-Age=0" in w.texte(), "déconnexion")
    w = await requete("GET", "/admin", cookie=cookie)
    verifie(w.code() == 303, "session fermée")


def test_dns():
    import struct
    from app import dns
    print("-- DNS (nom de la machine)")

    def question(nom, type_):
        tete = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        corps = b"".join(bytes([len(p)]) + p.encode() for p in nom.split(".")) + b"\x00"
        return tete + corps + struct.pack(">HH", type_, 1)

    for nom in ("cocktail.local", "cocktail.box", "n-importe-quoi.com"):
        r = dns.reponse(question(nom, 1), "192.168.4.1")
        verifie(r[-4:] == bytes([192, 168, 4, 1]) and r[:2] == b"\x12\x34" and r[7] == 1, "DNS : " + nom + " -> 192.168.4.1")
    r = dns.reponse(question("cocktail.local", 28), "192.168.4.1")
    verifie(r[7] == 0 and r[3] & 15 == 0, "DNS : demande IPv6 -> réponse vide sans erreur")
    verifie(dns.reponse(b"abc", "192.168.4.1") is None, "DNS : paquet trop court ignoré")
    verifie(dns.reponse(r, "192.168.4.1") is None, "DNS : une réponse n'est pas traitée comme une question")


def test_conseil():
    verifie(conseil.texte(["Glaçons", "Menthe"]) == "Glaçons, Menthe" and conseil.texte([]) == "", "texte du conseil")
    verifie(conseil.html([]) == "" and "Glaçons" in conseil.html(["Glaçons"]), "encadré du conseil")
    verifie("<b>" not in conseil.html(["<b>x</b>"]), "conseil échappé")
    verifie("Citron vert" in conseil.html_recette(RECETTES["recettes"][3]), "conseil d'une recette")


def test_pages():
    sale = '<b>"x"&'
    html = pages_admin.page_admin([sale, None, None, None], {"ingredients": [sale], "recettes": []}, None)
    verifie("<b>" not in html.split("<main>")[1].split("Ingrédients des récipients")[1], "HTML échappé")


async def principal():
    data = recettes.charger()
    catalogue.charger()
    verifie(len(data["recettes"]) >= 1, "recettes chargées")
    test_pompes()
    test_planification(data)
    await test_sequenceur(data)
    test_admin()
    test_reseau()
    test_dns()
    test_led()
    test_conseil()
    test_pages()
    await test_web(data)


try:
    asyncio.run(principal())
    print("OK :", ok, "vérifications réussies")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
