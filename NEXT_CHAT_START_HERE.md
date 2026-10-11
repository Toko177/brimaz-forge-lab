# REPRENDRE ICI — Brimaz Forge Lab / branche expérimentale V35

**PR #29** : https://github.com/Toko177/brimaz-forge-lab/pull/29
Brancher les travaux sur `feature/v35-strategic-search-20261011`,
depuis `main` consolidée. Les autres anciennes branches expérimentales
ne doivent pas être rouvertes. V35 introduit un planificateur borné de
séquences de 3 sorts sur 2 tours avec maintien de la validation légale
Forge ; lire d'abord [la note V35](docs/V35_STRATEGIC_SEARCH.md).
Résultat de qualité IA non démontré tant que les véritables A/B
et journaux d'interventions ne sont pas inspectés.

## Statut empirique réel de la V35

Le pilote original ([16 parties Forge](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38133124128))
a enregistré 230 propositions approuvées par le vrai contrôleur Forge
(101 Aristo, 129 Artifact), 15 fins naturelles et une partie censurée.
**Aucun gain stratégique ou winrate statistiquement validé**. Depuis
ce pilote, la branche inclut `MultiplayerTacticalPlannerV35` pour
retrait ciblé, nettoyage de plateau et réanimation défensive, plus
une correction de la menace multiadversaire et du mana futur.
Relire `docs/V35_STRATEGIC_SEARCH.md` avant la fusion et vérifier la
dernière CI Java21 et la nouvelle comparaison A/B de 16 vraies JVM.

## Socle intégré sur main

**11 octobre 2026 — dépôt consolidé et nettoyage global achevé.**

- Branche stable : `main` ; branche actuelle de travail : `feature/v35-strategic-search-20261011`.
- Deux autres branches distantes : `archive/experimental-branches-20261011`
  (archive) et `feature/v35-strategic-search-20261011` (PR #29).
- **Une PR ouverte (#29).** [PR de consolidation #28](https://github.com/Toko177/brimaz-forge-lab/pull/28),
  fusionnée par GitHub sans force-push : l'historique préexistant de
  `main`, celui de V34 et les six historiques divergents sont accessibles
  depuis le nouveau `main`.
- Les trente autres branches distantes ont été supprimées après vérification
  des SHA et de leur inclusion dans le Git ancestry de `main` :
  [workflow de suppression réussi](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38131746597).
- Les 7 decks originaux et leur rapport de normalisation sont versionnés
  (SHA256 immuables). Ne jamais remplacer les decks pour améliorer le winrate.
- Forge **2.0.15 Java 21**, 4 IA, deux pods adverses, quatre rotations,
  vrais processus JVM, conservation des journaux et statut de censure.
- Source patch principale : `scripts/patch_forge_brimaz_v13.py`
  (inclut les deux classes Java V33).
- Exécution locale : `scripts/setup_and_run_four_ai.ps1` ou
  `scripts/run_paired_four_ai.py` ; sur GitHub Actions :
  **Commander four-AI manual real Forge games**.
- Qualité stratégique **non démontrée** : le pilote V33
  [38128781081](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38128781081)
  a obtenu 16/16 fins naturelles et trois paires avec vainqueurs différents,
  mais l'audit initial des décisions était erroné (mauvais nom de journal et
  regex doublement échappée). Le parseur a été corrigé en V34 ;
  les artefacts bruts doivent être réaudités avant toute conclusion.
- Ne pas confondre validation Java, stabilité de Forge, vraie légalité,
  pertinence stratégique, et amélioration de taux de victoire.

## Priorité pour le prochain développement

La V35 combine recherche multi-cartes, priorisation des retraits et
contresorts défensifs. Vérifier le **vrai match A/B 16 JVM** et ses journaux
`FOUR_AI_V35_STOCK_APPROVED` avant toute fusion. Puis réanalyser les preuves des choix stratégiques V33 dans les artifacts
originaux ; vérifier le chemin proposition → approbation par l'IA Forge →
lancement du sort → résultat. Construire des cas tactiques validés par un
joueur compétent, pas de nouvelles versions de scoring mineures sans mesure.

## Documents

- [README](README.md) : installation et points d'entrée.
- [Architecture V33](docs/V33_MULTIPLAYER_STRATEGIC_PLANNER.md).
- [Lancement des parties](docs/RUN_LOCAL_4AI_COMMANDER.md).
- [Référence de vraie victoire Brimaz](docs/REAL_FOUR_AI_BRIMAZ_WIN_REFERENCE.md).
- [Audit global GitHub et résultat du nettoyage](docs/GLOBAL_GITHUB_REPOSITORY_AUDIT_2026-10-11.md).
- [Structure du dépôt](docs/REPOSITORY_STRUCTURE.md).

Les preuves brutes GitHub Actions demeurent consultables selon leur rétention.
La suppression des références Git n'efface pas le contenu des commits
conservés dans l'ascendance de `main`.
