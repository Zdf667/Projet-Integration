# US4.3 – Mode administrateur protégé par un code PIN.
#
#  - un seul administrateur à la fois : une nouvelle connexion remplace l'ancienne ;
#  - la session est un jeton aléatoire envoyé dans un cookie ;
#  - après config.DELAI_INACTIVITE_S sans action, retour au mode utilisateur ;
#  - après config.ESSAIS_MAX erreurs de PIN, blocage pendant config.BLOCAGE_S secondes.
# Le PIN est dans data/admin.json (changeable depuis le mode administrateur), sinon PIN_ADMIN_DEFAUT.
import os

from app import config, horloge, storage

_session = {"jeton": None, "dernier": 0}
_echecs = {"n": 0, "jusqua": None}


def pin_actuel():
    donnees = storage.lire_json(config.trouver_data(config.FICHIER_ADMIN), None)
    if isinstance(donnees, dict) and isinstance(donnees.get("pin"), str) and donnees["pin"]:
        return donnees["pin"]
    return config.PIN_ADMIN_DEFAUT


def pin_valide(pin):
    return isinstance(pin, str) and 4 <= len(pin) <= 8 and pin.isdigit()


def definir_pin(nouveau, confirmation):
    if nouveau != confirmation:
        raise ValueError("Les deux codes ne sont pas identiques.")
    if not pin_valide(nouveau):
        raise ValueError("Le code doit contenir 4 à 8 chiffres.")
    storage.ecrire_json(config.chemin_data(config.FICHIER_ADMIN), {"pin": nouveau})


def _egal(a, b):
    """Comparaison qui prend le même temps que les textes soient proches ou non."""
    if len(a) != len(b):
        return False
    reste = 0
    for x, y in zip(a, b):
        reste |= ord(x) ^ ord(y)
    return reste == 0


def _jeton():
    return "".join("{:02x}".format(octet) for octet in os.urandom(16))


def secondes_de_blocage():
    if _echecs["jusqua"] is None:
        return 0
    reste = -horloge.ecart(horloge.ms(), _echecs["jusqua"]) // 1000 + 1
    if reste <= 0:
        _echecs["jusqua"] = None
        _echecs["n"] = 0
        return 0
    return reste


def connecter(pin):
    """Renvoie le jeton de session, ou lève ValueError (message affichable)."""
    reste = secondes_de_blocage()
    if reste:
        raise ValueError("Trop d'essais. Réessayez dans {} s.".format(reste))
    if not _egal(str(pin), pin_actuel()):
        _echecs["n"] += 1
        if _echecs["n"] >= config.ESSAIS_MAX:
            _echecs["jusqua"] = horloge.ms() + config.BLOCAGE_S * 1000
            raise ValueError("Trop d'essais. Réessayez dans {} s.".format(config.BLOCAGE_S))
        raise ValueError("Code incorrect.")
    _echecs["n"] = 0
    _session["jeton"] = _jeton()
    _session["dernier"] = horloge.ms()
    return _session["jeton"]


def verifier(jeton):
    """True si la session est valide ; chaque action renouvelle le délai d'inactivité."""
    if not jeton or _session["jeton"] is None or not _egal(jeton, _session["jeton"]):
        return False
    if horloge.ecart(horloge.ms(), _session["dernier"]) > config.DELAI_INACTIVITE_S * 1000:
        _session["jeton"] = None
        return False
    _session["dernier"] = horloge.ms()
    return True


def deconnecter():
    _session["jeton"] = None
