# STATISTIQUES (US6.4) et DÉTECTION DU VERRE (US6.2) – mode administrateur.
#   GET  /admin/stats          cocktails servis, ml consommés          POST /admin/stats/reset   remise à zéro
#   GET  /admin/verre          poids mesuré                            POST /admin/verre/tare    la tare
#                                                                      POST /admin/verre/calibrer  poids=...
from app import catalogue, historique, pages_stats, verre
from app.http_outils import exiger_admin, parse_form, repondre, rediriger


async def _page_verre(w, message=None, erreur=None, code=200):
    await repondre(w, code, pages_stats.page_verre(verre.poids_g(), verre.reglages(), verre.present(), message, erreur))


async def traiter(w, methode, chemin, requete, corps, cookie):
    if chemin not in ("/admin/stats", "/admin/stats/reset", "/admin/verre", "/admin/verre/tare", "/admin/verre/calibrer"):
        return False
    if not await exiger_admin(w, cookie):
        return True
    get = methode == "GET"
    post = methode == "POST"

    if chemin == "/admin/stats":
        if not get:
            await repondre(w, 405, "Méthode non autorisée")
        else:
            message = "Statistiques remises à zéro." if "ok=1" in requete else None
            await repondre(w, 200, pages_stats.page_stats(catalogue.data(), message))
    elif chemin == "/admin/stats/reset":
        if not post:
            await repondre(w, 405, "Méthode non autorisée")
        else:
            historique.reinitialiser()
            await rediriger(w, "/admin/stats?ok=1")
    elif chemin == "/admin/verre":
        if not get:
            await repondre(w, 405, "Méthode non autorisée")
        else:
            await _page_verre(w)
    elif not post:
        await repondre(w, 405, "Méthode non autorisée")
    elif chemin == "/admin/verre/tare":
        try:
            verre.tarer()
        except ValueError as e:
            await _page_verre(w, erreur=str(e), code=400)
        else:
            await _page_verre(w, message="Tare enregistrée.")
    else:
        try:
            try:
                poids = float(parse_form(corps).get("poids", "").replace(",", "."))
            except ValueError:
                raise ValueError("Poids de référence invalide : indiquez un nombre de grammes.")
            verre.calibrer(poids)
        except ValueError as e:
            await _page_verre(w, erreur=str(e), code=400)
        else:
            await _page_verre(w, message="Calibration enregistrée.")
    return True
