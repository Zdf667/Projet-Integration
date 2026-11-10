# US2.4 – Conseil de service : éléments NON liquides à ajouter après la préparation (glaçons, garniture...).
# Ils viennent du champ « conseil » de chaque recette dans recettes.json. Le conseil s'affiche sur la fiche
# du cocktail et, une fois le verre prêt, sur la page de suivi.
from app.pages import e


def texte(conseil):
    """['Glaçons', 'Menthe'] -> 'Glaçons, Menthe' ; chaîne vide s'il n'y a pas de conseil."""
    return ", ".join(conseil) if conseil else ""


def html(conseil):
    """Encadré « À ajouter : ... » (chaîne vide s'il n'y a pas de conseil)."""
    if not conseil:
        return ""
    return '<p class="garniture">À ajouter : ' + e(texte(conseil)) + '</p>'


def html_recette(recette):
    return html(recette.get("conseil"))
