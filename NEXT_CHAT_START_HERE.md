# Reprise active — V34 (nettoyage V33)

**11 octobre 2026.** Branche de continuation :
`feature/v34-repository-cleanup-20261011` ;
parent `feature/v33-multiplayer-strategic-planner-20261011` (PR #26).
`main` est encore ancien et les PR #24–#26 sont empilées et non
fusionnées : ne pas repartir de `main` pour le prochain correctif.

## Vérités constatées

- Le vrai Forge 2.0.15 Java 21 exécute des Commander 4 IA avec 7 listes
  canoniques SHA256 fixes.
- La V33 compile réellement :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/38128781138
- Dernier A/B V33 :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/38128781081
  **16/16 parties naturelles** ; trois paires ont changé de vainqueur.
  Le résultat « 0 choix V33 » n'est PAS interprétable : l'audit recherchait
  `STRATEGIC_CHOICE` au lieu de `STRATEGIC_PROPOSAL` et contenait des
  échappements regex erronés pour `STRATEGIC_ACTION`.
  La V34 corrige le parseur et son test synthétique ; il faut rejouer
  l'analyse des artefacts originaux avant toute conclusion sur l'usage de l'IA.
- `scripts/patch_forge_brimaz_v13.py` reste le patch actuel,
  malgré son nom historique : il compile les deux classes V33.
- Le flag `v33_strategy` est opt-in et symétrique sur les quatre sièges.
  Les coûts, les règles et les résolutions restent à Forge.

## Priorité immédiate

**Réauditer les artefacts V33 avec les expressions régulières corrigées**, puis
quantifier propositions, approbations Forge, sorts réellement lancés et
choix par défaut. Ne pas confondre le résultat initial erroné de l'audit
avec une absence réelle de décisions. Ne pas inférer l'efficacité
du planificateur des seuls tests synthétiques ; éviter de relancer
une grande campagne tant que l'intervention n'est pas démontrée
sur une partie ciblée.

## Fichiers à consulter

1. `README.md` — installation, points d'entrée et commandes.
2. `docs/V33_MULTIPLAYER_STRATEGIC_PLANNER.md` — modèle et restrictions.
3. `docs/REPOSITORY_STRUCTURE.md` — protections du nettoyage.
4. `docs/RUN_LOCAL_4AI_COMMANDER.md` — lancer les expériences.
5. `docs/COMBAT_CPU_PROFILING.md` — historique du goulot CPU.

Cette branche supprime 110 fichiers historiques/redondants,
**pas leurs commits Git, leurs branches ou leurs PR**.
Aucune suppression des sept decks, des contrôles SHA,
des principaux scripts, des analyses V33 ni des outils
de deckbuilding.
