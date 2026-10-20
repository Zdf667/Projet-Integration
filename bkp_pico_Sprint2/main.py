# Lancé automatiquement au démarrage de la Pico.
import asyncio

from app import reseau_provisoire, serveur

ip = reseau_provisoire.demarrer()
print("Ouvrir http://{}/ dans le navigateur".format(ip))

asyncio.run(serveur.lancer())
