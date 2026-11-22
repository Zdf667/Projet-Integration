# US6.4 / US6.2 – Pages du mode administrateur : statistiques de service et réglage de la détection du verre.
from app import config, historique
from app.pages import e, fin, haut


def page_stats(data=None, message=None):
    """US6.4 – Cocktails servis (le plus apprécié en tête) et quantités estimées par ingrédient."""
    d = historique.lire()
    h = haut("admin", message, connecte=True)
    h.append('<section><h2>Statistiques de service</h2>')
    if not d["services"]:
        h.append('<p class="indice">Aucun cocktail servi depuis la dernière remise à zéro.</p>')
    else:
        h.append('<p class="msg ok">{} cocktail(s) servi(s).</p>'.format(d["services"]))
        h.append('<article class="carte"><header><h3>Cocktails préférés</h3></header><ul class="doses">')
        for nom, n, pct in historique.classement(d):
            h.append('<li class="dose"><span>{}</span><b>{} ({} %)</b></li>'.format(e(nom), n, pct))
        h.append('</ul></article>')
        ml = historique.consommation(d, data)
        if ml:
            h.append('<article class="carte"><header><h3>Ingrédients consommés (estimation)</h3></header><ul class="doses">')
            for nom, v in sorted(ml.items(), key=lambda x: (-x[1], x[0])):
                h.append('<li class="dose"><span>{}</span><b>{} ml</b></li>'.format(e(nom), v))
            h.append('</ul></article>')
    h.append('<p class="indice">Seul le nombre de fois où chaque cocktail a été servi est enregistré. Les quantités sont '
             'recalculées d\'après les recettes actuelles ; une préparation arrêtée ou en erreur n\'est pas comptée.</p>')
    h.append('<form method="post" action="/admin/stats/reset"><button type="submit" class="danger">Remettre à zéro</button></form>')
    h.append('</section>')
    return fin(h)


def page_verre(poids, reglages, present, message=None, erreur=None):
    """US6.2 – Poids mesuré, tare et calibration de la cellule de charge."""
    h = haut("admin", message, erreur, connecte=True)
    h.append('<section><h2>Détection du verre</h2>')
    if not config.VERRE_ACTIF:
        h.append('<p class="alerte">Détection désactivée (VERRE_ACTIF = False dans config.py) : la machine verse même sans '
                 'verre. Activez-la une fois la cellule de charge branchée et calibrée.</p>')
    if poids is None:
        h.append('<p class="msg err">Aucune mesure : le capteur ne répond pas.</p>')
    else:
        h.append('<p class="msg ok">Poids mesuré : {:.0f} g. {}</p>'.format(
            poids, "Verre détecté." if present else "Aucun verre détecté."))
    h.append('<p class="indice">Seuil de présence : {} g. Tare : {}. Facteur : {:.2f}.</p>'.format(
        config.VERRE_SEUIL_G, int(reglages["tare"]), reglages["facteur"]))
    h.append('<form method="post" action="/admin/verre/tare"><p class="indice">1. Plateau vide, puis :</p>'
             '<button type="submit">Faire la tare</button></form>')
    h.append('<form class="formulaire" method="post" action="/admin/verre/calibrer"><p class="indice">'
             '2. Posez un objet de poids connu, puis indiquez son poids :</p>'
             '<label class="champ c0"><span>Poids de référence (g)</span>'
             '<input type="number" name="poids" min="1" step="any" inputmode="decimal" required></label>'
             '<button type="submit">Calibrer</button></form>')
    h.append('</section>')
    return fin(h)
