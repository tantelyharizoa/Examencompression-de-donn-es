# Mini-compresseur (LZ77 + Huffman)

Outil de compression/décompression en ligne de commande, écrit en Python pur
(aucune dépendance externe). Il combine deux techniques classiques du cours :

1. **LZ77** (`lz77.py`) : élimine les répétitions en remplaçant les séquences
   déjà vues par des références `(offset, longueur, littéral)`.
2. **Huffman** (`huffman.py`) : réduit le nombre de bits utilisés en donnant
   des codes courts aux octets fréquents et des codes longs aux octets rares.

C'est le même principe que **DEFLATE**, l'algorithme au cœur de ZIP, gzip,
et utilisé aussi (avec d'autres) dans 7zip.

## Utilisation

```bash
# Compresser
python3 main.py compress mon_fichier.txt mon_fichier.mhz

# Décompresser
python3 main.py decompress mon_fichier.mhz mon_fichier_restaure.txt
```

Fonctionne avec **n'importe quel type de fichier** (texte, image, binaire...)
car tout est traité comme une suite d'octets bruts.

## Format du fichier compressé (.mhz)

```
[4 octets]   signature "MHZ1"
[8 octets]   taille du fichier original
[8 octets]   taille du flux de tokens LZ77 (avant Huffman)
[1 octet]    nombre de bits de bourrage (padding) du dernier octet
[1024 octets] table des fréquences (256 valeurs x 4 octets), pour
              reconstruire l'arbre de Huffman au décodage
[le reste]   données compressées (flux binaire Huffman empaqueté en octets)
```

## Résultats observés

| Type de fichier                          | Résultat                          |
|-------------------------------------------|------------------------------------|
| Texte répétitif (2740 octets)             | ~1128 octets → **-58 %**          |
| Données aléatoires (500 octets)           | augmente (aucune redondance à exploiter) |
| Petit fichier (< 1 Ko)                    | peut augmenter (l'en-tête de 1045 octets, dont la table de fréquences, coûte plus cher que ce qu'il économise) |

C'est un résultat attendu et important à mentionner dans un rapport : **on ne
peut pas compresser des données sans structure/redondance** (c'est une
conséquence de la théorie de l'information de Shannon), et un format de
compression a toujours un coût fixe (en-tête) qui n'est rentable que sur des
fichiers assez gros.

## Limites (axes d'amélioration possibles pour le rapport)

- La recherche de correspondances LZ77 est en force brute (O(n × fenêtre)) :
  une table de hachage rendrait la compression beaucoup plus rapide sur de
  gros fichiers.
- La table de fréquences Huffman est stockée en clair (1024 octets fixes) :
  on pourrait la sérialiser plus intelligemment (arbre canonique) pour réduire
  l'en-tête.
- Fenêtre glissante fixée à 4096 octets et correspondances limitées à 255
  octets : ce sont des paramètres classiques mais ajustables.

## Fichiers

- `lz77.py` — compression/décompression LZ77
- `huffman.py` — compression/décompression Huffman
- `main.py` — programme principal (CLI), assemble les deux étapes
