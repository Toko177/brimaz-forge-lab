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

## Note pour les versions ultérieures

Un prochain saut vers une IA de niveau humain nécessitera des **états
réels Forge sauvegardés** et des contrefactuels exacts (combat, activation,
interaction, table politique), puis une référence expert annotée et une
évaluation multicampaigns, pas des coefficients inventés.
