from app import catalogue, ingredients, pages_user, sequenceur
from app.http_outils import parse_form, repondre, rediriger


async def traiter(w, methode, chemin, requete, corps, cookie):
    """Traite la requête et renvoie True si elle concernait ce module."""
    data = catalogue.data()

    if chemin == "/":
        if methode != "GET":
            await repondre(w, 405, "Méthode non autorisée")
        else:
            await repondre(w, 200, pages_user.page_utilisateur(
                ingredients.charger(), data, catalogue.erreur(), etat=sequenceur.etat()))
        return True

    if chemin == "/cocktail":
        if methode != "GET":
            await repondre(w, 405, "Méthode non autorisée")
            return True
        try:
            numero = int(parse_form(requete).get("id", "-1"))
        except ValueError:
            numero = -1
        await repondre(w, 200, pages_user.page_cocktail(ingredients.charger(), data, numero, sequenceur.etat()))
        return True

    if chemin == "/servir":
        if methode != "POST":
            await repondre(w, 405, "Méthode non autorisée")
            return True
        try:
            numero = int(parse_form(corps).get("id", "-1"))
        except ValueError:
            numero = -1
        recette = data["recettes"][numero] if data and 0 <= numero < len(data["recettes"]) else None
        if recette is None:
            await repondre(w, 404, pages_user.page_cocktail(ingredients.charger(), data, -1))
            return True
        recipients = ingredients.charger()
        try:
            sequenceur.servir(recette, recipients)
        except sequenceur.Occupe as e:
            await repondre(w, 409, pages_user.page_cocktail(recipients, data, numero, sequenceur.etat(), erreur=str(e)))
        except ValueError as e:
            await repondre(w, 400, pages_user.page_cocktail(recipients, data, numero, sequenceur.etat(), erreur=str(e)))
        else:
            await rediriger(w, "/suivi")
        return True

    return False
