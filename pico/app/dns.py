# US personnelle (Thomas) – nom d'adresse pour la machine.
#  - Client Wi-Fi : reseau.py donne le nom "cocktail" à la machine -> http://cocktail.local (mDNS).
#  - Point d'accès : ce mini serveur DNS répond l'adresse de la machine à N'IMPORTE QUEL nom
#    (cocktail.local, cocktail.box, ...) : le téléphone connecté tombe toujours sur la machine.
import asyncio
import socket

from app import config


def reponse(demande, ip):
    """Construit la réponse DNS à une demande (octets), ou None si la demande est invalide."""
    if len(demande) < 17 or demande[2] & 0x80:       # trop court, ou ce n'est pas une question
        return None
    fin = 12
    while fin < len(demande) and demande[fin] != 0:  # fin du nom demandé
        fin += demande[fin] + 1
    fin += 5                                          # octet 0 + type (2) + classe (2)
    if fin > len(demande):
        return None
    type_ = (demande[fin - 4] << 8) | demande[fin - 3]
    question = demande[12:fin]
    if type_ == 1:                                    # type A : on répond l'adresse IPv4
        corps = b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04" + bytes(int(x) for x in ip.split("."))
        return demande[:2] + b"\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00" + question + corps
    # autre type (IPv6, ...) : réponse vide, sans erreur
    return demande[:2] + b"\x81\x80\x00\x01\x00\x00\x00\x00\x00\x00" + question


async def lancer(ip, port=53):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(False)
    s.bind(("0.0.0.0", port))
    print("DNS : tous les noms mènent à", ip)
    while True:
        try:
            demande, client = s.recvfrom(256)
        except OSError:
            await asyncio.sleep_ms(30)
            continue
        try:
            rep = reponse(demande, ip)
            if rep:
                s.sendto(rep, client)
        except Exception as e:
            print("dns :", e)
