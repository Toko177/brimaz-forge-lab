# INTÉGRATION — première version utilisable du simulateur Commander à quatre IA

**10 octobre 2026.** Branche `integration/four-ai-commander-simulator-20261010`,
basée sur le dernier code `feature/v22-four-ai-operator-smoke-and-counter-audit-20261010`.
Cette branche est une **candidate de consolidation vers main**, pas un
résultat de winrate certifié ni une preuve que les IA jouent au niveau humain.

## Ce que regroupe la candidate

1. **Vrai moteur Forge 2.0.15** (Java 21), partie Commander à quatre
   IA, coûts et Oracle suivant l'implémentation Forge, pile, combat,
   mulligans et vrai déroulement tour par tour.
2. **7 decks fixes normalisés**, vérifiés SHA256, dont Brimaz V3 et les
   six adversaires, deux pods et quatre rotations ; vrai processus
   indépendant par partie.
3. **Pilotage GitHub** via `.github/workflows/commander-four-ai-simulator.yml`
   présent sur main et [manuel](https://github.com/Toko177/brimaz-forge-lab/blob/main/docs/HOW_TO_RUN_FOUR_AI_SIMULATOR.md).
   Matrices distribuées, conservation des logs et provenance exécutable.
4. **Évaluation empirique** `forensic_four_seat.py`,
   `aggregate_four_ai_tournament.py`, V20 same-state legal removal
   counterfactual, tests de falsification et classification des censures.
5. **Améliorations tactiques optionnelles et réversibles** sur chaque
   siège, toujours soumises à la légalité de Forge : choix des
   adversaires, couverture défensive, ciblage du retrait, contresorts
   contre enlèvement ciblé du commandant et sort public à dommage/
   perte de vie chiffré et létal.

## Politique de sortie : ne pas fusionner les bonus à l'aveugle

| Fonction | Contrôle de robustesse | Preuve de qualité tactique |
|---|---|---|
| Partie réelle à quatre IA | Plusieurs vrais processus naturels vérifiés | Le niveau humain n'est **pas** démontré |
| Rapport tournoi | 8 vrais logs déjà consolidés | Les intervalles descriptifs ne démontrent pas de winrate |
| Politique V19 de cible de retrait | 804 classements réels à état identique, aucun changement | **Aucun bénéfice constaté** |
| Réserve défensive V17/V17.1 | Simulations Forge complètes et invariants | Pas de gain de victoire démontré |
| Contresorts PR #13 | 4 matchs naturels, 11 tests Java | Aucune exception active dans l'échantillon |
| Contresorts V22 | tests supplémentaires + smoke E2E vrai Forge | **Encore expérimental**, inspecter la dernière CI |

**Par défaut**, garder un mode testé et reproductible du lanceur
(`v17_strict`) ; les fonctions expérimentales nécessitent un
choix explicite. Le mode `critical_counter` est un **pilote**, pas
le nouveau comportement certifié de l'ensemble des IA.

Les vrais événements de Forge seuls servent à parler de jeux gagnés ;
les parties censurées, exceptions moteur et limites ne sont pas des
défaites fabriquées. Ne jamais affirmer la fidélité Oracle exhaustive
ou la qualité humaine des IA sans validation indépendante.

## Portes de validation avant éventuelle fusion vers main

- [ ] Le **dernier** vrai smoke E2E V22 a terminé avec 7 SHA
  canoniques, Java 21, un match à quatre sièges et les rapports
  forensiques et de tournoi ; vérifier son Artifact réel.
- [ ] Le workflow manuel `workflow_dispatch` de main a été lancé
  explicitement une fois ; les 8 matrices et le fan-in de résultats
  ont bien eu lieu. Le simple existence du YAML ne vaut pas preuve.
- [ ] Les PR empilées V13–V22 ont été relues pour collision ou
  modification de politique globale non documentée ; le JAR patché
  est versionné par SHA dans les rapports.
- [ ] Les modes IA pour contresorts et retrait ont des tests de
  contre-exemples réels à état identique, non uniquement des
  tests de scoring abstrait.
- [ ] Les scripts de certification des résultats vérifient les
  decklists via le rapport Scryfall et un seul gagnant naturel ;
  pas de winrate inféré d'un petit échantillon apparié.

## Pipeline recommandé pour continuer rapidement

1. Vérifier [les Actions](https://github.com/Toko177/brimaz-forge-lab/actions)
   puis résoudre **d'abord** les erreurs de lancement et d'agrégation.
2. Obtenir des états Forge réellement reproductibles et des
   **alternatives légales** pour les choix d'attaques, défense et
   pile. L'instrumentation V20 peut mesurer l'effet au même état.
3. Comparer sur 16 à 40 parties indépendantes, quatre positions,
   deux pods, plusieurs graines, taux de censure et lenteurs des IA.
4. Traiter au moyen de JFR les véritables points chauds de combat ;
   l'ancienne optimisation des déclencheurs (PR #3) n'a pas
   démontré de gain et ne doit pas être fusionnée pour la vitesse.
5. Consolider les PR lorsqu'elles sont validées, éviter de laisser
   le projet enfermé dans de nouvelles branches expérimentales
   et **mettre à jour la passation dans GitHub** à chaque chat.

L'historique V13–V22 et les procédures techniques sont détaillés
dans `docs/PASSATION_ACTIVE_V22_2026-10-10.md` ainsi que les
passations V16–V20.

