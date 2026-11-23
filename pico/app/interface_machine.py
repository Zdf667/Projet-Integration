import asyncio

from app import boutons, catalogue, config, horloge, ingredients, recettes, reseau, sequenceur, st7789

LISTE, DETAIL, INFO, SUIVI, PRET, ARRET = "liste", "detail", "info", "suivi", "pret", "arret"

TITRE_H = 32               
PIED_Y = 214                
LIGNE_LISTE = 26            
NB_LIGNES = (PIED_Y - TITRE_H) // LIGNE_LISTE    
PAS_TEXTE = 22              
LETTRES = 14
CONTROLE_LISTE_MS = 3000     

NOIR, BLANC, GRIS, ROUGE, VERT, ORANGE = st7789.NOIR, st7789.BLANC, st7789.GRIS, st7789.ROUGE, st7789.VERT, st7789.ORANGE
GRIS_FONCE = st7789.couleur(50, 50, 50)

_ui = {
    "vue": LISTE,            
    "avant_info": LISTE,
    "liste": [],            
    "choix": 0,              
    "debut": 0,             
    "origine": "",          
    "message": "",           
}
_interne = {"ecran": None, "je_lance": False, "precedent": sequenceur.ATTENTE, "ecoute": False,
            "vue_affichee": None, "complete": None, "partielle": None, "choix_affiche": None}



def _sur_changement(etat):
    """Écouteur du séquenceur : retient qui a lancé la préparation. Doit rester très rapide (pas de dessin ici)."""
    if etat["etat"] == sequenceur.EN_COURS and _interne["precedent"] != sequenceur.EN_COURS:
        _ui["origine"] = "machine" if _interne["je_lance"] else "telephone"
    _interne["precedent"] = etat["etat"]


def realisables():
    """[(numéro dans recettes.json, recette)] des cocktails réalisables maintenant (même calcul que la page web)."""
    data = catalogue.data()
    if not data:
        return []
    possibles = recettes.realisables(data, ingredients.charger())
    return [(data["recettes"].index(r), r) for r in possibles]


def _cadrer():
    """Fait défiler la liste pour que le cocktail choisi reste visible."""
    if _ui["choix"] < _ui["debut"]:
        _ui["debut"] = _ui["choix"]
    elif _ui["choix"] >= _ui["debut"] + NB_LIGNES:
        _ui["debut"] = _ui["choix"] - NB_LIGNES + 1


def rafraichir_liste():
    """Recalcule la liste ; garde le même cocktail sélectionné s'il est encore réalisable."""
    ancienne = _ui["liste"]
    nouvelle = realisables()
    if [n for n, _ in nouvelle] == [n for n, _ in ancienne]:
        return False
    choisi = ancienne[_ui["choix"]][0] if _ui["choix"] < len(ancienne) else None
    _ui["liste"] = nouvelle
    _ui["choix"] = 0
    _ui["debut"] = 0
    for i, (n, _) in enumerate(nouvelle):
        if n == choisi:
            _ui["choix"] = i
    _cadrer()
    return True


def vue(etat=None):
    """Écran à afficher : la préparation en cours passe avant la navigation (sauf l'écran Info demandé)."""
    e = (etat or sequenceur.etat())["etat"]
    if _ui["vue"] == INFO:
        return INFO
    if e == sequenceur.EN_COURS:
        return SUIVI
    if e == sequenceur.TERMINE:
        return PRET
    if e == sequenceur.ERREUR:
        return ARRET
    if _ui["vue"] == DETAIL and not _ui["liste"]:
        _ui["vue"] = LISTE
    return _ui["vue"]


def _deplacer(pas):
    n = len(_ui["liste"])
    if n:
        _ui["choix"] = min(max(_ui["choix"] + pas, 0), n - 1)
        _cadrer()


