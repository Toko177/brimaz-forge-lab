# Diagnostic CPU du moteur de décision Commander (Forge 2.0.15)

## Problème mesuré

La campagne V12 antérieure, fondée sur **32 véritables parties
EDH à quatre IA**, a détecté **33 dépassements du délai de décision**.
Parmi les échantillons de pile capturés **au moment précis du timeout**,
32/33 ont été classés liés aux prédictions de combats / bloqueurs
et un au recalcul de cartes/effets.

Analyse de \`v12_32_certified_corrected.zip\` :
- 20 échantillons contenaient
  \`CardState.getReplacementEffects\` ;
- 10 \`AiBlockController.assignBlockers\` ;
- 9 \`CardState.getStaticAbilities\`,
  \`Card.getStaticAbilities\`,
  \`ReplacementHandler.getReplacementList\` ;
- beaucoup d'échantillons comportaient plusieurs méthodes
  de cette liste, **les nombres ne sont pas additifs**.

Ces instantanés **ne donnent pas la répartition de la
consommation CPU de toutes les décisions** : ils sélectionnent
précisément les situations anormalement lentes.
Attribuer toute la lenteur à une carte ou à une méthode
à partir du dernier élément de la pile serait imprudent.

## JDK Flight Recorder (JFR), séparé des résultats de parties

Le laboratoire dispose désormais de
\`scripts/combat_jfr_probe.py\` et des
\`tests/test_combat_jfr_probe.py\` (5 tests) :

- démarre une vraie JVM Forge avec
  \`-XX:StartFlightRecording\` en profilage CPU
  (limite d'archive 48 Mo par partie) ;
- conserve les vrais logs Forge et l'enregistrement \`.jfr\` ;
- \`jfr print --json --events jdk.ExecutionSample\`
  attribue les échantillons où figurent des classes
  \`forge.ai.*\` aux prédictions d'attaques,
  décisions de bloqueurs, calculs de dégâts,
  recherche de mana ou autres décisions ;
- publie \`cpu-profile.json\` avec fréquences CPU
  et classes/méthodes récurrentes.

Le pilote GitHub
[\`commander-combat-jfr-profile.yml\`](../.github/workflows/commander-combat-jfr-profile.yml)
utilise deux adversaires \`aristo\`/\`artifact\` à
quatre joueurs, avec l'IA V13 commune, la
version Forge originale et le correctif Charm.
Il **n'injecte aucun raccourci dans la logique
de Magic ni aucune heuristique gagnante**.

### Comment interpréter le résultat

JFR est un **outil d'échantillonnage**, ce n'est
pas un contrôle exhaustif de légalité, ni une
preuve de supériorité de l'IA. Son overhead
peut affecter les durées : ne pas mélanger
les parties profilées aux tournois de winrate
ou à la réutilisation des résultats.

Une optimisation du moteur ne sera acceptée
qu'avec :
1. méthode coûteuse identifiée dans de
   nombreux échantillons CPU ;
2. garantie de ne pas changer les règles Magic ;
3. tests tactiques sur chaque joueur et situations
   de combat représentatives ;
4. vrais matchs à quatre IA, certificats
   indépendants et mesure du coût CPU
   AVANT/APRÈS ;
5. absence de dégradation significative de
   décisions tactiques ou de la couverture
   des capacités.

L'objectif n'est pas d'accélérer artificiellement
des parties en omettant des sorts adverses,
des bloqueurs légaux ou des effets de remplacement.

Voir [PASSATION ACTIVE](PASSATION_ACTIVE_2026-10-10.md)
pour les statuts des jobs et les rapports valides.


## Résultats du premier profilage CPU réel — 10 octobre 2026

**[GitHub Actions 38041169999 — SUCCESS, deux JVM Forge 4 joueurs](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38041169999)**.
Les deux jobs ont compilé Forge 2.0.15 avec les mêmes correctifs
annoncés, exécuté chacun une partie Commander, et produit
un \`real-four-ai-cpu.jfr\`, \`cpu-profile.json\` et les logs originaux.
Aucun deck canonique n'a été modifié ; **les résultats de ces deux
parties profilées ne sont pas utilisés dans les winrates**.

| Profil JFR | Aristo | Artifact | Total |
|---|---:|---:|---:|
| Durée wall, secondes | 201,80 | 131,22 | 333,02 |
| Échantillons CPU d'exécution Java | 13 943 | 8 041 | 21 984 |
| Échantillons dont la pile contient \`forge.ai\` | 890 | 532 | 1 422 |
| Parmi ceux-ci, catégorisés **combat** | 688 | 368 | **1 056** |
| Sous-catégorie \`ComputerUtilCombat\` | 491 | 271 | **762** |
| Sous-catégorie attribution de bloqueurs | 190 | 88 | **278** |
| Sous-catégorie prédiction d'attaques | 7 | 9 | 16 |

**74,3 % des échantillons qui comportent une méthode \`forge.ai\`
concernent la prédiction ou la décision de combat**, et non 74,3 %
du CPU total de Forge. Il s'agit d'une proportion des **1 422
échantillons classés IA**, pas des 21 984 échantillons Java. Les règles,
effets statiques et opérations Java à l'extérieur de la pile IA sont
présents parmi les autres échantillons. De même les comptes de
méthodes « présentes dans une pile » se recouvrent.

Dans **les deux pods**, les méthodes de la famille
\`forge.ai.ComputerUtilCombat\` sont omniprésentes, notamment
\`canDestroyBlocker\`, \`canDestroyAttacker\`,
\`predictPowerBonusOfAttacker\` et
\`predictToughnessBonusOfAttacker\`. Dans le groupe aristo,
\`predictPowerBonusOfAttacker\` apparaît dans 114 échantillons
avec cadre IA, \`canDestroyBlocker\` dans 98 et
\`predictDamageTo\` dans 87. Dans artifact, respectivement
48, 54 et la logique de dommages/effets est également fréquente.

**Décision de développement fondée sur ces mesures :**
ne pas « optimiser » en écartant des bloqueurs, des effets
de remplacement ou en donnant des décisions gratuites aux IA.
Le premier axe d'investigation est **l'élimination des
recalculs strictement redondants** au sein de la prédiction de
combat, avec invalidation immédiate dès qu'une créature,
la pile, un effet continu ou une déclaration de bloqueur
change. Une mise en cache naïve sur tout un tour serait
dangereuse : les caractéristiques P/T et la légalité des
blocs peuvent changer pendant une même décision.

Avant de changer le moteur, établir des tests comparatifs
sur des positions tactiques, puis mesurer le CPU JFR
et les issues naturelles. Les profils JFR ne prouvent
pas encore qu'une optimisation particulière conserverait
les mêmes décisions et la même légalité.
