# Temps en millisecondes, identique sur la Pico (ticks_ms) et sur PC (pour les tests).
import time

try:
    _ticks = time.ticks_ms
    ecart = time.ticks_diff       # ecart(a, b) = a - b, sans problème de débordement
except AttributeError:            # CPython (tests sur PC)
    def _ticks():
        return int(time.monotonic() * 1000)

    def ecart(a, b):
        return a - b


def ms():
    return _ticks()
