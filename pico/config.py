# Réglages communs de la machine à cocktail (Pico W, MicroPython).
# Un seul endroit pour les réglages : si le groupe change quelque chose, on ne modifie que ce fichier.

# --- Machine -----------------------------------------------------------------------------
NB_RECIPIENTS = 4            # récipient n = pompe n (le pilotage des pompes viendra avec US3.1)

# --- Fichiers sur la Pico ----------------------------------------------------------------
DOSSIER = ""                 # "" = racine de la Pico (les tests sur PC changent cette valeur)
FICHIER_CONFIG = "config.json"      # ingrédient de chaque récipient (US1.1)
FICHIER_RECETTES = "recettes.json"  # ingrédients connus + recettes (US2.1)
FICHIER_WIFI = "wifi.json"          # {"ssid": "...", "mot_de_passe": "..."} (facultatif)

# --- Réseau provisoire (en attendant US4.6) ----------------------------------------------
PORT_WEB = 80
AP_SSID = "Cocktail-Machine"
AP_MOT_DE_PASSE = "cocktail2026"    # 8 caractères minimum (WPA2)


def chemin(nom):
    return DOSSIER + nom
