# Test du matériel, pièce par pièce, sur la vraie Pico 2 W.
# Utilisation : ouvrir ce fichier dans Thonny (ou MicroPico) et l'exécuter ; le menu s'affiche dans la console.
# Ce fichier est autonome : il n'utilise pas le reste du projet. Arrêt à tout moment : Ctrl+C (les pompes s'éteignent).
import time
from machine import Pin

# ---------------------------------------------------------------- réglages (comme config.py)
PINS_RELAIS = (2, 3, 4, 5)        # GP2 à GP5 -> IN1 à IN4
ACTIF_BAS = True                  # True : broche à 0 V = relais collé (notre module)
PIN_RUBAN = 15                    # GP15 -> 330 ohms -> DIN
NB_LED = 26
LUMINOSITE = 0.25                 # garder bas : 26 LED à fond = plus de 1,5 A
PINS_BOUTONS = (10, 11, 12, 13)   # boutons vers la masse
PIN_SDA, PIN_SCL = 8, 9           # écran OLED I2C (pour vérifier qu'il répond)

# ---------------------------------------------------------------- relais / pompes
def _niveau(allume):
    return (0 if allume else 1) if ACTIF_BAS else (1 if allume else 0)

relais = [Pin(p, Pin.OUT, value=_niveau(False)) for p in PINS_RELAIS]   # tout éteint dès le départ


def tout_eteindre():
    for r in relais:
        r.value(_niveau(False))
    ruban_eteindre()


def attendre(secondes):
    """Pause qu'on peut interrompre avec Ctrl+C."""
    fin = time.ticks_add(time.ticks_ms(), int(secondes * 1000))
    while time.ticks_diff(fin, time.ticks_ms()) > 0:
        time.sleep_ms(20)


def demander_nombre(question, defaut, mini, maxi):
    texte = input("{} [{}] : ".format(question, defaut)).strip()
    if not texte:
        return defaut
    try:
        v = float(texte.replace(",", "."))
    except ValueError:
        print("Pas un nombre, valeur par défaut :", defaut)
        return defaut
    return min(max(v, mini), maxi)


def test_pompe(n):
    duree = demander_nombre("Durée en secondes (max 10)", 2, 0.2, 10)
    print("Pompe {} : en marche pendant {} s... (Ctrl+C pour arrêter)".format(n, duree))
    relais[n - 1].value(_niveau(True))
    try:
        attendre(duree)
    finally:
        relais[n - 1].value(_niveau(False))
    print("Pompe {} arrêtée.".format(n))
    print("Elle devait tourner ? Si rien ne s'est passé : voir « Inverser le niveau des relais » (option I).")


def test_toutes_pompes():
    print("Les 4 pompes, l'une après l'autre, 1 s chacune.")
    for n in range(1, 5):
        print(" pompe", n)
        relais[n - 1].value(_niveau(True))
        try:
            attendre(1)
        finally:
            relais[n - 1].value(_niveau(False))
        attendre(0.4)
    print("Terminé.")


def test_clic_relais():
    print("Clic des 4 relais (sans pompe branchée, on les entend). 3 allers-retours.")
    try:
        for _ in range(3):
            for r in relais:
                r.value(_niveau(True))
                attendre(0.25)
                r.value(_niveau(False))
                attendre(0.15)
    finally:
        tout_eteindre()


def inverser_niveau():
    global ACTIF_BAS
    tout_eteindre()
    ACTIF_BAS = not ACTIF_BAS
    for r in relais:
        r.value(_niveau(False))
    print("Relais maintenant :", "ACTIF BAS (0 V = collé)" if ACTIF_BAS else "ACTIF HAUT (3,3 V = collé)")
    print("Si ça marche mieux ainsi, mettez RELAIS_ACTIF_BAS = %s dans app/config.py." % ACTIF_BAS)


# ---------------------------------------------------------------- ruban de LED
_ruban = None


def _creer_ruban():
    global _ruban
    if _ruban is None:
        import neopixel
        _ruban = neopixel.NeoPixel(Pin(PIN_RUBAN), NB_LED)
    return _ruban


def _echelle(c):
    return (int(c[0] * LUMINOSITE), int(c[1] * LUMINOSITE), int(c[2] * LUMINOSITE))


def ruban_remplir(couleur):
    r = _creer_ruban()
    c = _echelle(couleur)
    for i in range(NB_LED):
        r[i] = c
    r.write()


def ruban_eteindre():
    try:
        ruban_remplir((0, 0, 0))
    except Exception:
        pass


