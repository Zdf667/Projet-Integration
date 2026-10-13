# Pages HTML : mode utilisateur et mode administrateur. Le style est dans web/style.css.
#
# Chaque récipient a une couleur (classes c0 à c3, définies dans style.css). Dans la liste des cocktails,
# chaque ingrédient reprend la couleur du récipient où il se trouve : on voit d'un coup d'œil d'où il vient.
from app import recettes

LOGO_LARGEUR = 360      # taille du fichier web/logo.png (voir design/preparer_logo.py)
LOGO_HAUTEUR = 358


def e(texte):
    """Protège un texte avant de l'écrire dans une page (MicroPython n'a pas le module html)."""
    return (str(texte).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _haut(mode, message=None, erreur=None, erreur_recettes=None):
    """En-tête commun : logo, onglets Utilisateur / Administrateur, messages."""
    h = ['<!doctype html><html lang="fr"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>One Cocktail</title>'
         '<link rel="icon" href="/static/favicon.png">'
         '<link rel="stylesheet" href="/static/style.css"></head><body><main>'
         '<header class="logo"><img src="/static/logo.png" width="{}" height="{}" '
         'alt="One Cocktail, le trésor ultime de vos soirées"></header>'.format(LOGO_LARGEUR, LOGO_HAUTEUR),
         '<nav aria-label="Choix du mode">']
    h.append('<a href="/"' + (' aria-current="page"' if mode == "user" else "") + '>Mode utilisateur</a>')
    h.append('<a href="/admin"' + (' aria-current="page"' if mode == "admin" else "") + '>Mode administrateur</a>')
    h.append('</nav>')
    if message:
        h.append('<p class="msg ok" role="status">' + e(message) + '</p>')
    if erreur:
        h.append('<p class="msg err" role="alert">' + e(erreur) + '</p>')
    if erreur_recettes:
        h.append('<p class="msg err" role="alert">recettes.json inutilisable : ' + e(erreur_recettes) +
                 '. Corrigez data/recettes.json puis redémarrez la machine.</p>')
    return h


def _total(recette):
    return sum(ligne["ml"] for ligne in recette["ingredients"])


def _detail(recette):
    return ", ".join("{} {} ml".format(x["ingredient"], x["ml"]) for x in recette["ingredients"])


def _garniture(recette):
    if recette.get("conseil"):
        return '<p class="garniture">À ajouter : ' + e(", ".join(recette["conseil"])) + '</p>'
    return ""


def page_utilisateur(recipients, data, erreur_recettes=None):
    """Contenu des 4 récipients + cocktails réalisables (lecture seule)."""
    h = _haut("user", erreur_recettes=erreur_recettes)

    h.append('<section><h2>Dans la machine</h2><ul class="cuves">')
    for i, nom in enumerate(recipients):
        if nom:
            h.append('<li class="cuve c{}"><span class="num">Récipient {}</span><b>{}</b></li>'.format(i, i + 1, e(nom)))
        else:
            h.append('<li class="cuve vide"><span class="num">Récipient {}</span><span>vide</span></li>'.format(i + 1))
    h.append('</ul></section>')

    if data:
        possibles = recettes.realisables(data, recipients)
        h.append('<section><h2>Cocktails réalisables ({})</h2>'.format(len(possibles)))
        if not any(recipients):
            h.append('<p class="indice">Aucun ingrédient chargé. Passez en <a href="/admin">mode administrateur</a> '
                     'pour remplir les récipients.</p>')
        elif not possibles:
            h.append('<p class="indice">Aucun cocktail réalisable avec ces ingrédients. Changez un récipient en '
                     '<a href="/admin">mode administrateur</a>.</p>')
        for r in possibles:
            h.append('<article class="carte"><header><h3>' + e(r["nom"]) + '</h3><span class="total">' +
                     str(_total(r)) + ' ml</span></header><ul class="doses">')
            for ligne in r["ingredients"]:
                h.append('<li class="dose c{}"><span>{}</span><b>{} ml</b></li>'.format(
                    recipients.index(ligne["ingredient"]), e(ligne["ingredient"]), ligne["ml"]))
            h.append('</ul>' + _garniture(r) + '</article>')
        h.append('</section>')
    h.append('</main></body></html>')
    return "".join(h)


def page_admin(selection, data, erreur_recettes=None, erreur=None, message=None):
    """Choix de l'ingrédient de chaque récipient + toutes les recettes chargées."""
    h = _haut("admin", message, erreur, erreur_recettes)
    h.append('<p class="alerte">Accès libre pour l\'instant : le code PIN viendra plus tard.</p>')

    if data:
        h.append('<section><h2>Ingrédients des récipients</h2>'
                 '<form class="formulaire" method="post" action="/ingredients">')
        for i in range(len(selection)):
            actuel = selection[i]
            h.append('<label class="champ c{0}"><span>Récipient {1}</span><select name="r{1}">'
                     '<option value="">— vide —</option>'.format(i, i + 1))
            for nom in data["ingredients"]:
                coche = " selected" if nom == actuel else ""
                h.append('<option value="' + e(nom) + '"' + coche + '>' + e(nom) + '</option>')
            h.append('</select></label>')
        h.append('<button type="submit">Enregistrer</button></form></section>')

        h.append('<section><h2>Recettes chargées ({})</h2>'.format(len(data["recettes"])))
        for r in data["recettes"]:
            h.append('<details class="recette"><summary><b>' + e(r["nom"]) + '</b><span class="total">' +
                     str(_total(r)) + ' ml</span></summary><p>' + e(_detail(r)) + '</p>' + _garniture(r) +
                     '</details>')
        h.append('</section>')
    h.append('</main></body></html>')
    return "".join(h)
