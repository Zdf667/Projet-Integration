# US2.1 – Recettes préenregistrées : lecture et contrôle de recettes.json.
#
# Format du fichier (c'est aussi le futur « contrat » avec le serveur pour le bonus US6.3) :
# {
#   "version": 1,
#   "ingredients": ["Vodka", "Jus d'orange", ...],          <- liste des ingrédients connus
#   "recettes": [
#     {"nom": "Screwdriver",
#      "ingredients": [{"ingredient": "Vodka", "ml": 50}, {"ingredient": "Jus d'orange", "ml": 150}],
#      "conseil": ["Glaçons", "Tranche d'orange"]}          <- ingrédients NON liquides (pas de pompe)
#   ]
# }
import config
import storage

ML_MAX = 500          # garde-fou : une recette ne verse pas plus de 500 ml d'un seul ingrédient
MAX_PAR_RECETTE = config.NB_RECIPIENTS   # 4 pompes = 4 ingrédients au maximum par recette


def valider(donnees):
    """Contrôle tout le fichier. Lève ValueError avec un message précis au premier problème."""
    if not isinstance(donnees, dict):
        raise ValueError("fichier de recettes invalide")
    version = donnees.get("version")
    if not isinstance(version, int) or version < 1:
        raise ValueError("« version » doit être un entier >= 1")

    connus = donnees.get("ingredients")
    if not isinstance(connus, list) or not connus:
        raise ValueError("« ingredients » doit être une liste non vide")
    vus = set()
    for nom in connus:
        if not isinstance(nom, str) or not nom.strip():
            raise ValueError("ingrédient connu invalide : {}".format(nom))
        if nom in vus:
            raise ValueError("ingrédient connu en double : {}".format(nom))
        vus.add(nom)

    recettes = donnees.get("recettes")
    if not isinstance(recettes, list) or not recettes:
        raise ValueError("« recettes » doit être une liste non vide")

    noms = set()
    for numero, r in enumerate(recettes, 1):
        if not isinstance(r, dict):
            raise ValueError("recette {} : objet attendu".format(numero))
        nom = r.get("nom")
        if not isinstance(nom, str) or not nom.strip():
            raise ValueError("recette {} : « nom » manquant".format(numero))
        if nom in noms:
            raise ValueError("recette en double : {}".format(nom))
        noms.add(nom)

        lignes = r.get("ingredients")
        if not isinstance(lignes, list) or not lignes:
            raise ValueError("recette « {} » : aucun ingrédient".format(nom))
        if len(lignes) > MAX_PAR_RECETTE:
            raise ValueError("recette « {} » : plus de {} ingrédients".format(nom, MAX_PAR_RECETTE))
        dans_la_recette = set()
        for ligne in lignes:
            if not isinstance(ligne, dict):
                raise ValueError("recette « {} » : ligne d'ingrédient invalide".format(nom))
            ing = ligne.get("ingredient")
            ml = ligne.get("ml")
            if ing not in vus:
                raise ValueError("recette « {} » : ingrédient inconnu « {} »".format(nom, ing))
            if ing in dans_la_recette:
                raise ValueError("recette « {} » : « {} » apparaît deux fois".format(nom, ing))
            dans_la_recette.add(ing)
            if not isinstance(ml, int) or isinstance(ml, bool) or ml < 1 or ml > ML_MAX:
                raise ValueError("recette « {} » : « ml » doit être un entier de 1 à {}".format(nom, ML_MAX))

        # « conseil de service » = liste d'ingrédients NON liquides (glaçons, garniture, menthe...)
        conseil = r.get("conseil", [])
        if not isinstance(conseil, list):
            raise ValueError("recette « {} » : « conseil » doit être une liste d'ingrédients non liquides".format(nom))
        dans_le_conseil = set()
        for element in conseil:
            if not isinstance(element, str) or not element.strip() or len(element) > 40:
                raise ValueError("recette « {} » : élément de « conseil » invalide".format(nom))
            if element in vus:
                raise ValueError("recette « {} » : « {} » est un liquide, il va dans « ingredients »".format(nom, element))
            if element in dans_le_conseil:
                raise ValueError("recette « {} » : « {} » apparaît deux fois dans « conseil »".format(nom, element))
            dans_le_conseil.add(element)
    return donnees


def realisables(donnees, recipients):
    """Recettes réalisables avec le contenu actuel des récipients.

    `donnees` = résultat de charger() ; `recipients` = liste de 4 éléments (ingrédient ou None).
    Une recette est réalisable si TOUS ses ingrédients liquides sont dans un récipient.
    Recalculée à chaque appel : après un changement d'ingrédient, la liste est aussitôt à jour (US1.2).
    """
    charges = set(x for x in recipients if x)
    resultat = []
    for r in donnees["recettes"]:
        if all(ligne["ingredient"] in charges for ligne in r["ingredients"]):
            resultat.append(r)
    return resultat


def charger():
    """Charge et valide recettes.json. Lève ValueError / OSError si le fichier est absent ou faux."""
    donnees = storage.lire_json(config.chemin(config.FICHIER_RECETTES), None)
    if donnees is None:
        raise ValueError("recettes.json absent ou illisible")
    return valider(donnees)
