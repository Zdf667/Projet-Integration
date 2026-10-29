# US3.1 – Piloter les 4 pompes, par le module 4 relais.
#
# Pompe n (1 à 4) = relais n = broche config.PINS_RELAIS[n-1] (GP2 à GP5).
# Notre module est « actif bas » : broche à 0 V = relais collé = pompe qui tourne.
# Les broches sont créées déjà à l'état « arrêt », pour que les relais ne claquent pas au démarrage.
#
# Sur PC (tests), il n'y a pas de module « machine » : de fausses broches mémorisent leur état.
from app import config

try:
    from machine import Pin
except ImportError:
    Pin = None


class _FausseBroche:
    def __init__(self, numero, valeur):
        self.numero = numero
        self._v = valeur

    def value(self, v=None):
        if v is None:
            return self._v
        self._v = v


_broches = []


def _niveau(allume):
    """Niveau électrique (0 ou 1) qui correspond à « allumé » ou « éteint »."""
    if config.RELAIS_ACTIF_BAS:
        return 0 if allume else 1
    return 1 if allume else 0


def init():
    """Crée les 4 broches, toutes éteintes. Peut être appelée plusieurs fois."""
    if _broches:
        return
    for numero in config.PINS_RELAIS:
        if Pin is None:
            _broches.append(_FausseBroche(numero, _niveau(False)))
        else:
            _broches.append(Pin(numero, Pin.OUT, value=_niveau(False)))


def _broche(n):
    if not isinstance(n, int) or n < 1 or n > config.NB_RECIPIENTS:
        raise ValueError("pompe inconnue : {}".format(n))
    init()
    return _broches[n - 1]


def pump_on(n):
    _broche(n).value(_niveau(True))


def pump_off(n):
    _broche(n).value(_niveau(False))


def stop_all():
    """Arrête les 4 pompes (utilisée aussi pour l'arrêt d'urgence logiciel, US3.4)."""
    init()
    for b in _broches:
        b.value(_niveau(False))


def est_allumee(n):
    return _broche(n).value() == _niveau(True)


def debit(n):
    """Débit de la pompe n en ml par seconde."""
    return config.DEBITS_ML_S[n - 1]


def duree_pour(n, ml):
    """Durée de marche (en secondes) pour verser `ml` millilitres avec la pompe n."""
    duree = ml / debit(n)
    if duree > config.DUREE_MAX_S:
        raise ValueError("{} ml dépasse la durée maximale d'une pompe".format(ml))
    return duree
