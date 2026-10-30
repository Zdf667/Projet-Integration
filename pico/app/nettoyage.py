# US5.1 – Nettoyage guidé : rinçage des 4 lignes, l'une après l'autre, avec le séquenceur.
# Les étapes affichées à l'administrateur sont dans pages_nettoyage.py.
from app import config, pompes, sequenceur


def plan():
    """Rinçage de chaque ligne : [(pompe, ml, durée en s, nom)]."""
    return [(n, config.NETTOYAGE_ML, pompes.duree_pour(n, config.NETTOYAGE_ML), "Ligne {}".format(n))
            for n in range(1, config.NB_RECIPIENTS + 1)]


def nettoyer():
    """Démarre un passage de rinçage des 4 lignes. Lève sequenceur.Occupe si une préparation est en cours."""
    if sequenceur.occupe():
        raise sequenceur.Occupe("Une préparation est déjà en cours.")
    sequenceur.lancer(plan(), "nettoyage", "Rinçage des 4 lignes", [])
