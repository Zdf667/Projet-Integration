# Lancé automatiquement au démarrage de la Pico.
import asyncio

from app import catalogue, config, dns, led, pompes, reseau, serveur
from app import interface_machine

pompes.init()                       # relais coupés dès le départ
interface_machine.ecran_demarrage()
ip = reseau.demarrer()              # client Wi-Fi ou point d'accès (US4.6)
print("Ouvrir http://{}/ dans le navigateur".format(ip))

catalogue.charger()
if reseau.info().get("mode") == "ap":
    print("ou http://{}/ (n'importe quel nom : cocktail.local, cocktail.box...)".format(config.NOM_MACHINE + ".box"))
else:
    print("ou http://{}.local/".format(config.NOM_MACHINE))
    catalogue.synchroniser_cloud()


async def principal():
    asyncio.create_task(led.boucle())   # voyant d'état (US4.2)
    asyncio.create_task(interface_machine.boucle())
    if reseau.info().get("mode") == "ap":
        asyncio.create_task(dns.lancer(ip))   # US perso : un nom pour la machine
    await serveur.lancer()


asyncio.run(principal())