def test_ruban_couleurs():
    print("Ruban : rouge, vert, bleu, blanc (1,5 s chacun). Si rouge/vert sont inversés, c'est un autre ordre de couleurs.")
    try:
        for nom, c in (("rouge", (255, 0, 0)), ("vert", (0, 255, 0)), ("bleu", (0, 0, 255)), ("blanc", (255, 255, 255))):
            print(" ", nom)
            ruban_remplir(c)
            attendre(1.5)
    finally:
        ruban_eteindre()


def test_ruban_chenillard():
    print("Ruban : une LED qui parcourt tout le ruban (vérifie que les 26 LED répondent).")
    r = _creer_ruban()
    try:
        for tour in range(2):
            for i in range(NB_LED):
                for j in range(NB_LED):
                    r[j] = _echelle((255, 110, 0)) if j == i else (0, 0, 0)
                r.write()
                attendre(0.05)
    finally:
        ruban_eteindre()


def test_ruban_barre():
    print("Ruban : barre de progression orange de 0 à 100 % (comme pendant une préparation).")
    r = _creer_ruban()
    try:
        for k in range(NB_LED + 1):
            for j in range(NB_LED):
                r[j] = _echelle((255, 110, 0)) if j < k else (0, 0, 0)
            r.write()
            attendre(0.15)
        attendre(0.8)
    finally:
        ruban_eteindre()


# ---------------------------------------------------------------- boutons, écran, Wi-Fi
def test_boutons():
    print("Appuyez sur les boutons GP10 à GP13 pendant 15 s (Ctrl+C pour sortir).")
    boutons = [Pin(p, Pin.IN, Pin.PULL_UP) for p in PINS_BOUTONS]
    avant = [1] * len(boutons)
    fin = time.ticks_add(time.ticks_ms(), 15000)
    while time.ticks_diff(fin, time.ticks_ms()) > 0:
        for i, b in enumerate(boutons):
            v = b.value()
            if v != avant[i]:
                print(" bouton GP{} : {}".format(PINS_BOUTONS[i], "appuyé" if v == 0 else "relâché"))
                avant[i] = v
        time.sleep_ms(10)
    print("Fin du test des boutons.")


def test_ecran():
    from machine import I2C
    i2c = I2C(0, sda=Pin(PIN_SDA), scl=Pin(PIN_SCL), freq=400000)
    trouves = i2c.scan()
    if trouves:
        print("Appareils I2C trouvés :", ["0x{:02x}".format(a) for a in trouves], "(un écran OLED est souvent en 0x3c)")
    else:
        print("Aucun appareil I2C : vérifier SDA=GP8, SCL=GP9, 3V3 et GND.")


def test_wifi():
    import network
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    print("Recherche des réseaux Wi-Fi...")
    reseaux = sta.scan()
    reseaux.sort(key=lambda r: -r[3])
    for r in reseaux[:15]:
        print("  {:<32} signal {} dBm".format(r[0].decode(), r[3]))
    if not reseaux:
        print("Aucun réseau trouvé.")


# ---------------------------------------------------------------- menu
MENU = (
    ("1", "Pompe 1", lambda: test_pompe(1)),
    ("2", "Pompe 2", lambda: test_pompe(2)),
    ("3", "Pompe 3", lambda: test_pompe(3)),
    ("4", "Pompe 4", lambda: test_pompe(4)),
    ("5", "Les 4 pompes, l'une après l'autre", test_toutes_pompes),
    ("6", "Clic des 4 relais (sans pompe)", test_clic_relais),
    ("7", "Ruban LED : couleurs", test_ruban_couleurs),
    ("8", "Ruban LED : une LED qui parcourt le ruban", test_ruban_chenillard),
    ("9", "Ruban LED : barre de progression", test_ruban_barre),
    ("B", "Boutons GP10 à GP13", test_boutons),
    ("E", "Écran OLED : est-il détecté ?", test_ecran),
    ("W", "Wi-Fi : réseaux visibles", test_wifi),
    ("I", "Inverser le niveau des relais (si les pompes ne réagissent pas comme prévu)", inverser_niveau),
    ("0", "Tout éteindre", tout_eteindre),
    ("Q", "Quitter", None),
)


def menu():
    print("\n===== Test du matériel One Cocktail =====")
    print("Relais :", "actif BAS (0 V = collé)" if ACTIF_BAS else "actif HAUT")
    for touche, texte, _ in MENU:
        print("  {} : {}".format(touche, texte))


def principal():
    try:
        while True:
            menu()
            choix = input("Votre choix : ").strip().upper()
            action = None
            for touche, _, f in MENU:
                if touche == choix:
                    if f is None:
                        return
                    action = f
            if action is None:
                print("Choix inconnu.")
                continue
            try:
                action()
            except KeyboardInterrupt:
                print("\nInterrompu.")
            except Exception as e:
                print("Erreur :", e)
            finally:
                tout_eteindre()
    finally:
        tout_eteindre()
        print("Tout est éteint. Au revoir.")


principal()
