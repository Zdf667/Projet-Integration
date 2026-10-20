# Réseau PROVISOIRE, juste pour pouvoir ouvrir la page sur la Pico en attendant US4.6.
# US4.6 le remplacera (saisie du Wi-Fi depuis le mode admin, page 100 % embarquée, affichage sur l'écran).
#
# Comportement :
#  1. si wifi.json existe ({"ssid": "...", "mot_de_passe": "..."}), essaie de se connecter 15 s ;
#  2. sinon, ou en cas d'échec, crée son propre réseau (point d'accès) : config.AP_SSID / AP_MOT_DE_PASSE.
# Dans les deux cas, renvoie l'adresse IP à taper dans le navigateur.
import time

import network

from app import config, storage


def _point_acces():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=config.AP_SSID, password=config.AP_MOT_DE_PASSE)
    ap.active(True)
    while not ap.active():
        time.sleep(0.1)
    print("Point d'accès :", config.AP_SSID, "/", config.AP_MOT_DE_PASSE)
    return ap.ifconfig()[0]


def demarrer():
    try:
        import rp2
        rp2.country("BE")
    except Exception:
        pass

    cfg = storage.lire_json(config.trouver_data(config.FICHIER_WIFI), None)
    if isinstance(cfg, dict) and cfg.get("ssid"):
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.connect(cfg["ssid"], cfg.get("mot_de_passe", ""))
        for _ in range(150):
            if sta.isconnected():
                print("Connecté au Wi-Fi", cfg["ssid"])
                return sta.ifconfig()[0]
            time.sleep(0.1)
        print("Connexion Wi-Fi échouée, passage en point d'accès")
        sta.active(False)
    return _point_acces()
