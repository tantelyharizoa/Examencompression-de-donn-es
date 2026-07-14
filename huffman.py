"""
huffman.py — Implémentation du codage de Huffman
===================================================

Principe :
Les octets qui apparaissent souvent dans les données sont codés avec très
peu de bits, et les octets rares avec plus de bits. On construit pour cela
un arbre binaire (arbre de Huffman) à partir des fréquences d'apparition de
chaque octet :

    1. Chaque octet devient une feuille, avec un "poids" = sa fréquence
    2. On fusionne à chaque étape les deux nœuds de plus faible poids
       en un nouveau nœud (poids = somme des deux)
    3. On répète jusqu'à ce qu'il ne reste qu'un seul nœud (la racine)

Le chemin de la racine jusqu'à une feuille (0 = gauche, 1 = droite) donne
le code binaire de l'octet correspondant. Les octets fréquents, proches de
la racine, ont donc un code court.
"""

import heapq


class Noeud:
    __slots__ = ("freq", "octet", "gauche", "droite")

    def __init__(self, freq, octet=None, gauche=None, droite=None):
        self.freq = freq
        self.octet = octet
        self.gauche = gauche
        self.droite = droite

    def __lt__(self, autre):
        # nécessaire pour que heapq puisse comparer les nœuds
        return self.freq < autre.freq


def _construire_arbre(freqs):
    """
    Construit l'arbre de Huffman à partir d'un tableau de 256 fréquences
    (une par valeur d'octet possible, 0 si l'octet n'apparaît pas).
    """
    tas = [Noeud(f, octet) for octet, f in enumerate(freqs) if f > 0]

    if len(tas) == 0:
        # cas limite : fichier vide
        return Noeud(0, 0)

    if len(tas) == 1:
        # cas limite : un seul octet distinct dans tout le fichier
        seul = tas[0]
        autre_octet = (seul.octet + 1) % 256
        tas.append(Noeud(0, autre_octet))

    heapq.heapify(tas)
    while len(tas) > 1:
        a = heapq.heappop(tas)
        b = heapq.heappop(tas)
        heapq.heappush(tas, Noeud(a.freq + b.freq, None, a, b))

    return tas[0]


def _generer_codes(noeud, prefixe="", codes=None):
    """
    Parcourt l'arbre pour associer à chaque octet son code binaire (str de '0'/'1').
    """
    if codes is None:
        codes = {}
    if noeud.octet is not None:
        codes[noeud.octet] = prefixe or "0"
        return codes
    _generer_codes(noeud.gauche, prefixe + "0", codes)
    _generer_codes(noeud.droite, prefixe + "1", codes)
    return codes


def encode(data: bytes):
    """
    Encode les données avec Huffman.

    Retourne (octets_encodes, freqs, padding, longueur_originale)
        - octets_encodes : le flux binaire compressé, empaqueté en octets
        - freqs          : tableau des 256 fréquences (nécessaire pour reconstruire
                            le même arbre au décodage)
        - padding        : nombre de bits de bourrage ajoutés à la fin
        - longueur_originale : nombre d'octets avant compression
    """
    freqs = [0] * 256
    for octet in data:
        freqs[octet] += 1

    arbre = _construire_arbre(freqs)
    codes = _generer_codes(arbre)

    bits = "".join(codes[octet] for octet in data)

    padding = (8 - len(bits) % 8) % 8
    bits += "0" * padding

    out = bytearray()
    for i in range(0, len(bits), 8):
        out.append(int(bits[i:i + 8], 2))

    return bytes(out), freqs, padding, len(data)


def decode(encoded: bytes, freqs, padding: int, longueur_originale: int):
    """
    Décode un flux Huffman. Reconstruit le même arbre à partir de `freqs`.
    """
    arbre = _construire_arbre(freqs)

    if longueur_originale == 0:
        return b""

    bits = "".join(f"{octet:08b}" for octet in encoded)
    if padding:
        bits = bits[:-padding]

    resultat = bytearray()
    noeud = arbre
    for bit in bits:
        noeud = noeud.gauche if bit == "0" else noeud.droite
        if noeud.octet is not None:
            resultat.append(noeud.octet)
            noeud = arbre
            if len(resultat) == longueur_originale:
                break

    return bytes(resultat)
