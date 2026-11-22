import time

from app import boutons, st7789
from app.st7789 import BLANC, GRIS, NOIR, ORANGE, VERT

DUREE_S = 60
ETIQUETTES = {"haut": "Haut", "bas": "Bas", "ok": "OK", "retour": "Retour", "info": "Info", "stop": "STOP"}

ecran = st7789.creer()
ecran.effacer(NOIR)
ecran.rect(0, 0, 240, 30, ORANGE)
ecran.texte("Test boutons", 8, 7, NOIR, ORANGE, taille=2)

comptes = {nom: 0 for nom in boutons.NOMS}
allumes = {}                                    


def ligne(i, nom, c):
    texte = "{:<6} GP{:<2} {:>3}".format(ETIQUETTES[nom], boutons.pins()[i], comptes[nom])
    ecran.texte(texte, 0, 40 + i * 30, c, taille=2)


boutons.init()
for i, nom in enumerate(boutons.NOMS):
    ligne(i, nom, BLANC)
ecran.texte("Appuie sur chaque bouton", 0, 226, GRIS, taille=1)
print("Appuie sur les boutons pendant {} s (Ctrl+C pour sortir).".format(DUREE_S))

fin = time.ticks_add(time.ticks_ms(), DUREE_S * 1000)
while time.ticks_diff(fin, time.ticks_ms()) > 0:
    maintenant = time.ticks_ms()
    for nom in boutons.scruter(maintenant):
        comptes[nom] += 1
        print("bouton", nom, "->", comptes[nom])
        ligne(boutons.NOMS.index(nom), nom, VERT)
        allumes[nom] = maintenant
    for nom in list(allumes):
        if time.ticks_diff(maintenant, allumes[nom]) > 300:
            del allumes[nom]
            ligne(boutons.NOMS.index(nom), nom, BLANC)
    time.sleep_ms(boutons.PERIODE_MS)

ecran.texte("Fin du test", 0, 226, BLANC, taille=1)
print("Fin du test :", comptes)