import time

from app import st7789
from app.st7789 import BLANC, BLEU, GRIS, NOIR, ORANGE, ROUGE, VERT

INVERSER = True       
BGR = False           
VITESSE = 24000000     
CS = 17                

ecran = st7789.creer(sck=18, mosi=19, dc=16, cs=CS, rst=20, bl=21, vitesse=VITESSE, inverser=INVERSER, bgr=BGR)
print("Écran initialisé.")

for nom, c in (("ROUGE", ROUGE), ("VERT", VERT), ("BLEU", BLEU)):
    print("Écran entièrement", nom)
    ecran.effacer(c)
    time.sleep(1)

debut = time.ticks_ms()
ecran.effacer(NOIR)
print("Effacement complet en", time.ticks_diff(time.ticks_ms(), debut), "ms")

ecran.rect(0, 0, 240, 1, BLANC)
ecran.rect(0, 239, 240, 1, BLANC)
ecran.rect(0, 0, 1, 240, BLANC)
ecran.rect(239, 0, 1, 240, BLANC)

ecran.rect(1, 1, 238, 36, ORANGE)
ecran.texte("Cocktail", 12, 11, NOIR, ORANGE, taille=2)
ecran.texte("Ecran OK", 12, 50, BLANC, taille=3)
debut = time.ticks_ms()
ecran.texte("Glaçons, citron", 4, 90, VERT, taille=2)
print("Une ligne de texte (taille 2) en", time.ticks_diff(time.ticks_ms(), debut), "ms")
ecran.texte("Cette ligne est trop longue pour l'ecran", 4, 116, GRIS, taille=2)
ecran.texte("Taille 1 : 29 lettres/ligne", 4, 140, GRIS, taille=1)
ecran.rect(4, 160, 76, 30, ROUGE)
ecran.rect(82, 160, 76, 30, VERT)
ecran.rect(160, 160, 76, 30, BLEU)
ecran.texte("ROUGE VERT  BLEU", 4, 200, BLANC, taille=2)

print("Regarde l'écran. Dans 5 s : rétroéclairage éteint 1 s puis rallumé.")
time.sleep(5)
ecran.allumer(False)
time.sleep(1)
ecran.allumer(True)
print("Fin du test.")