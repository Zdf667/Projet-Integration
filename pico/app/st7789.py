import time

try:
    import framebuf
    from machine import Pin, SPI
except ImportError:         
    framebuf = None
    Pin = None
    SPI = None

LARGEUR = 240
HAUTEUR = 240


def couleur(r, g, b):
    """Couleur (r, g, b) de 0 à 255 -> entier RGB565 compris par l'écran."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


NOIR = couleur(0, 0, 0)
BLANC = couleur(255, 255, 255)
GRIS = couleur(120, 120, 120)
ROUGE = couleur(255, 0, 0)
VERT = couleur(0, 200, 0)
BLEU = couleur(0, 0, 255)
ORANGE = couleur(255, 110, 0)

_ACCENTS = {}
for _lettre, _variantes in (("a", "àâä"), ("A", "ÀÂÄ"), ("e", "éèêë"), ("E", "ÉÈÊË"), ("i", "îï"), ("I", "ÎÏ"),
                            ("o", "ôö"), ("O", "ÔÖ"), ("u", "ùûü"), ("U", "ÙÛÜ"), ("c", "ç"), ("C", "Ç")):
    for _v in _variantes:
        _ACCENTS[_v] = _lettre
_ACCENTS.update({"«": '"', "»": '"', "’": "'", "–": "-", "…": "...", "œ": "oe", "\u00a0": " "})


def sans_accents(texte):
    """'Glaçons à côté' -> 'Glacons a cote' ; tout autre caractère non affichable devient '?'."""
    return "".join(_ACCENTS.get(c, c if " " <= c <= "~" else "?") for c in str(texte))


class ST7789:
    def __init__(self, spi, dc, rst, cs=None, bl=None, inverser=True, bgr=False):
        
        self.spi = spi
        self.dc = Pin(dc, Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=1)
        self.cs = Pin(cs, Pin.OUT, value=1) if cs is not None else None
        self.bl = Pin(bl, Pin.OUT, value=0) if bl is not None else None
        self._demarrer(inverser, bgr)

    def _commande(self, code, donnees=None):
        if self.cs is not None:
            self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes((code,)))
        if donnees:
            self.dc.value(1)
            self.spi.write(donnees)
        if self.cs is not None:
            self.cs.value(1)

    def _debut_donnees(self):
        if self.cs is not None:
            self.cs.value(0)
        self.dc.value(1)

    def _fin_donnees(self):
        if self.cs is not None:
            self.cs.value(1)

    def _fenetre(self, x0, y0, x1, y1):
        """Zone de l'écran où iront les prochains pixels (bornes incluses)."""
        self._commande(0x2A, bytes((x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF)))   
        self._commande(0x2B, bytes((y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF)))   
        self._commande(0x2C)                                                     

    def _demarrer(self, inverser, bgr):
        self.rst.value(1)
        time.sleep_ms(10)
        self.rst.value(0)             
        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(150)
        self._commande(0x01)           
        time.sleep_ms(150)
        self._commande(0x11)           
        time.sleep_ms(120)
        self._commande(0x3A, b"\x55")  
        time.sleep_ms(10)
        self._commande(0x36, bytes((0x08 if bgr else 0x00,)))   
        self._commande(0x21 if inverser else 0x20)              
        self._commande(0x13)           
        time.sleep_ms(10)
        self.effacer(NOIR)           
        self._commande(0x29)        
        time.sleep_ms(100)
        self.allumer(True)


    def allumer(self, oui=True):
        """Rétroéclairage (si la broche BLK est branchée)."""
        if self.bl is not None:
            self.bl.value(1 if oui else 0)

    def rect(self, x, y, largeur, hauteur, c):
        """Rectangle plein ; ce qui dépasse de l'écran est coupé."""
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(LARGEUR, x + largeur), min(HAUTEUR, y + hauteur)
        if x1 <= x0 or y1 <= y0:
            return
        largeur, hauteur = x1 - x0, y1 - y0
        self._fenetre(x0, y0, x1 - 1, y1 - 1)
        lignes = min(hauteur, max(1, 4096 // (2 * largeur)))   
        bloc = bytes((c >> 8, c & 0xFF)) * (largeur * lignes)
        self._debut_donnees()
        reste = hauteur
        while reste >= lignes:
            self.spi.write(bloc)
            reste -= lignes
        if reste:
            self.spi.write(memoryview(bloc)[:2 * largeur * reste])
        self._fin_donnees()

    def effacer(self, c=NOIR):
        self.rect(0, 0, LARGEUR, HAUTEUR, c)

    def texte(self, txt, x, y, c=BLANC, fond=NOIR, taille=2):
        """Une ligne de texte (8 x 8 pixels par lettre, multiplié par `taille`).

        Ce qui dépasse à droite est coupé. Renvoie la largeur dessinée, en pixels.
        Taille 1 : 30 lettres par ligne ; taille 2 : 15 lettres ; taille 3 : 10 lettres.
        """
        txt = sans_accents(txt)
        place = (LARGEUR - x) // (8 * taille)
        if x < 0 or y < 0 or y + 8 * taille > HAUTEUR or place <= 0:
            return 0
        txt = txt[:place]
        if not txt:
            return 0
        larg = 8 * len(txt)
        source = bytearray(larg)                     
        fb = framebuf.FrameBuffer(source, larg, 8, framebuf.MONO_HLSB)
        fb.text(txt, 0, 0, 1)
        plein = bytes((c >> 8, c & 0xFF)) * taille
        vide = bytes((fond >> 8, fond & 0xFF)) * taille
        pas = 2 * taille
        ligne = bytearray(larg * pas)
        self._fenetre(x, y, x + larg * taille - 1, y + 8 * taille - 1)
        self._debut_donnees()
        for j in range(8):
            k = 0
            for i in range(larg):
                ligne[k:k + pas] = plein if fb.pixel(i, j) else vide
                k += pas
            for _ in range(taille):                  
                self.spi.write(ligne)
        self._fin_donnees()
        return larg * taille


def creer(sck=18, mosi=19, dc=16, cs=17, rst=20, bl=21, vitesse=24000000, spi_id=0, inverser=True, bgr=False):
    """Crée l'écran avec les broches du câblage US4.5 (SPI0). Mettre cs=None si le module n'a pas de broche CS."""
    spi = SPI(spi_id, baudrate=vitesse, polarity=1, phase=1, sck=Pin(sck), mosi=Pin(mosi))
    return ST7789(spi, dc=dc, rst=rst, cs=cs, bl=bl, inverser=inverser, bgr=bgr)