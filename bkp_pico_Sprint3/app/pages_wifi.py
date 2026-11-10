from app import config
from app.pages import e, fin, haut


def page_wifi(info, enregistres, reseaux=None, erreur=None, message=None, ssid_saisi=""):
    """US4.6 – Mode réseau actuel, réseaux enregistrés, ajout d'un réseau (scan + mot de passe)."""
    h = haut("admin", message, erreur, connecte=True)
    if info["mode"] == "client":
        etat = 'Connectée au Wi-Fi « {} », adresse {}'.format(e(info["ssid"]), e(info["ip"]))
    else:
        etat = 'Point d\'accès « {} » (mot de passe {}), adresse {}'.format(e(info["ssid"]), e(config.AP_MOT_DE_PASSE), e(info["ip"]))
        if info.get("raison"):
            etat += '. Raison : ' + e(info["raison"])
    h.append('<section><h2>Réseau</h2><p class="indice">' + etat + '</p></section>')

    h.append('<section><h2>Réseaux enregistrés ({})</h2>'.format(len(enregistres)))
    if not enregistres:
        h.append('<p class="indice">Aucun. La machine crée son propre réseau au démarrage.</p>')
    for r in enregistres:
        h.append('<form class="reseau" method="post" action="/admin/wifi/oublier"><span>{}</span>'
                 '<input type="hidden" name="ssid" value="{}"><button type="submit" class="danger">Oublier</button></form>'
                 .format(e(r["ssid"]), e(r["ssid"])))
    h.append('</section>')

    h.append('<section><h2>Ajouter un réseau</h2><p><a class="bouton clair" href="/admin/wifi?scan=1">Rechercher les réseaux</a></p>'
             '<form class="formulaire" method="post" action="/admin/wifi">')
    if reseaux is not None:
        if reseaux:
            h.append('<label class="champ c1"><span>Réseaux trouvés</span><select name="ssid_liste">'
                     '<option value="">— choisir —</option>')
            for nom in reseaux:
                h.append('<option value="' + e(nom) + '">' + e(nom) + '</option>')
            h.append('</select></label>')
        else:
            h.append('<p class="indice">Aucun réseau trouvé. Rapprochez la machine de la box ou saisissez le nom à la main.</p>')
    h.append('<label class="champ c1"><span>Ou saisir le nom du réseau (SSID)</span>'
             '<input type="text" name="ssid" maxlength="32" value="{}" autocapitalize="none" autocorrect="off"></label>'
             '<label class="champ c2"><span>Mot de passe</span><input type="password" name="mdp" maxlength="63"></label>'
             '<button type="submit">Enregistrer et redémarrer</button></form>'.format(e(ssid_saisi or "")))
    h.append('<form method="post" action="/admin/wifi/oublier"><input type="hidden" name="ssid" value="">'
             '<button type="submit" class="danger">Tout oublier (redémarre en point d\'accès)</button></form></section>')
    return fin(h)


def page_redemarrage(texte):
    h = haut("admin", extra_head='<meta http-equiv="refresh" content="25;url=/">')
    h.append('<section><h2>Redémarrage</h2><p class="msg ok" role="status">' + e(texte) +
             '</p><p class="indice">Cette page se rechargera toute seule. Si le Wi-Fi a changé, reconnectez votre téléphone '
             'au bon réseau puis ouvrez l\'adresse affichée par la machine.</p></section>')
    return fin(h)