def _lancer():
    if not _ui["liste"]:
        return
    _numero, recette = _ui["liste"][_ui["choix"]]
    _interne["je_lance"] = True
    try:
        sequenceur.servir(recette, ingredients.charger())      
    except sequenceur.Occupe:
        _ui["message"] = "Machine occupee"
    except ValueError as e:                              
        print("lancement refusé :", e)
        _ui["message"] = "Ingr. manquant"
        _ui["vue"] = LISTE
        rafraichir_liste()
    else:
        _ui["vue"] = LISTE          
    finally:
        _interne["je_lance"] = False


def appui(nom):
    """Réagit à un bouton ("haut", "bas", "ok", "retour", "info", "stop"). Aucun dessin ici."""
    _ui["message"] = ""
    if nom == "stop":
        sequenceur.arreter()        
        return
    v = vue()
    if v == INFO:
        if nom in ("info", "retour", "ok"):
            _ui["vue"] = _ui["avant_info"]
        return
    if nom == "info":
        _ui["avant_info"] = _ui["vue"]
        _ui["vue"] = INFO
        return
    if v == LISTE:
        if nom == "haut":
            _deplacer(-1)
        elif nom == "bas":
            _deplacer(1)
        elif nom == "ok" and _ui["liste"]:
            _ui["vue"] = DETAIL
    elif v == DETAIL:
        if nom == "haut":
            _deplacer(-1)
        elif nom == "bas":
            _deplacer(1)
        elif nom == "retour":
            _ui["vue"] = LISTE
        elif nom == "ok":
            _lancer()
    elif v in (PRET, ARRET):
        if nom in ("ok", "retour"):
            sequenceur.acquitter()  
            _ui["vue"] = LISTE
    


def lignes_info():
    """(titre, lignes) de l'écran Info : comment rejoindre la machine avec un téléphone."""
    i = reseau.info()
    if i.get("mode") == "ap":
        return "Point d'acces", ["Wi-Fi :", config.AP_SSID, "Mot de passe :", config.AP_MOT_DE_PASSE,
                                 "Ouvrir :", i.get("ip", ""), config.NOM_MACHINE + ".box"]
    if i.get("mode") == "client":
        return "Client Wi-Fi", ["Reseau :", i.get("ssid", ""), "Ouvrir :", i.get("ip", ""),
                                config.NOM_MACHINE + ".local"]
    return "Reseau", ["Pas de reseau", "(Wi-Fi non", "demarre)"]


def couper(texte, largeur=LETTRES):
    """Découpe un texte en lignes de `largeur` lettres, sans couper les mots quand c'est possible."""
    lignes, ligne = [], ""
    for mot in st7789.sans_accents(texte).split(" "):
        while len(mot) > largeur:
            if ligne:
                lignes.append(ligne)
                ligne = ""
            lignes.append(mot[:largeur])
            mot = mot[largeur:]
        if not ligne:
            ligne = mot
        elif len(ligne) + 1 + len(mot) <= largeur:
            ligne += " " + mot
        else:
            lignes.append(ligne)
            ligne = mot
    if ligne:
        lignes.append(ligne)
    return lignes


def _titre(ecran, texte, droite="", fond=ORANGE, encre=NOIR):
    ecran.rect(0, 0, 240, TITRE_H, fond)
    place = LETTRES - (len(droite) + 1 if droite else 0)
    ecran.texte(st7789.sans_accents(texte)[:place], 4, 8, encre, fond)
    if droite:
        ecran.texte(droite, 240 - 4 - 16 * len(droite), 8, encre, fond)


def _pied(ecran, aide, fond=GRIS_FONCE):
    if _ui["message"]:
        aide, fond = _ui["message"], ROUGE
    ecran.rect(0, PIED_Y, 240, 240 - PIED_Y, fond)
    ecran.texte(aide, 4, PIED_Y + 5, BLANC, fond)


async def _ecrire(ecran, lignes, y):
    """Lignes de texte l'une sous l'autre ; une ligne qui finit par « : » est une étiquette (en gris)."""
    for ligne in lignes:
        if y + 16 > PIED_Y:
            break
        ecran.texte(ligne, 4, y, GRIS if ligne.endswith(":") else BLANC)
        y += PAS_TEXTE
        await asyncio.sleep(0)


