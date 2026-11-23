import asyncio

from app import interface_machine, pompes

pompes.init()                   
print("Haut/Bas : choisir, OK : voir puis lancer, Retour, STOP : arrêter, Info : réseau. Ctrl+C pour sortir.")
try:
    asyncio.run(interface_machine.boucle())
finally:
    pompes.stop_all()