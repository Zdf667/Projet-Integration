# Lancé automatiquement au démarrage de la Pico.
import asyncio

from app import config, dns, led, pompes, reseau, serveur

pompes.init()                       # relais coupés dès le départ
ip = reseau.demarrer()              # client Wi-Fi ou point d'accès (US4.6)
print("Ouvrir http://{}/ dans le navigateur".format(ip))
if reseau.info().get("mode") == "ap":
    print("ou http://{}/ (n'importe quel nom : cocktail.local, cocktail.box...)".format(config.NOM_MACHINE + ".box"))
else:
    print("ou http://{}.local/".format(config.NOM_MACHINE))


async def principal():
    asyncio.create_task(led.boucle())   # voyant d'état (US4.2)
    if reseau.info().get("mode") == "ap":
        asyncio.create_task(dns.lancer(ip))   # US perso : un nom pour la machine
    await serveur.lancer()


asyncio.run(principal())
