# US6.2 – Détection du verre : cellule de charge + module HX711 (convertisseur 24 bits).
#
# Une tâche (boucle) lit le poids toutes les 0,3 s en arrière-plan ; present() répond sans attendre :
# le séquenceur peut donc refuser un départ sans bloquer le serveur web.
# Réglages (tare, facteur de calibration) : /admin/verre, enregistrés dans data/verre.json.
# Tant que config.VERRE_ACTIF est False (capteur pas encore branché), la détection est ignorée.
import asyncio

from app import config, erreurs, horloge, storage

try:
    from machine import Pin
except ImportError:
    Pin = None

PERIODE_S = 0.3
VALIDITE_MS = 3000          # une mesure plus vieille que 3 s n'est plus fiable

_etat = {"brut": None, "ms": 0}
_reglages = None
_lecteur = None


class Capteur:
    """Pilote minimal du HX711 : 24 impulsions d'horloge, plus une pour choisir le gain 128."""

    def __init__(self, dt, sck):
        self.dt = Pin(dt, Pin.IN)
        self.sck = Pin(sck, Pin.OUT, value=0)

    def pret(self):
        return self.dt.value() == 0

    def lire(self):
        valeur = 0
        for _ in range(24):
            self.sck.value(1)
            self.sck.value(0)
            valeur = (valeur << 1) | self.dt.value()
        self.sck.value(1)
        self.sck.value(0)
        if valeur & 0x800000:
            valeur -= 1 << 24
        return valeur


def _reg():
    global _reglages
    if _reglages is None:
        d = storage.lire_json(config.trouver_data(config.FICHIER_VERRE), None)
        if not isinstance(d, dict) or not isinstance(d.get("tare"), (int, float)) or not d.get("facteur"):
            d = {"tare": 0, "facteur": 1.0}
        _reglages = {"tare": d["tare"], "facteur": float(d["facteur"])}
    return _reglages


def _sauver():
    storage.ecrire_json(config.chemin_data(config.FICHIER_VERRE), _reg())


def actif():
    return bool(config.VERRE_ACTIF)


def simuler(brut):
    """Pour les tests sur PC : fixe la dernière mesure (None = capteur muet)."""
    _etat["brut"] = brut
    _etat["ms"] = horloge.ms()


def poids_g():
    """Poids en grammes selon la dernière mesure, ou None si le capteur ne répond plus."""
    if _etat["brut"] is None or horloge.ecart(horloge.ms(), _etat["ms"]) > VALIDITE_MS:
        return None
    r = _reg()
    return (_etat["brut"] - r["tare"]) / r["facteur"]


def present():
    p = poids_g()
    return p is not None and p >= config.VERRE_SEUIL_G


def verifier():
    """Lève ValueError (message clair) si la détection est active et qu'aucun verre n'est posé."""
    if not actif():
        return
    p = poids_g()
    if p is None:
        raise ValueError(erreurs.texte("verre_illisible"))
    if p < config.VERRE_SEUIL_G:
        raise ValueError(erreurs.texte("verre_absent"))


def tarer():
    """Le plateau est vide : la mesure actuelle devient le zéro."""
    if _etat["brut"] is None:
        raise ValueError(erreurs.texte("verre_illisible"))
    _reg()["tare"] = _etat["brut"]
    _sauver()


def calibrer(poids_connu_g):
    """Un objet de poids connu est posé : calcule le facteur (unités brutes par gramme)."""
    if _etat["brut"] is None:
        raise ValueError(erreurs.texte("verre_illisible"))
    if poids_connu_g <= 0:
        raise ValueError("Le poids de référence doit être supérieur à 0 g.")
    ecart = _etat["brut"] - _reg()["tare"]
    if ecart == 0:
        raise ValueError("Aucune variation mesurée : posez l'objet sur le plateau, après la tare.")
    _reg()["facteur"] = ecart / poids_connu_g
    _sauver()


def reglages():
    return dict(_reg())


async def boucle():
    """Lecture permanente du capteur (à lancer au démarrage si config.VERRE_ACTIF)."""
    global _lecteur
    if Pin is None:
        return
    try:
        _lecteur = Capteur(config.PIN_HX711_DT, config.PIN_HX711_SCK)
    except Exception as e:
        print("HX711 introuvable :", e)
        return
    while True:
        try:
            attente = 0
            while not _lecteur.pret() and attente < 100:
                await asyncio.sleep_ms(10)
                attente += 1
            if _lecteur.pret():
                _etat["brut"] = _lecteur.lire()
                _etat["ms"] = horloge.ms()
        except Exception as e:
            print("lecture HX711 :", e)
        await asyncio.sleep(PERIODE_S)