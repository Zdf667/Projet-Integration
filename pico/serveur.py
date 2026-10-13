# Serveur web minimal (asyncio) avec deux modes visibles sur la page.
#
#   GET  /                 MODE UTILISATEUR : contenu des 4 récipients + cocktails réalisables
#   GET  /admin            MODE ADMINISTRATEUR : choix de l'ingrédient de chaque récipient + recettes chargées
#   POST /ingredients      enregistre les 4 récipients (refuse un doublon ou un ingrédient inconnu)
#   GET  /api/ingredients  {"recipients": [...], "connus": [...]}
#   GET  /api/recettes     contenu de recettes.json
#
# Le mode administrateur n'est PAS protégé par un PIN (US4.3 est remplacée par US1.2 pour l'instant) :
# n'importe qui sur le réseau de la machine peut ouvrir /admin.
import asyncio
import json

import config
import ingredients
import recettes

_etat = {"data": None, "erreur": None}   # contenu validé de recettes.json, ou message d'erreur


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


# --- petits outils (MicroPython n'a ni html ni urllib.parse) ---------------------------------
def _e(texte):
    return (str(texte).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


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


# --- pages HTML ------------------------------------------------------------------------------
_STYLE = ("body{font-family:sans-serif;max-width:34rem;margin:1rem auto;padding:0 1rem}"
          "nav{display:flex;gap:.5rem;margin:1rem 0}"
          "nav a{flex:1;text-align:center;padding:.6rem;border:2px solid #36c;border-radius:.4rem;"
          "text-decoration:none;color:#36c;font-weight:bold}"
          "nav a.actif{background:#36c;color:#fff}"
          "label{display:block;margin-top:.8rem}select,button{font-size:1rem;padding:.4rem;width:100%}"
          ".ok{background:#d9f2d9;padding:.5rem}.err{background:#f7d4d4;padding:.5rem}"
          ".vide{color:#777}ul{padding-left:1.2rem}li{margin:.4rem 0}small{color:#555}")


def _haut(mode, message=None, erreur=None):
    """En-tête commun : titre, onglets Utilisateur / Administrateur, messages."""
    h = ["<!doctype html><html lang=\"fr\"><head><meta charset=\"utf-8\">"
         "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
         "<title>Machine à cocktail</title><style>", _STYLE, "</style></head><body>",
         "<h1>Machine à cocktail</h1><nav>"
         "<a href=\"/\"", " class=\"actif\"" if mode == "user" else "", ">Mode utilisateur</a>"
         "<a href=\"/admin\"", " class=\"actif\"" if mode == "admin" else "", ">Mode administrateur</a></nav>"]
    if message:
        h.append("<p class=\"ok\">" + _e(message) + "</p>")
    if erreur:
        h.append("<p class=\"err\">" + _e(erreur) + "</p>")
    if _etat["erreur"]:
        h.append("<p class=\"err\">recettes.json inutilisable : " + _e(_etat["erreur"]) + "</p>")
    return h


def _detail(recette):
    return ", ".join("{} {} ml".format(x["ingredient"], x["ml"]) for x in recette["ingredients"])


def _page_utilisateur():
    recipients = ingredients.charger()
    h = _haut("user")

    h.append("<h2>Contenu des récipients</h2><ul>")
    for i, nom in enumerate(recipients):
        contenu = "<b>" + _e(nom) + "</b>" if nom else "<span class=\"vide\">vide</span>"
        h.append("<li>Récipient {} : {}</li>".format(i + 1, contenu))
    h.append("</ul>")

    if _etat["data"]:
        possibles = recettes.realisables(_etat["data"], recipients)
        h.append("<h2>Cocktails réalisables ({})</h2>".format(len(possibles)))
        if not any(recipients):
            h.append("<p class=\"vide\">Aucun ingrédient chargé. Passez en mode administrateur pour remplir les récipients.</p>")
        elif not possibles:
            h.append("<p class=\"vide\">Aucun cocktail réalisable avec ces ingrédients.</p>")
        else:
            h.append("<ul>")
            for r in possibles:
                ligne = "<li><b>" + _e(r["nom"]) + "</b><br>" + _e(_detail(r))
                if r.get("conseil"):
                    ligne += "<br><small>À ajouter : " + _e(", ".join(r["conseil"])) + "</small>"
                h.append(ligne + "</li>")
            h.append("</ul>")
    h.append("</body></html>")
    return "".join(h)


def _page_admin(selection, erreur=None, message=None):
    h = _haut("admin", message, erreur)
    h.append("<h2>Ingrédients des récipients</h2>")
    if _etat["data"]:
        h.append("<form method=\"post\" action=\"/ingredients\">")
        for i in range(config.NB_RECIPIENTS):
            actuel = selection[i] if i < len(selection) else None
            h.append("<label>Récipient {0}<select name=\"r{0}\"><option value=\"\">— vide —</option>".format(i + 1))
            for nom in _connus():
                coche = " selected" if nom == actuel else ""
                h.append("<option value=\"" + _e(nom) + "\"" + coche + ">" + _e(nom) + "</option>")
            h.append("</select></label>")
        h.append("<button style=\"margin-top:1rem\">Enregistrer</button></form>")

        h.append("<h2>Recettes chargées ({})</h2><ul>".format(len(_etat["data"]["recettes"])))
        for r in _etat["data"]["recettes"]:
            ligne = "<li><b>" + _e(r["nom"]) + "</b> : " + _e(_detail(r))
            if r.get("conseil"):
                ligne += "<br><small>À ajouter : " + _e(", ".join(r["conseil"])) + "</small>"
            h.append(ligne + "</li>")
        h.append("</ul>")
    h.append("</body></html>")
    return "".join(h)


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
        return await _repondre(w, 200, _page_utilisateur())

    if chemin == "/admin":
        if methode != "GET":
            return await _repondre(w, 405, "Méthode non autorisée")
        recipients = ingredients.charger()
        message = None
        if "ok=1" in requete:
            n = len(recettes.realisables(_etat["data"], recipients)) if _etat["data"] else 0
            message = "Configuration enregistrée : {} cocktail(s) réalisable(s).".format(n)
        return await _repondre(w, 200, _page_admin(recipients, message=message))

    if chemin == "/ingredients":
        if methode != "POST":
            return await _repondre(w, 405, "Méthode non autorisée")
        champs = _parse_form(corps)
        choix = [champs.get("r{}".format(i + 1), "") for i in range(config.NB_RECIPIENTS)]
        try:
            ingredients.enregistrer(choix, _connus())
        except ValueError as e:
            return await _repondre(w, 400, _page_admin(choix, erreur=str(e)))
        return await _repondre(w, 303, "", extra="Location: /admin?ok=1\r\n")

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