def _ligne_liste(ecran, i):
    y = TITRE_H + (i - _ui["debut"]) * LIGNE_LISTE
    choisi = i == _ui["choix"]
    fond = ORANGE if choisi else NOIR
    ecran.rect(0, y, 240, LIGNE_LISTE, fond)
    ecran.texte(_ui["liste"][i][1]["nom"], 4, y + 5, NOIR if choisi else BLANC, fond)


async def _dessiner_liste(ecran, etat, complet):
    liste = _ui["liste"]
    n = len(liste)
    compteur = "{}/{}".format(_ui["choix"] + 1, n) if n else ""
    if complet:
        ecran.effacer(NOIR)
        _titre(ecran, "Cocktails", compteur)
        if catalogue.erreur():
            await _ecrire(ecran, ["Recettes", "invalides :", "voir la page", "web"], 44)
        elif not n:
            await _ecrire(ecran, ["Aucun cocktail", "realisable.", "", "Remplir les", "recipients en", "mode admin", "(telephone)."], 44)
        else:
            for i in range(_ui["debut"], min(n, _ui["debut"] + NB_LIGNES)):
                _ligne_liste(ecran, i)
                await asyncio.sleep(0)
    else:                                       
        ancien = _interne["choix_affiche"]
        if ancien is not None and ancien != _ui["choix"] and ancien < n:
            _ligne_liste(ecran, ancien)
        if n:
            _ligne_liste(ecran, _ui["choix"])
        _titre(ecran, "Cocktails", compteur)
    _pied(ecran, "OK = Voir" if n else "Info = Reseau")
    _interne["choix_affiche"] = _ui["choix"]


async def _dessiner_detail(ecran, etat, complet):
    if complet:
        _numero, r = _ui["liste"][_ui["choix"]]
        ecran.effacer(NOIR)
        _titre(ecran, r["nom"])
        lignes = ["Total : {} ml".format(sum(l["ml"] for l in r["ingredients"]))]
        for l in r["ingredients"][:5]:
            lignes.append("{:<8}{:>4}ml".format(st7789.sans_accents(l["ingredient"])[:8], l["ml"]))
        if r.get("conseil"):
            lignes += ["A ajouter :"] + couper(", ".join(r["conseil"]))
        await _ecrire(ecran, lignes, 40)
    _pied(ecran, "OK = Lancer", VERT)


async def _dessiner_suivi(ecran, etat, complet):
    if complet:
        ecran.effacer(NOIR)
        _titre(ecran, etat["titre"] or "Preparation")
        if etat["mode"] == "nettoyage":
            qui = ["Nettoyage", "des lignes"]
        else:
            qui = ["Lance depuis :", "la machine" if _ui["origine"] == "machine" else "le telephone"]
        await _ecrire(ecran, qui, 40)
        ecran.rect(8, 94, 224, 28, BLANC)     
        _pied(ecran, "STOP = Arreter", ROUGE)
    k = 220 * etat["pct"] // 100
    ecran.rect(10, 96, k, 24, ORANGE)
    ecran.rect(10 + k, 96, 220 - k, 24, NOIR)
    ecran.texte("{:>3} %  {}/{}  ".format(etat["pct"], etat["etape"], etat["etapes"]), 4, 132, BLANC)
    ecran.texte("{:<14}".format(st7789.sans_accents(etat["message"])[:LETTRES]), 4, 160, GRIS)


async def _dessiner_fin(ecran, etat, complet):
    ecran.effacer(NOIR)
    if etat["etat"] == sequenceur.ERREUR:
        _titre(ecran, "Arret", fond=ROUGE, encre=BLANC)
        lignes = couper(etat["titre"]) + [""] + couper(etat["message"])
    else:
        _titre(ecran, etat["message"] or "Termine", fond=VERT)
        lignes = couper(etat["titre"])
        if etat["conseil"]:
            lignes += ["", "A ajouter :"] + [l for c in etat["conseil"] for l in couper("- " + c)]
    await _ecrire(ecran, lignes, 42)
    _pied(ecran, "OK = Retour")


