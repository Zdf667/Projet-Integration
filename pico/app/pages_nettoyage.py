# US5.1 – Page de l'assistant de NETTOYAGE guidé (mode administrateur).
from app.pages import e, fin, haut
from app.pages_suivi import _bloc_progression, _script_suivi


ETAPES_NETTOYAGE = (
    ("Préparer", "Videz le verre. Placez un grand récipient vide sous le bec de la machine.", False),
    ("Eau chaude", "Sortez les 4 tuyaux de leurs récipients et plongez-les dans un bol d'eau chaude "
                   "(pas bouillante) avec une goutte de produit vaisselle.", True),
    ("Eau claire", "Plongez les 4 tuyaux dans un bol d'eau claire pour rincer le produit.", True),
    ("Terminé", "Videz le grand récipient et remettez chaque tuyau dans son récipient d'ingrédient.", False),
)


def page_nettoyage(etape, etat, erreur=None):
    """US5.1 – Assistant de nettoyage pas à pas (étapes 1 à 4)."""
    etape = min(max(etape, 1), len(ETAPES_NETTOYAGE))
    titre, texte, lance = ETAPES_NETTOYAGE[etape - 1]
    rincage = etat["mode"] == "nettoyage"
    refresh = '<noscript><meta http-equiv="refresh" content="2"></noscript>' if (rincage and etat["etat"] == "en_cours") else ""
    h = haut("admin", erreur=erreur, connecte=True, extra_head=refresh)
    h.append('<section><h2>Nettoyage : étape {} sur {}</h2><article class="carte"><header><h3>{}</h3></header><p>{}</p></article>'
             .format(etape, len(ETAPES_NETTOYAGE), e(titre), e(texte)))
    if lance and rincage and etat["etat"] == "en_cours":
        h.append(_bloc_progression(etat))
        h.append('<form method="post" action="/arreter"><button type="submit" class="danger">Arrêter</button></form>')
        h.append(_script_suivi(etat))
    elif lance and rincage and etat["etat"] == "termine":
        h.append('<p class="msg ok" role="status">Rinçage terminé.</p>'
                 '<form method="post" action="/admin/nettoyage"><input type="hidden" name="action" value="suite">'
                 '<input type="hidden" name="etape" value="{}"><button type="submit">Étape suivante</button></form>'.format(etape))
    elif lance:
        h.append('<form method="post" action="/admin/nettoyage"><input type="hidden" name="action" value="lancer">'
                 '<input type="hidden" name="etape" value="{}"><button type="submit">Lancer le rinçage</button></form>'.format(etape))
    elif etape < len(ETAPES_NETTOYAGE):
        h.append('<a class="bouton" href="/admin/nettoyage?etape={}">Étape suivante</a>'.format(etape + 1))
    else:
        h.append('<a class="bouton" href="/admin">Terminer</a>')
    h.append('</section>')
    return fin(h)
