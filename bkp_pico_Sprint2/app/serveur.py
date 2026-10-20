# Serveur web minimal (asyncio) avec deux modes visibles sur la page.
#
#   GET  /                 MODE UTILISATEUR : contenu des 4 récipients + cocktails réalisables
#   GET  /admin            MODE ADMINISTRATEUR : choix de l'ingrédient de chaque récipient + recettes chargées
#   POST /ingredients      enregistre les 4 récipients (refuse un doublon ou un ingrédient inconnu)
#   GET  /static/<nom>     style.css, logo.png, favicon.png (dossier web/)
#   GET  /api/ingredients  {"recipients": [...], "connus": [...]}
#   GET  /api/recettes     contenu de data/recettes.json
#
# Le mode administrateur n'est PAS protégé par un PIN (US4.3 est remplacée par US1.2 pour l'instant) :
# n'importe qui sur le réseau de la machine peut ouvrir /admin. Le HTML est dans pages.py.
import asyncio
import json
import os

from app import config, ingredients, pages, recettes

_etat = {"data": None, "erreur": None}   # contenu validé de recettes.json, ou message d'erreur

# Seuls ces fichiers de web/ sont servis (liste fermée : pas de lecture d'un autre fichier de la Pico).
_STATIQUE = {
    "style.css": "text/css; charset=utf-8",
    "logo.png": "image/png",
    "favicon.png": "image/png",
}


def _charger_recettes():
    try:
        _etat["data"] = recettes.charger()
        _etat["erreur"] = None
    except Exception as e:
        _etat["data"] = None
        _etat["erreur"] = str(e)
        print("recettes.json refusé :", e)


def _connus():
    return _etat["data"]["ingredients"] if _etat["data"] else []


# --- petits outils (MicroPython n'a pas urllib.parse) ----------------------------------------
def _decoder(s):
    s = s.replace("+", " ")
    octets = bytearray()
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "%" and i + 2 < n:
            try:
                octets.append(int(s[i + 1:i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass
        octets.extend(c.encode())
        i += 1
    return bytes(octets).decode()


def _parse_form(corps):
    champs = {}
    for paire in corps.split("&"):
        if not paire:
            continue
        cle, _, valeur = paire.partition("=")
        champs[_decoder(cle)] = _decoder(valeur)
    return champs


# --- HTTP ------------------------------------------------------------------------------------
_RAISONS = {200: "OK", 303: "See Other", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed"}


async def _repondre(w, code, corps, type_="text/html; charset=utf-8", extra=""):
    donnees = corps.encode("utf-8") if isinstance(corps, str) else corps
    entete = ("HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\n"
              "Connection: close\r\nCache-Control: no-store\r\n{}\r\n").format(
        code, _RAISONS.get(code, ""), type_, len(donnees), extra)
    w.write(entete.encode())
    w.write(donnees)
    await w.drain()


async def _json(w, objet):
    await _repondre(w, 200, json.dumps(objet), "application/json; charset=utf-8")


async def _envoyer_fichier(w, nom):
    """Envoie un fichier de web/ par blocs de 1 Ko (le logo ne tient pas d'un coup dans la mémoire)."""
    chemin = config.chemin(config.DOSSIER_WEB + nom)
    try:
        taille = os.stat(chemin)[6]
        f = open(chemin, "rb")
    except OSError:
        return await _repondre(w, 404, "Introuvable")
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
    for _ in range(40):
        h = await reader.readline()
        if h in (b"\r\n", b"\n", b""):
            break
        bas = h.decode().lower()
        if bas.startswith("content-length:"):
            longueur = int(bas.split(":", 1)[1].strip())
    if longueur > 4096:
        raise ValueError("corps trop grand")
    corps = await reader.readexactly(longueur) if longueur else b""
    return morceaux[0], morceaux[1], corps.decode()


async def _router(w, methode, cible, corps):
    chemin, _, requete = cible.partition("?")

    if chemin == "/":
        if methode != "GET":
            return await _repondre(w, 405, "Méthode non autorisée")
        return await _repondre(w, 200, pages.page_utilisateur(ingredients.charger(), _etat["data"], _etat["erreur"]))

    if chemin == "/admin":
        if methode != "GET":
            return await _repondre(w, 405, "Méthode non autorisée")
        recipients = ingredients.charger()
        message = None
        if "ok=1" in requete:
            n = len(recettes.realisables(_etat["data"], recipients)) if _etat["data"] else 0
            message = "Configuration enregistrée : {} cocktail(s) réalisable(s).".format(n)
        return await _repondre(w, 200, pages.page_admin(recipients, _etat["data"], _etat["erreur"], message=message))

    if chemin == "/ingredients":
        if methode != "POST":
            return await _repondre(w, 405, "Méthode non autorisée")
        champs = _parse_form(corps)
        choix = [champs.get("r{}".format(i + 1), "") for i in range(config.NB_RECIPIENTS)]
        try:
            ingredients.enregistrer(choix, _connus())
        except ValueError as e:
            return await _repondre(w, 400, pages.page_admin(choix, _etat["data"], _etat["erreur"], erreur=str(e)))
        return await _repondre(w, 303, "", extra="Location: /admin?ok=1\r\n")

    if chemin.startswith("/static/") and methode == "GET" and chemin[8:] in _STATIQUE:
        return await _envoyer_fichier(w, chemin[8:])

    if chemin == "/api/ingredients" and methode == "GET":
        return await _json(w, {"recipients": ingredients.charger(), "connus": _connus()})

    if chemin == "/api/recettes" and methode == "GET":
        return await _json(w, _etat["data"] if _etat["data"] else {"erreur": _etat["erreur"]})

    await _repondre(w, 404, "Introuvable")


async def _client(reader, writer):
    try:
        requete = await asyncio.wait_for(_lire(reader), 5)
        if requete is not None:
            await _router(writer, requete[0], requete[1], requete[2])
    except Exception as e:
        print("requête refusée :", e)
        try:
            await _repondre(writer, 400, "Requête invalide")
        except Exception:
            pass
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


async def lancer(port=None):
    _charger_recettes()
    await asyncio.start_server(_client, "0.0.0.0", port or config.PORT_WEB)
    print("Serveur web prêt sur le port", port or config.PORT_WEB)
    while True:
        await asyncio.sleep(1)
