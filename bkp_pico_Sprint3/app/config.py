# Réglages communs de la machine à cocktail (Pico W, MicroPython).
# Un seul endroit pour les réglages : si le groupe change quelque chose, on ne modifie que ce fichier.
import os

# --- Machine -----------------------------------------------------------------------------
NB_RECIPIENTS = 4            # récipient n = pompe n (voir pompes.py)

# --- Dossiers et fichiers sur la Pico ----------------------------------------------------
DOSSIER = ""                 # "" = racine de la Pico (les tests sur PC changent cette valeur)
DOSSIER_DATA = "data/"       # données modifiables : recettes, ingrédients des récipients, Wi-Fi
DOSSIER_WEB = "web/"         # fichiers envoyés au navigateur : style, logo, icône
FICHIER_CONFIG = "config.json"      # ingrédient de chaque récipient (US1.1 / US1.2)
FICHIER_RECETTES = "recettes.json"  # ingrédients connus + recettes (US2.1)
FICHIER_WIFI = "wifi.json"          # {"ssid": "...", "mot_de_passe": "..."} (facultatif)

# --- Réseau (US4.6) -----------------------------------------------------------------------
PORT_WEB = 80
AP_SSID = "Cocktail-Machine"
AP_MOT_DE_PASSE = "cocktail2026"    # 8 caractères minimum (WPA2)
NOM_MACHINE = "cocktail"            # nom sur le réseau local (cocktail.local si le téléphone le comprend)
DELAI_CLIENT_S = 15                 # temps laissé à la box pour répondre avant de passer en point d'accès
PAYS_WIFI = "BE"
WIFI_MAX = 8                        # nombre de réseaux Wi-Fi qu'on peut enregistrer
WIFI_ESSAIS = 3                     # au démarrage, nombre de réseaux essayés avant de passer en point d'accès

# --- Pompes et relais (US3.1) -------------------------------------------------------------
PINS_RELAIS = (2, 3, 4, 5)          # GP2 à GP5 -> IN1 à IN4 du module 4 relais
RELAIS_ACTIF_BAS = True             # True : relais collé quand la broche est à 0 V (la masse), comme sur notre module
# Débit mesuré de chaque pompe (US3.2), en ml par seconde : 133,75 / 139,41 / 137,20 / 141,03 ml/min
DEBITS_ML_S = (2.23, 2.32, 2.29, 2.35)
DUREE_MAX_S = 240                   # garde-fou : une pompe ne tourne jamais plus longtemps d'affilée

# --- Ruban de LED d'état (US4.2) ----------------------------------------------------------
PIN_LED = 15                        # GP15 -> résistance 330 ohms -> fil de données (DIN) du ruban
LED_NB = 26                         # nombre de LED du ruban (WS2812 / NeoPixel, commandables une par une)
LED_LUMINOSITE = 0.25               # 0 à 1 : limite le courant (26 LED blanches à fond = plus de 1,5 A)

# --- Mode administrateur (US4.3) ----------------------------------------------------------
PIN_ADMIN_DEFAUT = "1234"           # à changer dans le mode administrateur (enregistré dans data/admin.json)
FICHIER_ADMIN = "admin.json"
DELAI_INACTIVITE_S = 300            # retour automatique au mode utilisateur après 5 minutes sans action
ESSAIS_MAX = 5                      # nombre d'erreurs de PIN avant blocage
BLOCAGE_S = 30                      # durée du blocage

# --- Nettoyage guidé (US5.1) --------------------------------------------------------------
NETTOYAGE_ML = 60                   # volume pompé dans chaque ligne à chaque rinçage


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
