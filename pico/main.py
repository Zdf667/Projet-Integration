# Lancé automatiquement au démarrage de la Pico.
import asyncio

from app import led, pompes, reseau, serveur

pompes.init()                       # relais coupés dès le départ
ip = reseau.demarrer()              # client Wi-Fi ou point d'accès (US4.6)
print("Ouvrir http://{}/ dans le navigateur".format(ip))


async def principal():
    asyncio.create_task(led.boucle())   # voyant d'état (US4.2)
    await serveur.lancer()


asyncio.run(principal())
