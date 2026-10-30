# SUIVI DE LA PRÉPARATION (libre) – US4.2.
#   GET  /status    état de la machine en JSON (la page l'interroge chaque seconde)
#   GET  /suivi     avancement, verre prêt, conseil de service
#   POST /arreter   arrêt immédiat des pompes
#   POST /acquitter retour à « machine prête » après un verre prêt ou une erreur
from app import pages_suivi, sequenceur
from app.http_outils import repondre, rediriger, reponse_json


async def traiter(w, methode, chemin, requete, corps, cookie):
    if chemin == "/status" and methode == "GET":
        await reponse_json(w, sequenceur.etat())
        return True

    if chemin == "/suivi":
        if methode != "GET":
            await repondre(w, 405, "Méthode non autorisée")
        else:
            await repondre(w, 200, pages_suivi.page_suivi(sequenceur.etat()))
        return True

    if chemin == "/arreter":
        if methode != "POST":
            await repondre(w, 405, "Méthode non autorisée")
        else:
            sequenceur.arreter()
            await rediriger(w, "/suivi")
        return True

    if chemin == "/acquitter":
        if methode != "POST":
            await repondre(w, 405, "Méthode non autorisée")
        else:
            sequenceur.acquitter()
            await rediriger(w, "/")
        return True

    return False
