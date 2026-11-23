# US4.4 – Catalogue des messages d'erreur : un seul endroit, des phrases claires (ce qui se passe + que faire).
# Chaque message sert au site web, et servira à l'écran OLED (US4.5) : texte(code, ...) renvoie une phrase complète.

_MESSAGES = {
    "aucun_cocktail": "Aucun cocktail réalisable avec ces ingrédients. Changez un récipient en mode administrateur.",
    "arret": "Préparation arrêtée. Le verre est incomplet : videz-le avant de recommencer.",
    "occupe": "Une préparation est déjà en cours. Attendez qu'elle soit terminée.",
    "pompe": "La pompe {n} a un problème ({detail}). Toutes les pompes sont arrêtées : vérifiez le tuyau et l'alimentation.",
    "verre_absent": "Aucun verre détecté. Posez un verre sous le bec, puis relancez.",
    "verre_retire": "Le verre a été retiré : les pompes sont arrêtées. Replacez un verre et recommencez.",
    "verre_illisible": "Le capteur de verre ne répond pas. Vérifiez son câblage ou désactivez la détection.",
    "recettes": "Le fichier de recettes est inutilisable ({detail}). Corrigez data/recettes.json puis redémarrez la machine.",
    "wifi_introuvable": "Le réseau Wi-Fi « {ssid} » est introuvable. Rapprochez la machine de la box ou vérifiez son nom.",
    "wifi_mdp": "Le mot de passe du Wi-Fi « {ssid} » est refusé. Enregistrez-le à nouveau en mode administrateur.",
    "wifi_sans_reponse": "Le réseau Wi-Fi « {ssid} » ne répond pas. Vérifiez que la box est allumée.",
    "maj": "La mise à jour a échoué. La version précédente reste active : réessayez avec une connexion stable.",
}


def texte(code, **champs):
    """Message complet pour un code ; un code inconnu donne un message générique (jamais d'exception)."""
    modele = _MESSAGES.get(code)
    if modele is None:
        return "Une erreur est survenue. Arrêtez la préparation et réessayez."
    try:
        return modele.format(**champs)
    except (KeyError, IndexError):
        return modele
