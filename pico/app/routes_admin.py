# MODE ADMINISTRATEUR protégé par un code PIN – US4.3 (+ choix des ingrédients, US1.1 / US1.2).
#   GET/POST /connexion   saisie du code PIN         GET /deconnexion
#   GET  /admin           choix de l'ingrédient de chaque récipient      POST /ingredients
#   GET/POST /admin/pin   changer le code PIN
# Le nettoyage (/admin/nettoyage) et le Wi-Fi (/admin/wifi) sont dans routes_nettoyage.py et routes_wifi.py.
from app import admin, catalogue, config, ingredients, pages_admin, recettes, sequenceur
from app.http_outils import exiger_admin, parse_form, repondre, rediriger


async def traiter(w, methode, chemin, requete, corps, cookie):
    get = methode == "GET"
    post = methode == "POST"
    data = catalogue.data()
    erreur_recettes = catalogue.erreur()

    if chemin == "/connexion":
        if get:
            await repondre(w, 200, pages_admin.page_connexion())
        elif post:
            try:
                jeton = admin.connecter(parse_form(corps).get("pin", ""))
            except ValueError as e:
                await repondre(w, 400, pages_admin.page_connexion(erreur=str(e)))
            else:
                await rediriger(w, "/admin", "Set-Cookie: sid={}; Path=/; HttpOnly; SameSite=Strict\r\n".format(jeton))
        else:
            await repondre(w, 405, "Méthode non autorisée")
        return True

    if chemin == "/deconnexion":
        admin.deconnecter()
        await rediriger(w, "/", "Set-Cookie: sid=; Path=/; Max-Age=0\r\n")
        return True

    if chemin == "/admin":
        if not await exiger_admin(w, cookie):
            return True
        if not get:
            await repondre(w, 405, "Méthode non autorisée")
            return True
        recipients = ingredients.charger()
        message = None
        if "ok=1" in requete:
            n = len(recettes.realisables(data, recipients)) if data else 0
            message = "Configuration enregistrée : {} cocktail(s) réalisable(s).".format(n)
        await repondre(w, 200, pages_admin.page_admin(recipients, data, erreur_recettes, message=message))
        return True

    if chemin == "/ingredients":
        if not await exiger_admin(w, cookie):
            return True
        if not post:
            await repondre(w, 405, "Méthode non autorisée")
            return True
        champs = parse_form(corps)
        choix = [champs.get("r{}".format(i + 1), "") for i in range(config.NB_RECIPIENTS)]
        if sequenceur.occupe():
            await repondre(w, 409, pages_admin.page_admin(choix, data, erreur_recettes,
                                                          erreur="Une préparation est en cours : attendez la fin."))
            return True
        try:
            ingredients.enregistrer(choix, catalogue.connus())
        except ValueError as e:
            await repondre(w, 400, pages_admin.page_admin(choix, data, erreur_recettes, erreur=str(e)))
        else:
            await rediriger(w, "/admin?ok=1")
        return True

    if chemin == "/admin/pin":
        if not await exiger_admin(w, cookie):
            return True
        if get:
            await repondre(w, 200, pages_admin.page_pin())
        elif post:
            champs = parse_form(corps)
            try:
                admin.definir_pin(champs.get("nouveau", ""), champs.get("confirmation", ""))
            except ValueError as e:
                await repondre(w, 400, pages_admin.page_pin(erreur=str(e)))
            else:
                await repondre(w, 200, pages_admin.page_pin(message="Code PIN enregistré."))
        else:
            await repondre(w, 405, "Méthode non autorisée")
        return True

    return False
