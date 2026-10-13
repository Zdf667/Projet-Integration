# Réglages communs de la machine à cocktail (Pico W, MicroPython).
# Un seul endroit pour les réglages : si le groupe change quelque chose, on ne modifie que ce fichier.
import os

# --- Machine -----------------------------------------------------------------------------
NB_RECIPIENTS = 4            # récipient n = pompe n (le pilotage des pompes viendra avec US3.1)

# --- Dossiers et fichiers sur la Pico ----------------------------------------------------
DOSSIER = ""                 # "" = racine de la Pico (les tests sur PC changent cette valeur)
DOSSIER_DATA = "data/"       # données modifiables : recettes, ingrédients des récipients, Wi-Fi
DOSSIER_WEB = "web/"         # fichiers envoyés au navigateur : style, logo, icône
FICHIER_CONFIG = "config.json"      # ingrédient de chaque récipient (US1.1 / US1.2)
FICHIER_RECETTES = "recettes.json"  # ingrédients connus + recettes (US2.1)
FICHIER_WIFI = "wifi.json"          # {"ssid": "...", "mot_de_passe": "..."} (facultatif)

# --- Réseau provisoire (en attendant US4.6) ----------------------------------------------
PORT_WEB = 80
AP_SSID = "Cocktail-Machine"
AP_MOT_DE_PASSE = "cocktail2026"    # 8 caractères minimum (WPA2)


def chemin(nom):
    return DOSSIER + nom


def chemin_data(nom):
    """Chemin d'un fichier de données, pour l'écrire : toujours dans data/."""
    return DOSSIER + DOSSIER_DATA + nom


def trouver_data(nom):
    """Chemin d'un fichier de données, pour le lire : data/ d'abord, puis l'ancien emplacement (racine).

    Évite de perdre la configuration d'une Pico déjà utilisée avant le rangement en sous-dossiers.
    """
    nouveau = chemin_data(nom)
    try:
        os.stat(nouveau)
        return nouveau
    except OSError:
        pass
    ancien = chemin(nom)
    try:
        os.stat(ancien)
        return ancien
    except OSError:
        return nouveau
