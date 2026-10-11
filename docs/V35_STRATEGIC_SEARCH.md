# V35 — recherche stratégique Commander à quatre IA

Date : 11 octobre 2026. Branche : `feature/v35-strategic-search-20261011`.
[PR #29](https://github.com/Toko177/brimaz-forge-lab/pull/29)
contre `main` (une seule branche de travail ; une seule PR).

## Changement fonctionnel

V33 évaluait principalement des cartes isolées et une seule continuation
hypothétique. V35 introduit **une recherche bornée de séquences de trois
sorts sur deux tours**, sans inventer de pioches ni simuler des états de Magic
impossibles à garantir. Le nombre d'options examinées est limité à 20,
avec trois niveaux : première décision immédiate, éventuel second sort
au même tour, et une carte **déjà connue** au tour suivant.

C'est une **abstraction stratégique**, pas un Monte-Carlo Magic à quatre
IA ni un moteur de règles de remplacement. La branche n'améliore pas
automatiquement le niveau de l'IA : elle rend la qualité des décisions
testable et modifie l'ordre de préférence quand Forge donne son accord.

### État utilisé (infos autorisées pour le joueur IA)

- Sa propre main, sa zone de commandant et son plateau ; terres présentes
  dans la main si projection au tour suivant (pas de future carte piochée).
- Mana **estimé** dans Forge, nombre de sources de mana et de terrains.
- Points de vie, puissance des créatures visibles sur les plateaux des
  **trois** adversaires, et présence de bloqueurs amis.
- Ressources et combinaisons de cartes : jetons, sacrifice,
  moteurs de jetons/incubation, payoff de mort/sacrifice,
  effets multiplicateurs, pioche, protection, recursion.
- Des noms de cartes précis pour caractériser les synergies quand leurs
  textes ne permettent pas de généralisation fiable (en particulier le
  vrai deck Brimaz V3 conservé byte à byte).

### Trois modules IA complémentaires de la V35

1. **Planification proactive** : recherche bornée de trois cartes connues.
2. **Retraits tactiques** : la politique historique
   `MultiplayerRemovalUrgencyPolicy.publicThreatBonus` ne classe que des
   créatures déjà légalement ciblables par Forge. Elle utilise les
   menaces publiques imminentes (vie, poison, dégâts de commandant).
3. **Contresorts défensifs** : `MultiplayerCriticalCounterPolicy`
   intervient uniquement lorsque Forge envisage une réponse réelle à
   une menace sur la pile. La politique évite un refus heuristique face
   à une destruction ciblée du commandant ou une menace létale chiffrable.

Ces deux modules existaient séparément depuis V19/V22, mais **la V35
les active simultanément, avec la recherche stratégique, pour les quatre
sièges**. Le benchmark global mesure la politique composée, pas la
contribution individuelle de chaque sous-module. Les règles, cibles,
coûts, réponses sur la pile et autorisations restent ceux de Forge.

### Priorités contextuelles

Le modèle augmente le poids d'une créature utile quand la table représente
une menace, réduit le poids d'une rampe lente en état critique, valorise
une accélération de mana au début de partie, et fait émerger des plans
comme `Brimaz → jetons → outlet de sacrifice → payoff de mort`.
La contribution du prochain tour est fortement escomptée sous pression.

**Limites** : la puissance brute des créatures n'est pas une prédiction
légale des attaques ou des blessures ; aucun effet de remplacement,
capacité déclenchée, activation, combat, interaction sur pile, possession
de mana coloré futur, disponibilité de cible ou draw futur n'est simulé
dans la recherche abstraite. Les sorceries, réponses ciblées et actions
hors des phases principales sont toujours sélectionnées par Forge.

## Contrainte absolue de légalité

`MultiplayerStrategicSequencerV35.rank(player, saList)` ne retourne qu'une
liste de candidats issus des **véritables SpellAbility Forge** du joueur,
sur pile vide, pendant sa propre phase principale. La source originale
`AiController` continue de contrôler le jeu de la carte :

```java
AiPlayDecision decisionV35 = canPlayAndPayFor(v35);
if (decisionV35 == AiPlayDecision.WillPlay) return v35;
```

Pas de faux mana, pas de modification de carte ni de gruge sur les
couleurs, taxes de commandant, coûts additionnels, cibles ou règles.
Si Forge refuse les quatre propositions, repli sur les algorithmes
déjà existants, identiques au moteur d'origine.

Activation opt-in **pour les quatre sièges** :
`-Dbrimaz.v35StrategicSearch=true` ou `--policy v35_strategy`.
Tous les autres modes conservent ce flag à false. Les flags de priorité de retrait et de contresorts défensifs sont également activés uniquement pour V35 ou leurs modes individuels historiques ; le mode de référence les désactive.

## Traces interprétables

- `FOUR_AI_V35_WINDOW` : taille de l'espace examiné, candidat
  en tête et séquence projetée. **Pas une action validée**.
- `FOUR_AI_V35_STOCK_APPROVED` : sortie dont l'original
  `canPlayAndPayFor` a donné `WillPlay` ; **pas une preuve de
  résolution effective de sort sur la pile**.
- `FOUR_AI_V35_STOCK_REJECTED` : propositions non acceptées
  par Forge, puis repli stock.

`scripts/audit_v35_real_search.py` refuse les journaux contaminés
dans l'arm de contrôle et les decks modifiés entre expériences. Il
sépare nombre de fins naturelles, décisions approuvées, différences
de déroulement, censures, erreurs et vainqueurs.

## Preuves et actions

- `.github/workflows/strategic-java21-gate.yml` :
  Forge officiel 2.0.15 Java21 + compilation `AiController` modifié
  + Java tests de recherche + contrôles Python.
- `.github/workflows/strategic-real-4ai-ab.yml` :
  2 pods × 4 rotations × 2 politiques = **16 vrais matchs JVM**,
  decks SHA256 vérifiés, horloge 420 s, `v17_strict` contre
  `v35_strategy`. Rapport d'audit et journaux bruts en artefacts.
  La porte d'intervention exige au moins une acceptation par le
  Forge originel dans chacun des deux pods.
- `tests/java/forge/ai/MultiplayerStrategicSearchV35Checks.java` :
  tests purement **synthétiques** : mana, séquences, valeur des jetons,
  priorités défensives à trois menaces, options illégales, bornage,
  déterminisme. Ils ne prouvent pas la qualité du jeu.
- `tests/test_audit_v35_real_search.py` :
  scénarios falsifiants pour les analyses de vraies traces.

## Séquence de validation avant fusion

1. Compiler avec Forge Java21 réel (pas seulement des tests jouets).
2. Vérifier chaque carte canonique SHA256 ; exiger les quatre sièges
   et les deux pods sur les 16 jeux de comparaison.
3. Vérifier `STOCK_APPROVED` sur les véritables traces, et non simplement
   les propositions. Compter les censurements séparément.
4. Comparer les actions et l'impact stratégique réel. Un meilleur winrate
   ne peut être **conclu statistiquement sur huit paires**.
5. Si aucune acceptation : ne pas fusionner comme « amélioration de l'IA ».
   Diagnostiquer `saList`, l'impact de `canPlayAndPayFor` et les critères
   restrictifs sans dégrader la légalité.

## Mesure empirique de la V35 initiale (avant la couche tactique)

Le [benchmark réel du 11 octobre 2026](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38133124128)
s'est terminé sans erreur de CI. Il a exécuté 16 JVM Forge avec les 7 decks
canoniques originaux : **15 parties se sont terminées naturellement**,
une paire comporte une censure ou un défaut. L'auditeur a détecté
**230 décisions de permanents V35 réellement approuvées par l'IA Forge** :
101 dans le pod Aristo et 129 dans le pod Artifact, réparties sur
les quatre sièges. Six paires ont changé de vainqueur, dont une paire
non intégralement naturelle. Ces résultats prouvent que le planificateur
**intervient**, mais ils ne prouvent pas que ses décisions sont meilleures
ni que les 230 sorts ont été effectivement résolus.

## Phase II — nouvelles décisions tactiques et corrections causales

`MultiplayerTacticalPlannerV35` propose, uniquement dans une véritable
fenêtre de phase principale avec pile vide, trois catégories de décisions
non traitées par le premier planificateur :

- **Retrait ciblé** en cas de forte pression d'un adversaire, en laissant
  le moteur Forge sélectionner et vérifier les cibles réelles.
- **Nettoyage du plateau** lorsqu'il faut survivre à un déséquilibre net
  de créatures et de puissance (p. ex. `Sunfall`). Un plateau allié
  solide, incluant le commandant, est protégé par des conditions
  restrictives.
- **Reconstruction depuis son propre cimetière** (p. ex. `Living Death`)
  si un nombre suffisant de créatures y sont déjà connues du joueur.

Cette couche n'affirme aucune prédiction exacte des prochains attaquants :
la puissance du pire adversaire est un indicateur, pas une preuve de
dommages imminents. Pour la même raison, la recherche proactive ne
**somme plus les trois plateaux adverses comme une unique attaque**.
Elle tient compte des propres bloqueurs, de l'exposition et de la santé.

La projection de mana du tour suivant est aussi corrigée : elle repose
désormais sur les terrains effectivement en jeu, ceux **connus** en main
et les accélérations mises en place, plutôt que de croire que les sources
déjà engagées ne se dégageront jamais. Ce n'est toujours pas une
simulation des couleurs, des coûts supplémentaires ou des effets exacts.

Chaque proposition reste conditionnée à
`AiController.canPlayAndPayFor(...) == AiPlayDecision.WillPlay`.
Les cas tactiques sont vérifiés par
`tests/java/forge/ai/MultiplayerTacticalPlannerV35Checks.java` avec
compilation Java21 contre la version officielle de Forge. Le nouvel
auditeur distingue `FOUR_AI_V35_TACTICAL_WINDOW`,
`FOUR_AI_V35_TACTICAL_STOCK_APPROVED` et
`FOUR_AI_V35_TACTICAL_STOCK_REJECTED`.

**Le gain de qualité de cette phase II n'a pas encore été mesuré.**
Ses 16 vraies parties A/B doivent être inspectées séparément du pilote
V35 initial ; les tests synthétiques ne valent pas certification de jeu.

## Note pour les versions ultérieures

Un prochain saut vers une IA de niveau humain nécessitera des **états
réels Forge sauvegardés** et des contrefactuels exacts (combat, activation,
interaction, table politique), puis une référence expert annotée et une
évaluation multicampaigns, pas des coefficients inventés.

## V35 vs **Forge originel non modifié** : nouvelle porte de vérité

Les premiers A/B utilisaient `v17_strict` comme référence. Cette
politique embarquait pourtant déjà nos adaptations V13/V17, de sorte
qu'elle **n'était pas Forge original**. Les 230 interventions approuvées
par l'IA démontrent la mise en service du planificateur, **pas sa
supériorité** sur l'IA stock.

Nouvelle politique `forge_stock` : zéro patch Java, **zéro flag
`brimaz.*`**, copie byte-à-byte du JAR original Forge 2.0.15.
L'audit rejette désormais une prétendue référence originale si la liste
des patchs n'est pas vide, ou si les SHA256 ne coïncident pas. Les
sept decks restent identiques et épinglés entre les deux campagnes.

Le [workflow A/B](../.github/workflows/strategic-real-4ai-ab.yml)
compare maintenant `forge_stock` à `v35_strategy`.
Le rapport sépare les deux taux de fin naturelle, les victoires par
deck, les résultats de Brimaz **sur paires où les deux manches se sont
achevées naturellement**, et les inversions de victoire. Pour Brimaz,
la statistique exacte sur les paires discordantes et les intervalles de
Wilson à 95 % sont fournis comme diagnostics d'incertitude, **pas comme
une validation automatique**.

**Limite méthodologique majeure** : les quatre sièges d'une partie
emploient toujours tous la même politique. Un Brimaz V35 qui gagne
plus souvent contre trois autres V35 qu'un Brimaz original contre
trois autres Forge originaux n'est pas une mesure de duel direct
`V35 contre Forge` : les trois adversaires évoluent aussi.
Même si les résultats favorisent V35, la phrase « IA bien meilleure
que Forge » reste **non démontrée** sans des matchs avec politiques
mixtes (par siège), des réplications nombreuses, des contrôles de
règles et un test statistique robuste.

### Sécurité de Living Death et du cimetière

La couche tactique examine désormais non seulement les créatures de
**son propre** cimetière, mais aussi celles des **trois cimetières
adverses, publics**. Elle ne propose plus prioritairement une
réanimation de masse si le gain potentiel de créatures ennemies est
comparable ou supérieur. Il s'agit encore d'une approximation
conservatrice ; `AiController` et les résolutions Oracle restent
seules sources de vérité pour les cas d'exil, remplacement ou
réanimation modifiée.

## Benchmark **mixte** : Brimaz seul modifié, adversaires constants

En plus des deux campagnes où les quatre sièges jouent avec la même
politique (`forge_stock` original / `v35_strategy`), une seconde
comparaison utilise `v35_brimaz_duel`.

- Référence : Brimaz et ses trois adversaires utilisent `v17_strict`.
- Expérience : **seul le siège Brimaz** reçoit la recherche
  proactive et la gestion tactique V35 ; les trois adversaires restent
  sous `v17_strict`.
- Le duel est répété dans les quatre positions, les deux pods et les
  graines appariées. Le rapport interdit toute intervention V35
  détectée dans un siège adversaire.
- Les modules V19 de retrait ciblé et V22 de contre de menaces ne sont
  **pas activés globalement** en mode `v35_brimaz_duel`.
- Cette comparaison mesure un effet bien plus causal du comportement
  de **Brimaz V35 contre la politique V17 inchangée** que le protocole
  à quatre IA toutes différentes. Elle n'est toutefois **pas** un
  affrontement contre trois véritables Forge originaux : `v17_strict`
  contient des modifications historiques.

Un moteur plus fort contre Forge original demande, au-delà de cette
mesure, des sièges mixtes dont les autres contrôleurs soient réellement
originaux, des jeux sur plusieurs centaines de parties, plusieurs
pods tenus à l'écart du développement, et une évaluation des
erreurs/qualité du combat et des interactions au-delà des victoires.

### Provenance stricte du test mixte

La suite rejette désormais les faux « duels » si les deux bras n'ont pas
**exactement les mêmes scripts de patch JVM**, si la propriété
`v35BrimazOnly=true` manque, si la référence n'a pas désactivé V35,
si les modifications globales V19/V22 sont activées par erreur, ou si
un `V35_WINDOW`/une approbation survient dans un siège non-Brimaz.
Les processus purgent `_JAVA_OPTIONS`, `JDK_JAVA_OPTIONS` et
`JAVA_TOOL_OPTIONS` hérités ; le véritable bras `forge_stock`
n'injecte **aucun** de ces paramètres.
