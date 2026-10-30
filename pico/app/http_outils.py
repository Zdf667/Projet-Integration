# Petits outils HTTP communs à toutes les routes (MicroPython n'a pas urllib.parse).
# Réponses, redirections, lecture d'un formulaire, lecture du cookie, contrôle de la session administrateur.
import json

from app import admin


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


def parse_form(corps):
    """'a=1&b=x+y' -> {'a': '1', 'b': 'x y'}"""
    champs = {}
    for paire in corps.split("&"):
        if not paire:
            continue
        cle, _, valeur = paire.partition("=")
        champs[_decoder(cle)] = _decoder(valeur)
    return champs


def cookie_de(valeur, nom="sid"):
    for morceau in (valeur or "").split(";"):
        cle, _, v = morceau.strip().partition("=")
        if cle == nom:
            return v
    return ""


_RAISONS = {200: "OK", 303: "See Other", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed",
            409: "Conflict"}


async def repondre(w, code, corps, type_="text/html; charset=utf-8", extra=""):
    donnees = corps.encode("utf-8") if isinstance(corps, str) else corps
    entete = ("HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\n"
              "Connection: close\r\nCache-Control: no-store\r\n{}\r\n").format(
        code, _RAISONS.get(code, ""), type_, len(donnees), extra)
    w.write(entete.encode())
    w.write(donnees)
    await w.drain()


async def reponse_json(w, objet):
    await repondre(w, 200, json.dumps(objet), "application/json; charset=utf-8")


async def rediriger(w, ou, extra=""):
    await repondre(w, 303, "", extra="Location: {}\r\n{}".format(ou, extra))


async def exiger_admin(w, cookie):
    """True si l'administrateur est connecté ; sinon renvoie vers la page du code PIN et renvoie False."""
    if admin.verifier(cookie_de(cookie)):
        return True
    await rediriger(w, "/connexion")
    return False
