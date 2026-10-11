# V14 — Combat Commander à quatre IA

## Objectif
Le choix historique de cible de Forge 2.0.15 s'appuie sur une menace de plateau et un tirage aléatoire parmi scores proches. La V14 évalue les attaquants disponibles contre chaque joueur, les bloqueurs visibles, la possibilité de dégâts non bloqués et une élimination potentielle.

## Propriétés
- Option JVM brimaz.fourSeatCombatTarget=true ; option désactivée = comportement original.
- Chaque siège IA exploite la même politique, pas de privilège artificiel pour Brimaz.
- Les restrictions d'attaque et blocage sont demandées au moteur Forge. L'état public des animateurs et Incubateurs défensifs est considéré.
- Distinction dégâts de vie (y compris wither) et marqueurs poison (infect).
- Monarchie, initiative et adversaires protégés sont évalués.
- Les états trop larges retournent au choix historique pour borner les calculs.
- Aucun changement des effets, coûts, textes, règles, cartes ou capacités adverses.

## Validation
La CI exécute des tests Java de classement tactique, puis des paires de parties réelles en quatre sièges sur deux pods canoniques. Baseline V13 et V14 utilisent le même JAR Forge 2.0.15 avec les mêmes correctifs. Le rapport distingue parties naturelles, censures, gagnants, décisions et durée.

## Réserves
Une élimination apparemment possible ne garantit pas le résultat : des réponses instantanées peuvent modifier le combat. L'amélioration réelle de la politique devra être établie sur des transcriptions certifiées et des graines indépendantes. Le benchmark V14 est séparé du projet d'optimisation CPU PR #3.

## Travaux suivants
Inspecter les décisions observées par siège ; enregistrer les alternatives et les raisons de classement, les déclarations d'attaque et pertes matérielles ; comparer les séquences à de véritables replays humains contenant les actions et états publics ; élargir les rotations et pods avant tout classement statistique.
