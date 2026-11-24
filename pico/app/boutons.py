from app import config, horloge

try:
    from machine import Pin
except ImportError:          
    Pin = None

NOMS = ("haut", "bas", "ok", "retour", "info", "stop")
PINS_DEFAUT = (9, 2, 3, 4, 5, 14)        
PERIODE_MS = 10                           
ANTI_REBOND_MS = 30
REPETITION_DEBUT_MS = 500                
REPETITION_MS = 150                       
A_REPETITION = ("haut", "bas")


class _FausseBroche:
    def __init__(self):
        self._v = 1                      

    def value(self, v=None):
        if v is None:
            return self._v
        self._v = v


_boutons = []


def pins():
    return getattr(config, "PINS_BOUTONS", PINS_DEFAUT)

def _broches_prises():
    """Broches déjà utilisées ailleurs dans config.py (relais, ruban, HX711) : jamais pour un bouton."""
    prises = set(getattr(config, "PINS_RELAIS", ()))
    for nom in ("PIN_LED", "PIN_HX711_DT", "PIN_HX711_SCK"):
        if hasattr(config, nom):
            prises.add(getattr(config, nom))
    return prises

def init():
    """Crée les 6 entrées. Peut être appelée plusieurs fois."""
    if _boutons:
        return
    conflit = [n for n in pins() if n in _broches_prises()]
    if conflit:
        raise ValueError("boutons : broche(s) GP{} déjà utilisée(s) par les relais, le ruban ou le HX711".format(conflit))
    for nom, numero in zip(NOMS, pins()):
        broche = _FausseBroche() if Pin is None else Pin(numero, Pin.IN, Pin.PULL_UP)
        _boutons.append({"nom": nom, "numero": numero, "broche": broche,
                         "appuye": False, "brut": False, "depuis": 0, "rep": 0, "delai": 0})


def scruter(maintenant=None):
    """Liste des boutons appuyés depuis le dernier appel (après anti-rebond)."""
    init()
    if maintenant is None:
        maintenant = horloge.ms()
    evenements = []
    for b in _boutons:
        brut = b["broche"].value() == 0
        if brut != b["brut"]:                 
            b["brut"] = brut
            b["depuis"] = maintenant
            continue
        if brut != b["appuye"]:
            if horloge.ecart(maintenant, b["depuis"]) >= ANTI_REBOND_MS:
                b["appuye"] = brut
                if brut:
                    evenements.append(b["nom"])
                    b["rep"] = maintenant
                    b["delai"] = REPETITION_DEBUT_MS
        elif brut and b["nom"] in A_REPETITION and horloge.ecart(maintenant, b["rep"]) >= b["delai"]:
            evenements.append(b["nom"])
            b["rep"] = maintenant
            b["delai"] = REPETITION_MS
    return evenements


def est_appuye(nom):
    """État stable (après anti-rebond) d'un bouton."""
    init()
    for b in _boutons:
        if b["nom"] == nom:
            return b["appuye"]
    raise ValueError("bouton inconnu : {}".format(nom))


def simuler(nom, appuye):
    """Tests sur PC uniquement : appuie (True) ou relâche (False) un faux bouton."""
    init()
    for b in _boutons:
        if b["nom"] == nom:
            b["broche"].value(0 if appuye else 1)
            return
    raise ValueError("bouton inconnu : {}".format(nom))