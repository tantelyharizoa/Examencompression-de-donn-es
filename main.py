"""
main.py — Outil de compression en ligne de commande (façon 7zip)
====================================================================

Pipeline de compression :   fichier -> LZ77 -> Huffman -> fichier .mhz
Pipeline de décompression : fichier .mhz -> Huffman -> LZ77 -> fichier original

Utilisation :
    python main.py compress   <fichier_entree> <fichier_sortie.mhz>
    python main.py decompress <fichier_entree.mhz> <fichier_sortie>

Exemple :
    python main.py compress rapport.txt rapport.mhz
    python main.py decompress rapport.mhz rapport_restaure.txt
"""

import argparse
import os
import sys

import lz77
import huffman

MAGIC = b"MHZ1"  # signature du format de fichier


def compress_file(chemin_entree: str, chemin_sortie: str):
    with open(chemin_entree, "rb") as f:
        data = f.read()

    # Étape 1 : LZ77 (élimine les répétitions)
    tokens = lz77.compress(data)
    tokens_bytes = lz77.tokens_to_bytes(tokens)

    # Étape 2 : Huffman (réduit le nombre de bits selon la fréquence)
    encoded, freqs, padding, longueur_tokens = huffman.encode(tokens_bytes)

    with open(chemin_sortie, "wb") as f:
        f.write(MAGIC)
        f.write(len(data).to_bytes(8, "big"))          # taille du fichier original
        f.write(longueur_tokens.to_bytes(8, "big"))     # taille du flux de tokens LZ77
        f.write(bytes([padding]))                       # bits de bourrage Huffman
        for freq in freqs:                               # table des fréquences (256 x 4 octets)
            f.write(freq.to_bytes(4, "big"))
        f.write(encoded)

    taille_orig = len(data)
    taille_comp = os.path.getsize(chemin_sortie)
    taux = (taille_comp / taille_orig * 100) if taille_orig else 0.0

    print(f"Fichier compressé : {chemin_sortie}")
    print(f"Taille originale   : {taille_orig:,} octets")
    print(f"Taille compressée  : {taille_comp:,} octets")
    print(f"Taux de compression: {taux:.2f}% de la taille originale (gain de {100 - taux:.2f}%)")


def decompress_file(chemin_entree: str, chemin_sortie: str):
    with open(chemin_entree, "rb") as f:
        contenu = f.read()

    if contenu[:4] != MAGIC:
        raise ValueError("Format de fichier non reconnu (ce n'est pas un fichier .mhz valide).")

    idx = 4
    taille_orig = int.from_bytes(contenu[idx:idx + 8], "big"); idx += 8
    longueur_tokens = int.from_bytes(contenu[idx:idx + 8], "big"); idx += 8
    padding = contenu[idx]; idx += 1

    freqs = []
    for _ in range(256):
        freqs.append(int.from_bytes(contenu[idx:idx + 4], "big"))
        idx += 4

    encoded = contenu[idx:]

    # Étape 1 : décodage Huffman -> on retrouve le flux de tokens LZ77
    tokens_bytes = huffman.decode(encoded, freqs, padding, longueur_tokens)

    # Étape 2 : décodage LZ77 -> on retrouve les données originales
    tokens = lz77.bytes_to_tokens(tokens_bytes)
    data = lz77.decompress(tokens)

    with open(chemin_sortie, "wb") as f:
        f.write(data)

    ok = "OK" if len(data) == taille_orig else "ATTENTION : taille différente de l'originale !"
    print(f"Fichier décompressé : {chemin_sortie} ({len(data):,} octets) [{ok}]")


def main():
    parser = argparse.ArgumentParser(
        description="Mini outil de compression (LZ77 + Huffman), façon 7zip."
    )
    sous = parser.add_subparsers(dest="commande", required=True)

    p_comp = sous.add_parser("compress", help="Compresser un fichier")
    p_comp.add_argument("entree", help="Fichier à compresser")
    p_comp.add_argument("sortie", help="Fichier compressé de sortie (ex: fichier.mhz)")

    p_decomp = sous.add_parser("decompress", help="Décompresser un fichier")
    p_decomp.add_argument("entree", help="Fichier compressé (.mhz) à décompresser")
    p_decomp.add_argument("sortie", help="Fichier restauré de sortie")

    args = parser.parse_args()

    try:
        if args.commande == "compress":
            compress_file(args.entree, args.sortie)
        elif args.commande == "decompress":
            decompress_file(args.entree, args.sortie)
    except FileNotFoundError:
        print(f"Erreur : fichier introuvable.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
