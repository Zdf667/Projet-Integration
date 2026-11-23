# US6.4 – Statistiques de service : on ne retient QUE le nombre de fois où chaque cocktail a été servi.
#
# Fichier data/historique.json (une seule écriture par cocktail terminé) :
# {"version": 1, "services": 12, "cocktails": {"Madras": 3, "Screwdriver": 9}}
# Les proportions et les quantités de liquide sont recalculées à l'affichage, à partir de ces compteurs et des
# recettes : rien d'autre n'est mémorisé. La Pico n'a pas d'horloge, donc pas de date non plus.
from app import config, storage


def _vide():
    return {"version": 1, "services": 0, "cocktails": {}}


def lire():
    d = storage.lire_json(config.trouver_data(config.FICHIER_HISTORIQUE), None)
    if not isinstance(d, dict) or not isinstance(d.get("cocktails"), dict):
        return _vide()
    # un ancien fichier pouvait contenir « ml » et « derniers » : on ne garde que les compteurs
    cocktails = {nom: n for nom, n in d["cocktails"].items() if isinstance(n, int) and n > 0}
    return {"version": 1, "services": sum(cocktails.values()), "cocktails": cocktails}


def enregistrer(nom):
    """Compte un cocktail terminé."""
    d = lire()
    d["cocktails"][nom] = d["cocktails"].get(nom, 0) + 1
    d["services"] += 1
    storage.ecrire_json(config.chemin_data(config.FICHIER_HISTORIQUE), d)


def reinitialiser():
    storage.ecrire_json(config.chemin_data(config.FICHIER_HISTORIQUE), _vide())


def classement(d):
    """Du cocktail le plus servi au moins servi : [(nom, nombre, pourcentage)].

    Les pourcentages sont arrondis à l'entier ; l'écart éventuel par rapport à 100 est reporté sur la plus
    grande ligne pour que le total fasse exactement 100 %.
    """
    lignes = sorted(d["cocktails"].items(), key=lambda x: (-x[1], x[0]))
    total = sum(n for _, n in lignes)
    if not total:
        return []
    parts = [int(round(100 * n / total)) for _, n in lignes]
    parts[0] += 100 - sum(parts)
    return [(nom, n, parts[i]) for i, (nom, n) in enumerate(lignes)]


def consommation(d, data):
    """Millilitres estimés par ingrédient : nombre de services × quantité de la recette actuelle.

    Un cocktail qui n'est plus dans les recettes est ignoré. Calculé à l'affichage, jamais enregistré.
    """
    ml = {}
    if not data:
        return ml
    par_nom = {r["nom"]: r for r in data["recettes"]}
    for nom, n in d["cocktails"].items():
        r = par_nom.get(nom)
        if r:
            for ligne in r["ingredients"]:
                ml[ligne["ingredient"]] = ml.get(ligne["ingredient"], 0) + n * ligne["ml"]
    return ml
