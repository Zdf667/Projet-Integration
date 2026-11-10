# Lecture / écriture de fichiers JSON sur la Pico.
# L'écriture est « atomique » : on écrit dans un fichier .tmp puis on le renomme sur l'ancien.
# Une coupure de courant laisse donc soit l'ancien fichier, soit le nouveau, jamais un fichier à moitié écrit.
import json
import os
import sys

_MICROPYTHON = sys.implementation.name == "micropython"


def _ouvrir(chemin, mode):
    if _MICROPYTHON:
        return open(chemin, mode)
    return open(chemin, mode, encoding="utf-8")


def lire_json(chemin, defaut=None):
    """Renvoie le contenu JSON, ou `defaut` si le fichier est absent ou illisible."""
    try:
        with _ouvrir(chemin, "r") as f:
            return json.load(f)
    except OSError:
        return defaut
    except ValueError:
        print("storage : JSON invalide dans", chemin)
        return defaut


def _creer_dossier(chemin):
    """Crée le dossier qui contiendra le fichier (data/ au premier enregistrement)."""
    dossier = chemin.rpartition("/")[0]
    if dossier:
        try:
            os.mkdir(dossier)
        except OSError:
            pass          # existe déjà


def ecrire_json(chemin, donnees):
    _creer_dossier(chemin)
    tmp = chemin + ".tmp"
    with _ouvrir(tmp, "w") as f:
        json.dump(donnees, f)
    try:
        os.rename(tmp, chemin)
    except OSError:
        # certains systèmes de fichiers refusent de renommer sur un fichier existant
        try:
            os.remove(chemin)
        except OSError:
            pass
        os.rename(tmp, chemin)
