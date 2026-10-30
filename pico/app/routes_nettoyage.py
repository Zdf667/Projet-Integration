# NETTOYAGE GUIDÉ (mode administrateur, code PIN) – US5.1.
#   GET  /admin/nettoyage?etape=N   assistant pas à pas
#   POST /admin/nettoyage           action=lancer (rinçage des 4 lignes) ou action=suite (étape suivante)
from app import nettoyage, pages_nettoyage, sequenceur
from app.http_outils import exiger_admin, parse_form, repondre, rediriger


def _etape(texte):
    try:
        return int(texte)
    except ValueError:
        return 1


async def traiter(w, methode, chemin, requete, corps, cookie):
    if chemin != "/admin/nettoyage":
        return False
    if not await exiger_admin(w, cookie):
        return True
    if methode == "GET":
        etape = _etape(parse_form(requete).get("etape", "1"))
        await repondre(w, 200, pages_nettoyage.page_nettoyage(etape, sequenceur.etat()))
    elif methode == "POST":
        champs = parse_form(corps)
        etape = _etape(champs.get("etape", "1"))
        if champs.get("action") == "suite":
            sequenceur.acquitter()
            await rediriger(w, "/admin/nettoyage?etape={}".format(etape + 1))
        else:
            try:
                nettoyage.nettoyer()
            except sequenceur.Occupe as e:
                await repondre(w, 409, pages_nettoyage.page_nettoyage(etape, sequenceur.etat(), erreur=str(e)))
            else:
                await rediriger(w, "/admin/nettoyage?etape={}".format(etape))
    else:
        await repondre(w, 405, "Méthode non autorisée")
    return True
