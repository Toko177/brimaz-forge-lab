# Protocole V4 contre V5 — 96 parties Forge à quatre joueurs

**13 octobre 2026.** Expérience à lancer par un **push** sur `decks/Challenger.txt`. Le commit doit contenir `Challenger.txt` **strictement identique** à `decks/Brimaz_V5_Tempo_Trial.txt`.

## Pourquoi ce test ?

L'utilisateur veut **faire avancer la decklist avec de vraies preuves**, pas de nouvelles substitutions arbitraires. La campagne précédente V3/V4 a lancé 16 parties, certifié 13 fins naturelles et rapporté **0 victoire Brimaz dans chaque bras**, sans différence concluante. Le but ici est de comparer directement **V4 à V5** après deux changements précis :

- `Throne of Geth -> Vault Skirge`
- `Myr Sire -> Changeling Outcast`

Ces changements permettent deux créatures Phyrexian/artefact-créatures lançables avec **1 mana de reste après Brimaz**, mais retirent de la prolifération et une production de corps de remplacement. Aucun gain de taux de victoire n'est présumé.

## Configuration préenregistrée avant les résultats

| Paramètre | Valeur |
|---|---|
| Moteur | Stock Forge 2.0.15 + mêmes patchs de règles + IA V13 sur les quatre sièges |
| Référence | **V4** `decks/Brimaz_V4_B3.txt` |
| Candidat | **V5** `decks/Challenger.txt` (copie de `Brimaz_V5_Tempo_Trial.txt`) |
| Pods | `aristo` et `artifact`, trois adversaires réels du groupe enregistrés par SHA |
| Rotations | 4 positions pour le deck évalué par pod |
| Répétitions | **6** graines distinctes par pod/rotation/bras |
| Total prévu | **2 pods × 4 rotations × 6 répétitions × 2 bras = 96 parties** |
| V4 | 48 parties prévues |
| V5 | 48 parties prévues |
| Graines | base `21620000` et `+100000` pour `artifact`, puis `+10000×rotation + repetition` |
| CPU/game | 1 JVM indépendante, `--clock 360`, `--timeout 445`; 16 shards parallèles |
| Rapport | `deckbuild_certify.py` et `deckbuild_compare.py`, artefact `commander-deckbuild-certified-comparison` |

Le workflow est conditionnel au type d'événement : les **pushes Challenger** imposent cette comparaison de 96 parties, tandis que le déclenchement **manuel** préserve les anciennes valeurs par défaut `V3` et `repeats=1`.

## Critères de validité AVANT d'observer les résultats

1. Manifeste exact : **100 cartes**, identité WB, sans Game Changer, listes V4 et V5 cohérentes avec les deux seuls swaps.
2. Certificat individuel de **fin naturelle** : une partie interrompue artificiellement à 360 secondes, un `OutOfMemoryError` ou une absence de traces de quatre joueurs = **exclue**, jamais « défaite » attribuée.
3. Si les deux bras ont suffisamment de fins naturelles et de victoires, comparer le taux de victoire sur le même pod et la même rotation, avec **Wilson 95%** et comptage des **paires comparables**.
4. Si trop de parties sont censurées, ou si les deux bras enregistrent très peu de victoires, **ne pas prétendre avoir démontré un gain**. Lire dans les vrais journaux : apparition de Brimaz au tour 4, nombre de relances, Incubations déclenchées, transformations, dégâts de combat, activations des cartes échangées.
5. **L'IA V13 n'est pas un joueur humain expert**. Un résultat Forge mesure la confrontation de ces politiques de jeu et de ces trois adversaires dans ce moteur ; il ne démontre pas la capacité réelle de l'utilisateur contre KaalDeagle.

## Critère de décision de deckbuilding

- La V5 n'est **pas adoptée automatiquement** si ses options à un mana sont plus nombreuses : c'est déjà démontré par le test combinatoire et cela ne prouve pas une meilleure partie.
- Favoriser la V5 **seulement si** les matchs montrent un gain cohérent de victoire ou, si les winrates restent inutilisables, un gain concret de tours utiles / dégâts de combat dans des situations comparables, tout en documentant les sacrifices de Throne/Myr Sire.
- Garder la V4 inchangée jusqu'au verdict ; tout remplacement ultérieur sera motivé par une **trace ou un test strict**, pas l'intuition du deckbuilder.
