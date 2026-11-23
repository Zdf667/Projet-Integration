# Recettes chargées au démarrage (data/recettes.json) : contenu validé, ou message d'erreur.
# Toutes les routes lisent le catalogue ici : un seul endroit.
import gc
import json
from app import config, recettes, storage

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

def importer(brut):
    """Analyse le JSON reçu, fusionne les nouvelles recettes sans doublon, écrit sur flash et recharge."""
    if not brut or not brut.strip():
        raise ValueError("Fichier JSON vide.")

    gc.collect()
    try:
        nouveau = json.loads(brut)
    except ValueError:
        raise ValueError("Format JSON invalide.")

    if not isinstance(nouveau, dict) or not isinstance(nouveau.get("recettes"), list):
        raise ValueError("Structure invalide : clé 'recettes' manquante.")

    if not _etat["data"]:
        raise ValueError("Catalogue actuel non chargé : impossible de fusionner.")

    # Copie de travail pour préserver l'intégrité en cas d'erreur de validation
    sauvegarde_ingredients = list(_etat["data"]["ingredients"])
    sauvegarde_recettes = list(_etat["data"]["recettes"])

    ingredients_fusion = list(sauvegarde_ingredients)
    recettes_fusion = list(sauvegarde_recettes)

    # Indexation des noms existants en minuscules pour éviter tout doublon
    noms_existants = set(r["nom"].strip().lower() for r in recettes_fusion if "nom" in r)
    ajouts = 0

    # Ajout des éventuels nouveaux ingrédients déclarés à la racine
    for ing in nouveau.get("ingredients", []):
        if isinstance(ing, str) and ing not in ingredients_fusion:
            ingredients_fusion.append(ing)

    # Fusion des nouvelles recettes et de leurs ingrédients associés
    for r in nouveau["recettes"]:
        if not isinstance(r, dict) or "nom" not in r:
            continue
        cle_nom = r["nom"].strip().lower()
        if cle_nom not in noms_existants:
            recettes_fusion.append(r)
            noms_existants.add(cle_nom)
            ajouts += 1
            for item in r.get("ingredients", []):
                if isinstance(item, dict):
                    nom_ing = item.get("ingredient")
                    if isinstance(nom_ing, str) and nom_ing not in ingredients_fusion:
                        ingredients_fusion.append(nom_ing)

    if ajouts == 0:
        return 0

    donnees_finales = {
        "version": _etat["data"].get("version", 3),
        "ingredients": ingredients_fusion,
        "recettes": recettes_fusion,
    }

    chemin_cible = config.chemin_data(config.FICHIER_RECETTES)
    storage.ecrire_json(chemin_cible, donnees_finales)

    # Revalidation complète par recettes.charger()
    charger()
    if _etat["erreur"]:
        # Rollback : le nouveau JSON a été rejeté par le validateur, on restaure l'état précédent
        erreur_validation = _etat["erreur"]
        storage.ecrire_json(chemin_cible, {
            "version": _etat["data"].get("version", 3) if _etat["data"] else 3,
            "ingredients": sauvegarde_ingredients,
            "recettes": sauvegarde_recettes,
        })
        charger()
        raise ValueError("Recette invalide refusée par la machine : " + erreur_validation)

    gc.collect()
    return ajouts


def synchroniser_cloud():
    """Télécharge le catalogue maître depuis GitHub Pages si le Wi-Fi client est connecté."""
    if not network or not urequests:
        return 0

    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        print("Sync Cloud ignorée : pas de connexion Wi-Fi client.")
        return 0

    url = getattr(config, "URL_CATALOGUE_CLOUD", "")
    if not url:
        return 0

    gc.collect()
    reponse = None
    try:
        print("Vérification des nouvelles recettes sur :", url)
        reponse = urequests.get(url)

        # Suivi manuel si redirection HTTP 301/302
        if reponse.status_code in (301, 302) and "Location" in reponse.headers:
            nouvelle_url = reponse.headers["Location"]
            reponse.close()
            gc.collect()
            reponse = urequests.get(nouvelle_url)

        if reponse.status_code == 200:
            brut = reponse.text
            reponse.close()
            reponse = None
            gc.collect()
            ajouts = importer(brut)
            print("Sync Cloud terminée : {} nouvelle(s) recette(s) ajoutée(s).".format(ajouts))
            return ajouts
        else:
            print("Sync Cloud échouée : code HTTP", reponse.status_code)
            return 0
    except Exception as e:
        print("Sync Cloud impossible :", e)
        return 0
    finally:
        if reponse:
            try:
                reponse.close()
            except Exception:
                pass
        gc.collect()