
from app import conseil, recettes
from app.pages import bandeau_occupe, detail, e, fin, haut, total

def page_utilisateur(recipients, data, erreur_recettes=None, etat=None, message=None):
    """Contenu des 4 récipients + cocktails réalisables (chaque carte mène au détail et au lancement)."""
    h = haut("user", message=message, erreur_recettes=erreur_recettes)
    h.append(bandeau_occupe(etat))

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
            numero = data["recettes"].index(r)
            h.append('<article class="carte"><header><h3>' + e(r["nom"]) + '</h3><span class="total">' +
                     str(total(r)) + ' ml</span></header><ul class="doses">')
            for ligne in r["ingredients"]:
                h.append('<li class="dose c{}"><span>{}</span><b>{} ml</b></li>'.format(
                    recipients.index(ligne["ingredient"]), e(ligne["ingredient"]), ligne["ml"]))
            h.append('</ul>' + conseil.html_recette(r) + '<a class="bouton" href="/cocktail?id={}">Choisir</a></article>'.format(numero))
        h.append('</section>')
    return fin(h)


def page_cocktail(recipients, data, numero, etat=None, erreur=None):
    """US2.3 / US4.1 – Composition d'un cocktail avant de le lancer, puis bouton de lancement."""
    h = haut("user", erreur=erreur)
    if not data or not 0 <= numero < len(data["recettes"]):
        h.append('<p class="msg err">Cocktail introuvable.</p><p><a class="bouton" href="/">Retour</a></p>')
        return fin(h)
    r = data["recettes"][numero]
    manquants = [x["ingredient"] for x in r["ingredients"] if x["ingredient"] not in recipients]
    h.append('<section><h2>' + e(r["nom"]) + '</h2>')
    h.append(bandeau_occupe(etat))
    h.append('<article class="carte"><header><h3>Composition</h3><span class="total">' + str(total(r)) +
             ' ml</span></header><ul class="doses">')
    for ligne in r["ingredients"]:
        if ligne["ingredient"] in recipients:
            h.append('<li class="dose c{}"><span>{} (récipient {})</span><b>{} ml</b></li>'.format(
                recipients.index(ligne["ingredient"]), e(ligne["ingredient"]),
                recipients.index(ligne["ingredient"]) + 1, ligne["ml"]))
        else:
            h.append('<li class="dose">{} : absent ({} ml)</li>'.format(e(ligne["ingredient"]), ligne["ml"]))
    h.append('</ul>' + conseil.html_recette(r) + '</article>')
    if manquants:
        h.append('<p class="msg err">Il manque : ' + e(", ".join(manquants)) + '.</p>')
    elif etat and etat["etat"] == "en_cours":
        h.append('<p class="indice">Attendez la fin de la préparation en cours.</p>')
    else:
        h.append('<p class="indice">Placez un verre sous le bec, puis lancez.</p>'
                 '<form method="post" action="/servir"><input type="hidden" name="id" value="{}">'
                 '<button type="submit">Lancer la préparation</button></form>'.format(numero))
    h.append('<p><a class="bouton clair" href="/">Retour aux cocktails</a></p></section>')
    return fin(h)
