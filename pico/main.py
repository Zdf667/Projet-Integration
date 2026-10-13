# Lancé automatiquement au démarrage de la Pico.
import asyncio

import reseau_provisoire
import serveur

ip = reseau_provisoire.demarrer()
print("Ouvrir http://{}/ dans le navigateur".format(ip))
asyncio.run(serveur.lancer())
