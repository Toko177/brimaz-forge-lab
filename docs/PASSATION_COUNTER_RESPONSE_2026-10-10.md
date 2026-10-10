# PASSATION — Four-AI Commander : protection contre retrait de commandant sur la pile

**10 octobre 2026** — branche `feature/four-ai-critical-counter-response-20261010`,
issue de `feature/v20-counterfactual-removal-and-tournament-20261010`.
Lire d'abord [la passation V20](PASSATION_2026-10-10_V20.md) et le pointeur
`NEXT_CHAT_START_HERE.md` sur main.

## Pourquoi intervenir ici

Le source original `forge-ai/src/main/java/forge/ai/ability/CounterAi.java`
de Forge 2.0.15 tire un choix probabiliste pour accepter certains sorts
à faible CMC. Pour les **quatre** joueurs IA Commander, cela peut
faire refuser de contrer un sort public peu coûteux qui cherche à
**détruire/exiler/voler leur commandant**.

Ce patch **n'augmente pas magiquement le nombre de contresorts en main**.
Il n'est examiné qu'après les contrôles Forge existants : sort public
en pile, cible légalement contrable, coûts applicables, autres restrictions
spécifiques du sort. Il ne contourne pas l'état de la priorité ni les règles
Magic.

## Code

- `scripts/patch_forge_counter_critical.py` : télécharge le `CounterAi`
  d'origine exactement au tag `forge-2.0.15`, vérifie un ancrage
  unique, compile Java 21 contre le JAR et insère les classes modifiées.
- `patches/java/forge/ai/ability/MultiplayerCriticalCounterPolicy.java` :
  inspecte uniquement les informations de la pile déjà publiques.
  Il faut un sort hostile ciblant précisément **notre commandant** et
  dont l'API soit `Destroy`, `ChangeZone` ou `GainControl`.
  N'oblige pas à contrer un simple `Destroy` qui n'affecterait pas
  un commandant indestructible.
- `tests/java/forge/ai/ability/MultiplayerCriticalCounterChecks.java` :
  tests indépendants de la politique, dont des invariants pour les quatre
  sièges. La validité de la pile et de la cible reste à Forge.
- Propriété JVM : `-Dbrimaz.fourSeatCounterCritical=true`, **désactivée**
  par défaut. Journal si la politique corrige un refus :
  `FOUR_AI_CRITICAL_COUNTER accepted ...`.
- `scripts/audit_critical_counter.py` :
  compare deux vrais processus Forge aux mêmes decks/seats/seed,
  compte les décisions compensées, fins naturelles, événements.
- `.github/workflows/four-ai-critical-counter.yml` :
  compile + tests, puis deux pods appariés (quatre vrais matchs).

**IMPORTANT :** ce n'est pas une estimation du résultat
du combat ni une garantie de ne jamais perdre son commandant.
Un changement de décision de `CounterAi` n'est pas à lui seul la
preuve que Forge a lancé le contresort, encore moins d'une victoire.
Ne pas le rendre obligatoire avant audit de logs et d'une position
Forge déterministe où le sort adverse et les possibilités de réponse
sont toutes les deux légales.

## Autres travaux et statut

Le lanceur sur main exécute de vrais matchs 4 IA, et la PR #12 V20
est en cours de validation de classements contrefactuels **à état identique**
pour le choix de créatures à éliminer.
Le rapport de tournoi global `scripts/aggregate_four_ai_tournament.py`
a déjà passé son test sur huit vraies parties archivées (run
38085452376, huit naturelles, zéro censurée, sans niveau humain prouvé).

Ne pas mélanger dans un seul benchmark l'effet du nouveau contresort
et celui des anti-créatures. Le workflow compare uniquement l'option
`fourSeatCounterCritical`, toutes les autres égales.

À chaque futur chat, vérifier PR, derniers Actions, preuves, puis mettre
à jour `NEXT_CHAT_START_HERE.md` et les rapports. Les PR sont empilées ;
ne pas fusionner les feuilles avant les parents.
