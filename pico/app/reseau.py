
# Au démarrage :
#  va chercher dans data/wifi.json les réseaux enregistré puis essae de s'y connecter
# Si pas connecté, crée son propre réseau
import os
import time

from app import config, storage

try:
    import network
except ImportError:          # tests sur PC
    network = None

# mode : "client", "ap" ou "aucun" ; raison : pourquoi on est en point d'accès
_info = {"mode": "aucun", "ssid": "", "ip": "", "raison": ""}


def info():
    return dict(_info)


def chemin_wifi():
    return config.trouver_data(config.FICHIER_WIFI)


def lire_reseaux():
    """Réseaux enregistrés : liste de {"ssid", "mot_de_passe"}. Lit aussi l'ancien format (un seul réseau)."""
    cfg = storage.lire_json(chemin_wifi(), None)
    if not isinstance(cfg, dict):
        return []
    liste = cfg.get("reseaux")
    if liste is None and cfg.get("ssid"):
        liste = [cfg]
    resultat = []
    for r in liste or []:
        if isinstance(r, dict) and r.get("ssid"):
            resultat.append({"ssid": r["ssid"], "mot_de_passe": r.get("mot_de_passe", "")})
    return resultat


def _sauver(reseaux):
    storage.ecrire_json(config.chemin_data(config.FICHIER_WIFI), {"reseaux": reseaux})


def enregistrer_identifiants(ssid, mot_de_passe):
    """Ajoute un réseau (ou met à jour son mot de passe) sans toucher aux autres."""
    ssid = (ssid or "").strip()
    mot_de_passe = mot_de_passe or ""
    if not ssid or len(ssid) > 32:
        raise ValueError("Le nom du réseau doit faire de 1 à 32 caractères.")
    if mot_de_passe and not 8 <= len(mot_de_passe) <= 63:
        raise ValueError("Le mot de passe Wi-Fi doit faire de 8 à 63 caractères (ou rester vide si le réseau est ouvert).")
    reseaux = [r for r in lire_reseaux() if r["ssid"] != ssid]
    reseaux.append({"ssid": ssid, "mot_de_passe": mot_de_passe})
    if len(reseaux) > config.WIFI_MAX:
        raise ValueError("{} réseaux au maximum : oubliez-en un d'abord.".format(config.WIFI_MAX))
    _sauver(reseaux)


def oublier_reseau(ssid):
    """Oublie un seul réseau."""
    reseaux = lire_reseaux()
    restant = [r for r in reseaux if r["ssid"] != ssid]
    if len(restant) == len(reseaux):
        raise ValueError("Réseau inconnu.")
    if restant:
        _sauver(restant)
    else:
        oublier_identifiants()


def oublier_identifiants():
    """Oublie tous les réseaux : au prochain démarrage, la machine crée son propre réseau."""
    for chemin in (config.chemin_data(config.FICHIER_WIFI), config.chemin(config.FICHIER_WIFI)):
        try:
            os.remove(chemin)
        except OSError:
            pass


def scanner():
    """Noms des réseaux visibles, du plus fort au plus faible. Liste vide en cas d'échec."""
    if network is None:
        return []
    try:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        trouves = sta.scan()
    except Exception as e:
        print("scan Wi-Fi impossible :", e)
        return []
    trouves.sort(key=lambda r: -r[3])
    noms = []
    for r in trouves:
        try:
            nom = r[0].decode()
        except Exception:
            continue
        if nom and nom not in noms:
            noms.append(nom)
    return noms


def _point_acces(raison):
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=config.AP_SSID, password=config.AP_MOT_DE_PASSE)
    ap.active(True)
    while not ap.active():
        time.sleep(0.1)
    _info.update(mode="ap", ssid=config.AP_SSID, ip=ap.ifconfig()[0], raison=raison)
    print("Point d'accès :", config.AP_SSID, "/", config.AP_MOT_DE_PASSE)
    return _info["ip"]


def _client(cfg):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(cfg["ssid"], cfg.get("mot_de_passe", ""))
    for _ in range(config.DELAI_CLIENT_S * 10):
        if sta.isconnected():
            _info.update(mode="client", ssid=cfg["ssid"], ip=sta.ifconfig()[0], raison="")
            print("Connecté au Wi-Fi", cfg["ssid"], sta.ifconfig()[0])
            return _info["ip"]
        time.sleep(0.1)
    sta.disconnect()
    return None


def _ordre(reseaux):
    """Réseaux à essayer : d'abord ceux qu'on voit (le plus fort en premier), puis les autres au cas où."""
    visibles = scanner()
    vus = [r for nom in visibles for r in reseaux if r["ssid"] == nom]
    return vus + [r for r in reseaux if r not in vus]


def demarrer():
    """Choisit le mode réseau et renvoie l'adresse IP à taper dans le navigateur."""
    try:
        import rp2
        rp2.country(config.PAYS_WIFI)
    except Exception:
        pass
    try:
        network.hostname(config.NOM_MACHINE)
    except Exception:
        pass

    reseaux = lire_reseaux()
    if not reseaux:
        return _point_acces("Aucun Wi-Fi enregistré")
    for cfg in _ordre(reseaux)[:config.WIFI_ESSAIS]:
        ip = _client(cfg)
        if ip:
            return ip
    noms = ", ".join(r["ssid"] for r in reseaux)
    return _point_acces("aucun réseau enregistré ({}) n'a répondu (éteint, mot de passe faux ou trop loin)".format(noms))


def adresse():
    """Adresse à afficher à l'utilisateur."""
    return "http://{}/".format(_info["ip"]) if _info["ip"] else ""
