# US3.3 – Séquenceur de recette : verse les ingrédients un par un, sans bloquer le serveur web.
#
# Une seule préparation à la fois, quelle que soit l'origine de la commande (téléphone, plus tard écran et boutons).
# Machine à états :  attente -> en_cours -> termine | erreur   (puis retour à « attente » avec acquitter()).
# Les pompes sont TOUJOURS arrêtées à la fin, même après une erreur ou un arrêt (bloc finally).
#
# Pour ajouter plus tard un écran OLED : appeler  sequenceur.ecouter(ma_fonction)  ;
# ma_fonction(etat) reçoit le dictionnaire d'état à chaque changement (la LED fait déjà comme ça).
import asyncio

from app import horloge, ingredients, pompes

ATTENTE = "attente"
EN_COURS = "en_cours"
TERMINE = "termine"
ERREUR = "erreur"

_etat = {"etat": ATTENTE, "mode": "", "titre": "", "etape": 0, "etapes": 0, "pct": 0, "message": "", "conseil": []}
_tache = None
_numero = 0          # identifie la préparation en cours : une ancienne tâche arrêtée ne touche pas à la nouvelle
_ecouteurs = []


class Occupe(Exception):
    """Une préparation est déjà en cours."""


def ecouter(fonction):
    _ecouteurs.append(fonction)


def _maj(**champs):
    _etat.update(champs)
    for f in _ecouteurs:
        try:
            f(_etat)
        except Exception as e:
            print("écouteur en erreur :", e)


def etat():
    """Copie de l'état courant (pour /status et pour les pages)."""
    copie = dict(_etat)
    copie["conseil"] = list(_etat["conseil"])
    return copie


def occupe():
    return _etat["etat"] == EN_COURS


def acquitter():
    """Revient à « attente » après un verre prêt ou une erreur."""
    if _etat["etat"] in (TERMINE, ERREUR):
        _maj(etat=ATTENTE, mode="", titre="", etape=0, etapes=0, pct=0, message="", conseil=[])


def planifier(recette, recipients):
    """Liste des étapes [(pompe 1 à 4, ml, durée en s, nom)] ; ValueError si un ingrédient n'est pas chargé."""
    plan = []
    for ligne in recette["ingredients"]:
        i = ingredients.pompe_pour(ligne["ingredient"], recipients)
        if i is None:
            raise ValueError("« {} » n'est dans aucun récipient.".format(ligne["ingredient"]))
        plan.append((i + 1, ligne["ml"], pompes.duree_pour(i + 1, ligne["ml"]), ligne["ingredient"]))
    return plan


def lancer(plan, mode, titre, conseil):
    global _tache, _numero
    if occupe():
        raise Occupe("Une préparation est déjà en cours.")
    _numero += 1
    _maj(etat=EN_COURS, mode=mode, titre=titre, etape=0, etapes=len(plan), pct=0, message="Démarrage", conseil=[])
    _tache = asyncio.create_task(_executer(plan, conseil, _numero))


def servir(recette, recipients):
    """Démarre un cocktail. Lève Occupe ou ValueError (rien n'est lancé dans ce cas)."""
    if occupe():
        raise Occupe("Une préparation est déjà en cours.")
    plan = planifier(recette, recipients)
    lancer(plan, "cocktail", recette["nom"], list(recette.get("conseil", [])))


def arreter():
    """Arrêt immédiat : les pompes s'arrêtent tout de suite. Renvoie True si quelque chose tournait."""
    pompes.stop_all()
    if not occupe():
        return False
    if _tache is not None:
        _tache.cancel()
    _maj(etat=ERREUR, message="Arrêté")
    return True


async def _executer(plan, conseil, numero):
    total = sum(etape[2] for etape in plan)
    fait = 0.0
    try:
        for i, (n, ml, duree, nom) in enumerate(plan):
            _maj(etape=i + 1, message="{} : {} ml".format(nom, ml))
            pompes.pump_on(n)
            debut = horloge.ms()
            while True:
                ecoule = horloge.ecart(horloge.ms(), debut) / 1000
                if ecoule >= duree:
                    break
                _maj(pct=int(100 * (fait + ecoule) / total))
                await asyncio.sleep(min(0.25, duree - ecoule))
            pompes.pump_off(n)
            fait += duree
        _maj(etat=TERMINE, pct=100, message="Verre prêt" if _etat["mode"] == "cocktail" else "Rinçage terminé",
             conseil=conseil)
    except asyncio.CancelledError:
        if numero == _numero:
            _maj(etat=ERREUR, message="Arrêté")
        raise
    except Exception as e:
        if numero == _numero:
            _maj(etat=ERREUR, message="Erreur : {}".format(e))
    finally:
        if numero == _numero:
            pompes.stop_all()
