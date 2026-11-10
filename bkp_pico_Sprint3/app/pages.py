# Éléments communs à toutes les pages HTML : échappement, en-tête (logo, onglets, menu admin, messages), pied.
# Chaque mode a ses pages dans son propre fichier : pages_user.py, pages_suivi.py, pages_admin.py,
# pages_nettoyage.py, pages_wifi.py. Le style est dans web/style.css.


LOGO_LARGEUR = 360      # taille du fichier web/logo.png (voir design/preparer_logo.py)


LOGO_HAUTEUR = 358


def e(texte):
    """Protège un texte avant de l'écrire dans une page (MicroPython n'a pas le module html)."""
    return (str(texte).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def haut(mode, message=None, erreur=None, erreur_recettes=None, connecte=False, extra_head=""):
    """En-tête commun : logo, onglets Utilisateur / Administrateur, menu admin si connecté, messages."""
    h = ['<!doctype html><html lang="fr"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>One Cocktail</title>'
         '<link rel="icon" href="/static/favicon.png">'
         '<link rel="stylesheet" href="/static/style.css">' + extra_head + '</head><body><main>'
         '<header class="logo"><img src="/static/logo.png" width="{}" height="{}" '
         'alt="One Cocktail, le trésor ultime de vos soirées"></header>'.format(LOGO_LARGEUR, LOGO_HAUTEUR),
         '<nav aria-label="Choix du mode">']
    h.append('<a href="/"' + (' aria-current="page"' if mode == "user" else "") + '>Mode utilisateur</a>')
    h.append('<a href="/admin"' + (' aria-current="page"' if mode == "admin" else "") + '>Mode administrateur</a>')
    h.append('</nav>')
    if connecte:
        h.append('<nav class="sous" aria-label="Menu administrateur">'
                 '<a href="/admin">Ingrédients</a><a href="/admin/nettoyage">Nettoyage</a>'
                 '<a href="/admin/wifi">Wi-Fi</a><a href="/admin/pin">Code PIN</a>'
                 '<a href="/deconnexion">Déconnexion</a></nav>')
    if message:
        h.append('<p class="msg ok" role="status">' + e(message) + '</p>')
    if erreur:
        h.append('<p class="msg err" role="alert">' + e(erreur) + '</p>')
    if erreur_recettes:
        h.append('<p class="msg err" role="alert">recettes.json inutilisable : ' + e(erreur_recettes) +
                 '. Corrigez data/recettes.json puis redémarrez la machine.</p>')
    return h


def fin(h):
    h.append('</main></body></html>')
    return "".join(h)


def total(recette):
    return sum(ligne["ml"] for ligne in recette["ingredients"])


def detail(recette):
    return ", ".join("{} {} ml".format(x["ingredient"], x["ml"]) for x in recette["ingredients"])


def bandeau_occupe(etat):
    if etat and etat["etat"] == "en_cours":
        return ('<p class="alerte">Une préparation est en cours : <a href="/suivi">voir l\'avancement</a>.</p>')
    return ""
