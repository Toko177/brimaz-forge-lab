# Brimaz V3 vs V4 — 16 vraies parties Forge (13 octobre 2026)

**[GitHub Actions run #38370552595](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38370552595)**, **[rapport certifié et données originales](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38370552595/artifacts/11799725119)**.

## Protocole et sources

- V3 : `decks/Brimaz_V3.txt` (témoin immuable).
- V4 : `decks/Challenger.txt`, copie stricte des 100 cartes de `decks/Brimaz_V4_B3.txt` au début du test.
- Moteur **réel Forge 2.0.15**, même patch de règles et **IA V13-incubate-adaptive** sur chaque siège dans les deux bras.
- Deux groupes d'adversaires du playgroup : `aristo` et `artifact`, trois IA adverses dans chaque partie ; les quatre places tournent, avec graines préalablement choisies.
- 8 parties prévues par liste, 16 au total. Les logs complets, les empreintes SHA256 des decks, `certificate.json`, `comparison.json` et `preflight.json` sont archivés dans les artefacts du run.
- **Pas de combat entre humains**, pas d'imposition expérimentale d'une destruction de Brimaz au T4, et pas de garantie que l'IA choisit la meilleure ligne de jeu.

## Résultats réellement certifiés

| Mesure | V3 | V4 |
|---|---:|---:|
| Parties démarrées | 8 | 8 |
| Fins naturelles certifiées | **7** | **6** |
| Victoires certifiées | **0** | **0** |
| Winrate conditionné aux parties certifiées | 0/7 | 0/6 |
| Borne supérieure Wilson 95 % | 35,43 % | 39,03 % |
| Exclusions | 1 | 2 |

**Conclusion : aucune amélioration du taux de victoire de V4 n'est démontrée.**
Les bornes d'incertitude sont énormes, donc **ce n'est pas une estimation valable d'un winrate humain de 0 %**.

Les **3 exclusions sont motivées et vérifiées sur les logs**, et **ne deviennent jamais des défaites ou victoires inventées** :

1. V3 / artifact / rotation 3 : fin proche de **360,18 s**, simulée au cutoff et non une victoire naturelle certifiable.
2. V4 / artifact / rotation 0 : Forge affiche `Deck_Candidate has won` à **360,15 s** ; partie **exclue comme victoire** parce que son résultat coïncide avec la limite artificielle.
3. V4 / aristo / rotation 3 : `OutOfMemoryError` du moteur. Aucune issue attribuée.

Parmi les parties certifiées, les gagnants ont été :
- V3 : Dungeon Party Time ×3, Zimone/Dina ×1, Lathril ×3 ;
- V4 : Dungeon Party Time ×3, Zimone/Dina ×1, Radha ×1, Lathril ×1.
Ces répartitions sont descriptives, sans classement de puissance.

## Vérification des traces de Brimaz, des Incubateurs et des transformations

Comptage direct des événements des **13 logs de parties certifiées uniquement** :

| Événement observé | V3 (7 parties) | V4 (6 parties) |
|---|---:|---:|
| Brimaz lancé (événements `Add To Stack: cast Brimaz`) | 15 | 9 |
| Capacités de Brimaz d'Incubation résolues | 12 | 13 |
| Activations de jeton Incubateur par le joueur Brimaz | 12 | 16 |
| Parties avec Brimaz lancé, mais **aucune** Incubation résolue grâce à sa capacité | **4/7** | **2/6** |

Attention : plus de déclenchements **au total** dans 6 parties V4 que 7 parties V3 ne prouve **pas** que les mains, mana, séquences ou dégâts de la V4 sont meilleurs. Les durées, situations et décisions de l'IA divergent.

**Observation concrète :** V4/aristo/rotation 0, Brimaz arrive au quatrième tour personnel. Aux fenêtres de décision des tours 4–7, `candidatePhyrexianTokens=0`. Deux sont visibles au tour 8, puis trois. Partie gagnée par Dungeon Party Time. Les fenêtres sont des instantanés, pas la liste exhaustive de chaque arrivée/mort entre elles.

## Pré-test de courbe, hors gameplay

| Aspect | V3 | V4 |
|---|---:|---:|
| Terrains sur la face avant | 35 | 35 |
| MDFC terrains supplémentaires | 3 | 3 |
| MV moyenne des sorts hors terrains de face avant | 2,892 | 2,785 |
| Options d'Incubation *potentiellement* utilisables sans le commandant (étiquettes manuelles) | 4 | 7 |
| Protections installables avant Brimaz | 0 | 2 |
| Sorts susceptibles de déclencher Brimaz à leur lancement | 26 | 26 |

En simple tirage hypergéométrique de 13 cartes, voir au moins une option classée « Incubation indépendante » : V3 **43,2 %** ; V4 **63,5 %**. Il s'agit uniquement de cartes **vues**, non jouées ; certaines nécessitent un coût de mana élevé ou une condition.

## Diagnostic et prochaines hypothèses à isoler

- **Dépendance au commandant confirmée comme risque à explorer** : en plusieurs parties, l'IA a lancé Brimaz, parfois plusieurs fois, sans jamais résoudre un déclenchement Incubation de sa capacité. La question ne se résout pas seulement par `Command Beacon` et `Lightning Greaves` ; il faut **du contenu utile avant Brimaz et des casts déclencheurs après**.
- **Attention au moteur IA** : la certification signale des délais d'évaluation et des replis d'attaque, particulièrement côté V4. Ce n'est **pas un modèle de l'expertise de KaalDeagle humain**.
- **Pas de nouvelle coupe automatique** : une campagne aussi courte avec zéro victoire dans les deux bras ne justifie pas de remplacer encore des cartes.
- Pour isoler la plainte, un vrai test ciblé doit forcer un `destroy/exile commander` avant la première valeur de Brimaz, avec contrôle des ressources, du comportement IA et de l'évolution du board après sa première relance. **Ce scénario n'a pas été exécuté par ce run**.
- L'extension de l'échantillon doit conserver deux listes SHA-pinnées, les mêmes adversaires/policies/rotations, et compter **seulement** les victoires naturelles, jamais les cutoffs.

**Statut : première vraie campagne Forge terminée et certifiée, sans preuve de V4 > V3.**
