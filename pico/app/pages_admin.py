# US4.3 – Pages du MODE ADMINISTRATEUR : saisie du code PIN, choix des ingrédients, changement de PIN.
from app import conseil
from app.pages import detail, e, fin, haut, total


# --- mode administrateur ---------------------------------------------------------------------
def page_connexion(erreur=None, bloque=0):
    h = haut("admin", erreur=erreur)
    h.append('<section><h2>Mode administrateur</h2>'
             '<form class="formulaire" method="post" action="/connexion">'
             '<label class="champ c0"><span>Code PIN</span>'
             '<input type="password" name="pin" inputmode="numeric" autocomplete="off" required></label>'
             '<button type="submit">Entrer</button></form></section>')
    return fin(h)


def page_admin(selection, data, erreur_recettes=None, erreur=None, message=None):
    """Choix de l'ingrédient de chaque récipient + toutes les recettes chargées."""
    h = haut("admin", message, erreur, erreur_recettes, connecte=True)

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
                     str(total(r)) + ' ml</span></summary><p>' + e(detail(r)) + '</p>' + conseil.html_recette(r) +
                     '</details>')
        h.append('</section>')
    return fin(h)


def page_pin(erreur=None, message=None):
    h = haut("admin", message, erreur, connecte=True)
    h.append('<section><h2>Changer le code PIN</h2><form class="formulaire" method="post" action="/admin/pin">'
             '<label class="champ c0"><span>Nouveau code (4 à 8 chiffres)</span>'
             '<input type="password" name="nouveau" inputmode="numeric" autocomplete="off" required></label>'
             '<label class="champ c0"><span>Confirmer</span>'
             '<input type="password" name="confirmation" inputmode="numeric" autocomplete="off" required></label>'
             '<button type="submit">Enregistrer</button></form></section>')
    return fin(h)
