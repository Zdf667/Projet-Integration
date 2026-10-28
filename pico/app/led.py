# US4.2 – Ruban de LED adressables (WS2812 / NeoPixel) : config.LED_NB LED commandables une par une, un seul fil de données.
#
#   prête        tout le ruban en vert doux
#   en cours     barre orange qui se remplit avec l'avancement (chaque LED = 1/26 de la préparation)
#   verre prêt   tout le ruban flashe en vert deux fois, puis une pause
#   erreur       tout le ruban clignote vite en rouge
#   nettoyage    petit train violet qui tourne le long du ruban
#
# Pour changer un effet ou une couleur : modifier seulement couleurs() ci-dessous.
# couleurs() ne touche à aucune broche : elle renvoie la liste des couleurs, donc elle se teste sur PC.
# La luminosité est limitée (config.LED_LUMINOSITE) : 26 LED en blanc pleine puissance tirent plus de 1,5 A.
import asyncio

from app import config, horloge, sequenceur

try:
    from machine import Pin
    import neopixel
except ImportError:           # tests sur PC
    Pin = None
    neopixel = None

ETEINT = (0, 0, 0)
VERT = (0, 255, 0)
VERT_DOUX = (0, 70, 0)
ORANGE = (255, 110, 0)
ROUGE = (255, 0, 0)
VIOLET = (120, 0, 255)
PAS_MS = 80                   # une image toutes les 80 ms

_ruban = None


def _creer():
    global _ruban
    if _ruban is None and neopixel is not None:
        _ruban = neopixel.NeoPixel(Pin(config.PIN_LED), config.LED_NB)
    return _ruban


def nom_motif(etat):
    """Quel effet pour cet état ? (le rinçage en cours a son propre effet)"""
    if etat["etat"] == "en_cours" and etat["mode"] == "nettoyage":
        return "nettoyage"
    return etat["etat"]


def couleurs(etat, t_ms):
    """Liste de config.LED_NB couleurs (r, g, b) pour cet état à l'instant t_ms."""
    n = config.LED_NB
    nom = nom_motif(etat)
    if nom == "en_cours":
        k = n * etat["pct"] // 100
        image = [ORANGE] * k + [ETEINT] * (n - k)
        if k < n and (t_ms // 250) % 2:        # la LED qui se remplit clignote
            image[k] = ORANGE
        return image
    if nom == "termine":
        phase = t_ms % 1400
        allume = phase < 160 or 320 <= phase < 480
        return [VERT if allume else ETEINT] * n
    if nom == "erreur":
        return [ROUGE if (t_ms // 150) % 2 else ETEINT] * n
    if nom == "nettoyage":
        tete = (t_ms // PAS_MS) % n
        return [VIOLET if (i - tete) % n < 5 else ETEINT for i in range(n)]
    return [VERT_DOUX] * n                     # attente


def _echelle(c):
    k = config.LED_LUMINOSITE
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))


def afficher(image):
    ruban = _creer()
    if ruban is None:
        return
    for i, c in enumerate(image):
        ruban[i] = _echelle(c)
    ruban.write()


async def boucle():
    if _creer() is None:
        return
    derniere = None
    while True:
        image = couleurs(sequenceur.etat(), horloge.ms())
        if image != derniere:                  # on n'écrit que si l'image a changé
            afficher(image)
            derniere = image
        await asyncio.sleep(PAS_MS / 1000)