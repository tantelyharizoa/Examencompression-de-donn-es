"""
lz77.py — Implémentation de l'algorithme LZ77
================================================

Principe :
Au lieu d'encoder les données octet par octet, on cherche si la séquence
qu'on est en train de lire est déjà apparue récemment (dans une "fenêtre
glissante" des N derniers octets). Si oui, on remplace la séquence répétée
par un simple triplet (offset, longueur, littéral) :

    - offset   : à combien d'octets en arrière commence la répétition
    - longueur : combien d'octets sont recopiés
    - littéral : l'octet qui suit la répétition (non compressé)

Exemple : "ABABABC"
    A B A B A B C
    -> (0,0,'A')      on lit A, rien avant, littéral
    -> (0,0,'B')      on lit B, rien avant, littéral
    -> (2,3,'C')      "ABA" est déjà apparu 2 positions en arrière (longueur 3),
                       suivi du littéral 'C'

C'est cette redondance qui permet de gagner de la place : au lieu de stocker
7 octets, on en stocke 3 tokens de taille fixe (qui seront ensuite encore
réduits par le codage de Huffman).
"""

# Taille de la fenêtre glissante (zone où l'on cherche des répétitions)
WINDOW_SIZE = 4096

# Longueur maximale d'une correspondance (doit tenir sur 1 octet -> 0-255)
LOOKAHEAD_SIZE = 255

# Longueur minimale pour qu'une correspondance soit intéressante
# (en dessous, le triplet coderait plus de place que ce qu'il économise)
MIN_MATCH = 3


def _trouve_meilleure_correspondance(data, i, n):
    """
    Cherche, en partant de la position i, la plus longue correspondance
    possible avec une séquence déjà vue dans la fenêtre glissante.

    Retourne (offset, longueur). (0, 0) si aucune correspondance utile.
    """
    max_len = min(LOOKAHEAD_SIZE, n - i - 1)
    if max_len < MIN_MATCH:
        return 0, 0

    debut_fenetre = max(0, i - WINDOW_SIZE)
    meilleure_longueur = 0
    meilleur_offset = 0

    for j in range(debut_fenetre, i):
        longueur = 0
        # on compare tant que ça correspond (on peut dépasser i car les
        # répétitions peuvent chevaucher la position courante)
        while longueur < max_len and data[j + longueur] == data[i + longueur]:
            longueur += 1
        if longueur > meilleure_longueur:
            meilleure_longueur = longueur
            meilleur_offset = i - j

    if meilleure_longueur >= MIN_MATCH:
        return meilleur_offset, meilleure_longueur
    return 0, 0


def compress(data: bytes):
    """
    Transforme une suite d'octets en une liste de tokens (offset, longueur, littéral).
    """
    n = len(data)
    i = 0
    tokens = []

    while i < n:
        if n - i <= 1:
            # plus assez de place pour chercher un match ET garder un littéral
            tokens.append((0, 0, data[i]))
            i += 1
            continue

        offset, longueur = _trouve_meilleure_correspondance(data, i, n)

        if longueur >= MIN_MATCH:
            litteral = data[i + longueur]
            tokens.append((offset, longueur, litteral))
            i += longueur + 1
        else:
            tokens.append((0, 0, data[i]))
            i += 1

    return tokens


def decompress(tokens):
    """
    Reconstruit les octets originaux à partir de la liste de tokens.
    """
    data = bytearray()
    for offset, longueur, litteral in tokens:
        if longueur > 0:
            start = len(data) - offset
            for k in range(longueur):
                data.append(data[start + k])
        data.append(litteral)
    return bytes(data)


def tokens_to_bytes(tokens):
    """
    Sérialise les tokens en une suite d'octets bruts, format fixe 4 octets/token :
        [offset: 2 octets][longueur: 1 octet][littéral: 1 octet]
    """
    out = bytearray()
    for offset, longueur, litteral in tokens:
        out += offset.to_bytes(2, "big")
        out.append(longueur)
        out.append(litteral)
    return bytes(out)


def bytes_to_tokens(b: bytes):
    """
    Opération inverse de tokens_to_bytes.
    """
    tokens = []
    for i in range(0, len(b), 4):
        offset = int.from_bytes(b[i:i + 2], "big")
        longueur = b[i + 2]
        litteral = b[i + 3]
        tokens.append((offset, longueur, litteral))
    return tokens
