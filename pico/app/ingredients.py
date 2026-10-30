# US1.1 – Enregistrer les ingrédients : un ingrédient par récipient (1 à 4).
#
# Règles :
#  - un récipient peut rester vide (None) ;
#  - un ingrédient doit appartenir à la liste des ingrédients connus (pas de saisie libre) ;
#  - impossible d'enregistrer 2 fois le même ingrédient ;
#  - la configuration est sauvegardée dans config.json et survit à un redémarrage.
#
# Le récipient n est branché sur la pompe n : récipient 1 = index 0 = pompe 1.
from app import config, storage

VERSION = 1


def _nettoyer(valeur):
    if valeur is None:
        return None
    texte = str(valeur).strip()
    return texte if texte else None


def valider(recipients, connus):
    """Lève ValueError (message lisible par l'utilisateur) si la configuration est refusée."""
    if not isinstance(recipients, (list, tuple)) or len(recipients) != config.NB_RECIPIENTS:
        raise ValueError("Il faut exactement {} récipients.".format(config.NB_RECIPIENTS))
    deja_vus = {}
    for i, valeur in enumerate(recipients):
        ingredient = _nettoyer(valeur)
        if ingredient is None:
            continue
        if ingredient not in connus:
            raise ValueError("Ingrédient inconnu : {}.".format(ingredient))
        if ingredient in deja_vus:
            raise ValueError("« {} » est déjà dans le récipient {}.".format(ingredient, deja_vus[ingredient]))
        deja_vus[ingredient] = i + 1


def charger():
    """Liste de 4 éléments (ingrédient ou None). Par défaut : 4 récipients vides."""
    donnees = storage.lire_json(config.trouver_data(config.FICHIER_CONFIG), None)
    if isinstance(donnees, dict):
        liste = donnees.get("recipients")
        if isinstance(liste, list) and len(liste) == config.NB_RECIPIENTS:
            return [_nettoyer(x) for x in liste]
    return [None] * config.NB_RECIPIENTS


def enregistrer(recipients, connus):
    """Valide puis sauvegarde. Renvoie la liste nettoyée. Lève ValueError si refusé."""
    valider(recipients, connus)
    propre = [_nettoyer(x) for x in recipients]
    storage.ecrire_json(config.chemin_data(config.FICHIER_CONFIG), {"version": VERSION, "recipients": propre})
    return propre


def pompe_pour(ingredient, recipients):
    """Index de la pompe (0 à 3) qui contient cet ingrédient, ou None s'il n'est pas chargé."""
    for i, valeur in enumerate(recipients):
        if valeur == ingredient:
            return i
    return None
