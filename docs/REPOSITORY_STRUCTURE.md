# Dépôt épuré : périmètre de maintenance

**V34 — 11 octobre 2026.** Nettoyage non destructif dans la branche
`feature/v34-repository-cleanup-20261011`, parent V33.

## Modifications

- Suppression de **83 workflows historiques et one-shot** (pilotes V2–V28,
  premiers benchmarks, migrations, imports et investigations terminées).
  Les 14 workflows maintenus avant nettoyage restent présents.
- Suppression de **12 anciens scripts de patch Brimaz**
  (`patch_forge_brimaz.py` et `_v2.py` à `_v12.py`).
  **`patch_forge_brimaz_v13.py` reste la version réellement compilée**,
  dont les classes stratégiques V33.
- Suppression de **15 passations/rapports historiques dupliqués**, pas des
  documents d'architecture opérationnels ou des diagnostics pertinents.
- Refonte de `README.md`, `NEXT_CHAT_START_HERE.md` et du guide local ;
  ajout d'un contrôle CI de cohérence et de `.gitignore`.
- Total des suppressions : **110 fichiers, environ 815 287 octets** de
  sources YAML/Python/Markdown. L'historique Git conserve tous ces fichiers.

## Périmètre protégé

- `forge_decks/\*.dck` — exactement 7 originaux, empreintes fixées dans
  `scripts/run_local_four_ai.py` et
  `canonical/results/forge_normalization/report.json`.
- `scripts/run_local_four_ai.py`, `run_paired_four_ai.py`,
  `batch.py`, `compare_local_four_ai_campaigns.py`,
  `certify_commander_games.py`, `validate_commander_legality.py`.
- `scripts/patch_forge_brimaz_v13.py`,
  `patch_forge_four_ai_targets.py`, `patch_forge_charm_context.py` et
  les sources Java utilisées par les politiques encore proposées.
- `patches/java/forge/ai/MultiplayerStrategicModel.java` et
  `MultiplayerStrategicSequencer.java`, audits et tests associés.
- Toute la filière de comparaison et d'optimisation des decklists,
  tests et documentation de deckbuilding.
- Les **branches et PR historiques n'ont pas été supprimées ou fermées** ;
  `main` est également inchangée.

## Workflows opérationnels

- `repository-health.yml` — vérification de structure, tests Python, SHA256.
- `v33-strategic-compile.yml` — JDK 21 + vrai JAR Forge.
- `v33-real-strategy-ab.yml` — A/B réel 4 IA, deux pods.
- `v31-operator-validation.yml`, `v31-real-paired-forge.yml`,
  `v32-offline-decks-test.yml` — reproductibilité, Windows et decks.
- `v30-exact-card-property-rules.yml` — équivalence du fast-path opt-in.
- `commander-legality.yml`, `forge-smoke.yml`.
- `deckbuild-*.yml` conservés — campagnes A/B, tournois, classement
  et tests de decklists.

Les anciennes PR ont leurs propres branches et scripts d'époque, accessibles
pour une investigation ponctuelle sans polluer le chemin courant.

## Avant d'intégrer vers main

Le socle `main` est toujours ancien et les PR #24–#26 sont empilées.
Valider le correctif IA et les tests réels sur la branche actuelle, puis
planifier **l'intégration complète** plutôt que fusionner uniquement
un commit de suppressions sur `main` au risque de retirer l'outillage
préexistant sans introduire sa remplaçante V33.

Le benchmark V33 a eu **16 fins naturelles**, mais son premier audit
« zéro action approuvée » utilisait deux expressions régulières incorrectes.
Le parseur est corrigé en V34, et la réanalyse des artefacts reste à faire.
La qualité stratégique n'est pas démontrée par les seules fins naturelles.
