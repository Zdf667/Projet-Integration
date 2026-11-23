# US4.3 – Pages du MODE ADMINISTRATEUR : saisie du code PIN, choix des ingrédients, sync/import JSON, changement de PIN.
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
    """Choix de l'ingrédient de chaque récipient + sync Cloud + import JSON + toutes les recettes chargées."""
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

        h.append('<section><h2>Mise à jour des recettes</h2>'
                 '<form class="formulaire" method="post" action="/admin/synchroniser" style="margin-bottom:1.2rem;">'
                 '<button type="submit">Synchroniser avec le site OneCocktail</button></form>'
                 '<form id="form-import" class="formulaire" method="post" action="/admin/importer">'
                 '<label class="champ c0"><span>Ou importer un fichier (.json)</span>'
                 '<input type="file" id="fichier-json" accept=".json,application/json" required></label>'
                 '<input type="hidden" name="json_data" id="json-data">'
                 '<button type="submit">Importer le fichier</button></form>'
                 '<script>'
                 'document.getElementById("form-import").addEventListener("submit", function(ev) {'
                 '  var input = document.getElementById("fichier-json");'
                 '  if (!input.files.length) return;'
                 '  ev.preventDefault();'
                 '  var reader = new FileReader();'
                 '  reader.onload = function(e) {'
                 '    document.getElementById("json-data").value = e.target.result;'
                 '    ev.target.submit();'
                 '  };'
                 '  reader.readAsText(input.files[0]);'
                 '});'
                 '</script></section>')

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