async def _dessiner_info(ecran, etat, complet):
    titre, lignes = lignes_info()
    ecran.effacer(NOIR)
    _titre(ecran, titre)
    await _ecrire(ecran, [l for x in lignes for l in couper(x)], 40)
    _pied(ecran, "<- = Retour")


_DESSINS = {LISTE: _dessiner_liste, DETAIL: _dessiner_detail, SUIVI: _dessiner_suivi,
            PRET: _dessiner_fin, ARRET: _dessiner_fin, INFO: _dessiner_info}


def _cles(v, etat):
    """(clé complète, clé partielle) : si la 1re change on redessine tout l'écran, si la 2e change seulement un morceau."""
    if v == LISTE:
        return (v, tuple(n for n, _ in _ui["liste"]), _ui["debut"], catalogue.erreur()), (_ui["choix"], _ui["message"])
    if v == DETAIL:
        return (v, _ui["liste"][_ui["choix"]][0]), (_ui["message"],)
    if v == SUIVI:
        return (v, etat["titre"], etat["mode"], _ui["origine"]), (etat["pct"], etat["etape"], etat["message"])
    if v in (PRET, ARRET):
        return (v, etat["titre"], etat["message"], tuple(etat["conseil"])), ()
    titre, lignes = lignes_info()
    return (v, titre, tuple(lignes)), ()


async def afficher(ecran):
    """Met l'écran à jour si quelque chose a changé."""
    etat = sequenceur.etat()
    v = vue(etat)
    if v == LISTE and _interne["vue_affichee"] != LISTE:
        rafraichir_liste()                      
    complete, partielle = _cles(v, etat)
    if complete != _interne["complete"]:
        await _DESSINS[v](ecran, etat, True)
    elif partielle != _interne["partielle"]:
        await _DESSINS[v](ecran, etat, False)
    else:
        return
    _interne["complete"], _interne["partielle"], _interne["vue_affichee"] = complete, partielle, v

def _ecran():
    """L'écran, créé une seule fois (par ecran_demarrage() ou par boucle())."""
    if _interne["ecran"] is None:
        _interne["ecran"] = st7789.creer()
    return _interne["ecran"]

def ecran_demarrage():
    """À appeler dans main.py AVANT reseau.demarrer() : la recherche du Wi-Fi peut durer longtemps.

    Ne lève jamais d'erreur : sans écran, la machine démarre quand même.
    """
    try:
        ecran = _ecran()
        ecran.effacer(NOIR)
        _titre(ecran, "Demarrage")
        attente = config.WIFI_ESSAIS * config.DELAI_CLIENT_S
        for k, ligne in enumerate(["Recherche du", "Wi-Fi...", "", "Patientez", "jusqu'a {} s".format(attente)]):
            ecran.texte(ligne, 4, 44 + k * PAS_TEXTE, BLANC)
    except Exception as e:
        print("écran US4.5 indisponible :", e)
        
async def boucle(ecran=None):
    """Tâche asyncio : lit les boutons toutes les 10 ms et met l'écran à jour. Ne s'arrête jamais sur une erreur."""
    if ecran is None:
        try:
            ecran = _ecran()
        except Exception as e:                 
            print("écran US4.5 indisponible :", e)
            return
    if catalogue.data() is None and catalogue.erreur() is None:
        catalogue.charger()
    boutons.init()
    if not _interne["ecoute"]:
        sequenceur.ecouter(_sur_changement)
        _interne["ecoute"] = True
    rafraichir_liste()
    controle = horloge.ms()
    while True:
        try:
            for nom in boutons.scruter():
                appui(nom)
            if vue() == LISTE and horloge.ecart(horloge.ms(), controle) > CONTROLE_LISTE_MS:
                controle = horloge.ms()
                rafraichir_liste()
            await afficher(ecran)
        except Exception as e:
            print("interface machine :", e)
            await asyncio.sleep(1)
        await asyncio.sleep(boutons.PERIODE_MS / 1000)