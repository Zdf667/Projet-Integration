# Recettes chargées au démarrage (data/recettes.json) : contenu validé, ou message d'erreur.
# Toutes les routes lisent le catalogue ici : un seul endroit.
from app import recettes

_etat = {"data": None, "erreur": None}


def charger():
    try:
        _etat["data"] = recettes.charger()
        _etat["erreur"] = None
    except Exception as e:
        _etat["data"] = None
        _etat["erreur"] = str(e)
        print("recettes.json refusé :", e)


def data():
    return _etat["data"]


def erreur():
    return _etat["erreur"]


def connus():
    return _etat["data"]["ingredients"] if _etat["data"] else []
