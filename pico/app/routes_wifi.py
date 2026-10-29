#   GET  /admin/wifi[?scan=1]   réseau actuel, réseaux enregistrés, recherche des réseaux
#   POST /admin/wifi            ajoute un réseau (sans effacer les autres), puis redémarre
#   POST /admin/wifi/oublier    oublie un réseau (ssid=...) ou tous (ssid vide), puis redémarre
import asyncio

from app import config, pages_wifi, reseau
from app.http_outils import exiger_admin, parse_form, repondre


async def _redemarrer_bientot():
    """Laisse partir la réponse, puis redémarre la Pico pour appliquer le changement de Wi-Fi."""
    await asyncio.sleep(1.5)
    try:
        import machine
        machine.reset()
    except ImportError:
        print("(PC) redémarrage demandé")


async def traiter(w, methode, chemin, requete, corps, cookie):
    if chemin not in ("/admin/wifi", "/admin/wifi/oublier"):
        return False
    if not await exiger_admin(w, cookie):
        return True

    if chemin == "/admin/wifi":
        if methode == "GET":
            liste = reseau.scanner() if "scan=1" in requete else None
            await repondre(w, 200, pages_wifi.page_wifi(reseau.info(), reseau.lire_reseaux(), liste))
        elif methode == "POST":
            champs = parse_form(corps)
            ssid = champs.get("ssid", "").strip() or champs.get("ssid_liste", "")
            try:
                reseau.enregistrer_identifiants(ssid, champs.get("mdp", ""))
            except ValueError as e:
                await repondre(w, 400, pages_wifi.page_wifi(reseau.info(), reseau.lire_reseaux(),
                                                            erreur=str(e), ssid_saisi=ssid))
            else:
                asyncio.create_task(_redemarrer_bientot())
                await repondre(w, 200, pages_wifi.page_redemarrage(
                    "Wi-Fi « {} » ajouté. La machine redémarre et essaie de s'y connecter.".format(ssid)))
        else:
            await repondre(w, 405, "Méthode non autorisée")
        return True

    # /admin/wifi/oublier
    if methode != "POST":
        await repondre(w, 405, "Méthode non autorisée")
        return True
    ssid = parse_form(corps).get("ssid", "")
    if ssid:
        try:
            reseau.oublier_reseau(ssid)
        except ValueError as e:
            await repondre(w, 400, pages_wifi.page_wifi(reseau.info(), reseau.lire_reseaux(), erreur=str(e)))
            return True
        texte = "Wi-Fi « {} » oublié. La machine redémarre.".format(ssid)
    else:
        reseau.oublier_identifiants()
        texte = "Tous les réseaux sont oubliés. La machine redémarre en point d'accès « {} ».".format(config.AP_SSID)
    asyncio.create_task(_redemarrer_bientot())
    await repondre(w, 200, pages_wifi.page_redemarrage(texte))
    return True
