# Serveur web minimal (asyncio). Il lit la requête et la passe aux modules de routes, chacun responsable de ses pages :
#
#   routes_user.py        mode utilisateur       /  /cocktail  /servir                      (US4.1, US2.3)
#   routes_suivi.py       suivi de préparation   /suivi  /status  /arreter  /acquitter       (US4.2)
#   routes_admin.py       mode admin (PIN)       /connexion  /deconnexion  /admin  /ingredients  /admin/pin   (US4.3)
#   routes_nettoyage.py   nettoyage guidé        /admin/nettoyage                            (US5.1)
#   routes_wifi.py        modes réseau           /admin/wifi  /admin/wifi/oublier            (US4.6)
#
# Ici : fichiers statiques (web/) et API JSON. Pour ajouter une page : créer un module routes_xxx.py avec une
# fonction traiter(...) et l'ajouter à ROUTES ci-dessous.
import asyncio
import gc
import os

from app import catalogue, config, ingredients, pompes
from app import routes_admin, routes_nettoyage, routes_suivi, routes_user, routes_wifi
from app.http_outils import repondre, reponse_json

# Ordre d'essai : le premier module qui reconnaît l'adresse répond.
ROUTES = (routes_user, routes_suivi, routes_admin, routes_nettoyage, routes_wifi)

_STATIQUE = {
    "style.css": "text/css; charset=utf-8",
    "logo.png": "image/png",
    "favicon.png": "image/png",
}


async def _envoyer_fichier(w, nom):
    """Envoie un fichier de web/ par blocs de 1 Ko (le logo ne tient pas d'un coup dans la mémoire)."""
    chemin = config.chemin(config.DOSSIER_WEB + nom)
    try:
        taille = os.stat(chemin)[6]
        f = open(chemin, "rb")
    except OSError:
        return await repondre(w, 404, "Introuvable")
    try:
        w.write(("HTTP/1.1 200 OK\r\nContent-Type: {}\r\nContent-Length: {}\r\nConnection: close\r\n"
                 "Cache-Control: public, max-age=300\r\n\r\n").format(_STATIQUE[nom], taille).encode())
        while True:
            bloc = f.read(1024)
            if not bloc:
                break
            w.write(bloc)
            await w.drain()
    finally:
        f.close()


async def _lire(reader):
    ligne = await reader.readline()
    if not ligne:
        return None
    morceaux = ligne.decode().split(" ")
    if len(morceaux) < 2:
        return None
    longueur = 0
    cookie = ""
    for _ in range(40):
        h = await reader.readline()
        if h in (b"\r\n", b"\n", b""):
            break
        texte = h.decode()
        bas = texte.lower()
        if bas.startswith("content-length:"):
            longueur = int(bas.split(":", 1)[1].strip())
        elif bas.startswith("cookie:"):
            cookie = texte.split(":", 1)[1].strip()
    if longueur > 4096:
        raise ValueError("corps trop grand")
    corps = await reader.readexactly(longueur) if longueur else b""
    return morceaux[0], morceaux[1], corps.decode(), cookie, cookie


async def _router(w, methode, cible, corps, cookie=""):
    chemin, _, requete = cible.partition("?")

    if chemin.startswith("/static/") and methode == "GET" and chemin[8:] in _STATIQUE:
        return await _envoyer_fichier(w, chemin[8:])
    if chemin == "/api/ingredients" and methode == "GET":
        return await reponse_json(w, {"recipients": ingredients.charger(), "connus": catalogue.connus()})
    if chemin == "/api/recettes" and methode == "GET":
        return await reponse_json(w, catalogue.data() if catalogue.data() else {"erreur": catalogue.erreur()})

    for module in ROUTES:
        if await module.traiter(w, methode, chemin, requete, corps, cookie):
            return
    await repondre(w, 404, "Introuvable")


async def _client(reader, writer):
    try:
        requete = await asyncio.wait_for(_lire(reader), 5)
        if requete is not None:
            await _router(writer, requete[0], requete[1], requete[2], requete[3])
    except Exception as e:
        print("requête refusée :", e)
        try:
            await repondre(writer, 400, "Requête invalide")
        except Exception:
            pass
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass
    gc.collect()


async def lancer(port=None):
    pompes.stop_all()          # au démarrage, aucune pompe ne doit tourner
    catalogue.charger()
    await asyncio.start_server(_client, "0.0.0.0", port or config.PORT_WEB)
    print("Serveur web prêt sur le port", port or config.PORT_WEB)
    while True:
        await asyncio.sleep(1)
