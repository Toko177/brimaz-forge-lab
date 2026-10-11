# Brimaz Forge Lab

Simulateur **Magic: The Gathering Commander à quatre IA** avec le vrai moteur
[Forge 2.0.15](https://github.com/Card-Forge/forge), Java 21, parties
indépendantes, sept decks canoniques épinglés par SHA256, journalisation,
certification et comparaisons de politiques.

**Branche active : `main`.** Anciennes expériences conservées dans
`archive/experimental-branches-20261011`, aucune PR ouverte.
Nettoyage global effectué le 11 octobre 2026 :
[30 anciennes branches supprimées](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38131746597),
[PR de consolidation #28](https://github.com/Toko177/brimaz-forge-lab/pull/28).
L'historique de `main` et de toutes les branches expérimentales a été préservé.

Le workflow **Commander four-AI manual real Forge games** dans GitHub Actions
permet les campagnes de vraies parties, seules ou appariées A/B, en utilisant
les decks canoniques versionnés. [Guide de reprise](NEXT_CHAT_START_HERE.md)
et [historique du nettoyage](docs/GLOBAL_GITHUB_REPOSITORY_AUDIT_2026-10-11.md).

## Ce qui fonctionne réellement

- Compilation du patch V33 contre le véritable JAR Forge Java 21,
  [test validé](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38128781138).
- Lancement de quatre sièges et comparaison A/B sur les deux groupes d'adversaires.
- [V33, 16 parties réelles / 16 fins naturelles](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38128781081).
  Les parties ont divergé, mais **l'ancien audit V33 était défectueux** :
  son parseur cherchait un nom de journal incorrect et des expressions
  régulières mal échappées. La V34 corrige ces défauts ; le nombre réel
  d'actions approuvées doit être recalculé depuis les artefacts du run.
  Aucune amélioration stratégique n'est encore démontrée.
- Les parties censurées ou en erreur ne sont **jamais** comptées
  comme des victoires naturelles.

## Reprendre le développement

Voir [la V33 et ses limites](docs/V33_MULTIPLAYER_STRATEGIC_PLANNER.md)
et [l'organisation épurée](docs/REPOSITORY_STRUCTURE.md).
La priorité est de **réauditer les journaux réels V33 avec le parseur corrigé**,
puis d'évaluer les refus éventuels de Forge et d'améliorer la décision
sans déformer les règles.

### Installation et exécution (Windows)

Prérequis : Python 3.10+, JDK 21 et `gh auth login`.
Le programme récupère l'archive officielle Forge et vérifie son SHA256.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v33_strategy -Pod both -GamesPerRotation 1 -Parallel 2 -Clock 420 -PreflightOnly
```

Pour lancer **16 véritables processus Forge** (2 pods × 4 positions ×
2 politiques), enlever `-PreflightOnly`.

Sur Linux ou avec un JAR déjà installé :
```bash
python3 scripts/run_paired_four_ai.py \
  --jar /chemin/forge-gui-desktop-2.0.15-jar-with-dependencies.jar \
  --reference-policy v17_strict --experiment-policy v33_strategy \
  --pod both --parallel 2 --games-per-rotation 1 --clock 420
```

[Guide de lancement détaillé](docs/RUN_LOCAL_4AI_COMMANDER.md).

## Points d'entrée et tests

| Objectif | Chemin |
|---|---|
| Expérience Forge réelle | `scripts/run_paired_four_ai.py` |
| Exécuter une politique | `scripts/run_local_four_ai.py` |
| Préparer un PC Windows | `scripts/setup_and_run_four_ai.ps1` |
| Patch principal actuel | `scripts/patch_forge_brimaz_v13.py` |
| Planificateur V33 | `patches/java/forge/ai/MultiplayerStrategicModel.java` et `MultiplayerStrategicSequencer.java` |
| Audit des vraies décisions | `scripts/audit_v33_real_strategy.py` |
| Résultats naturels / censures | `scripts/certify_commander_games.py` |
| Référence canonique | `forge_decks/\*.dck` et `canonical/results/forge_normalization/report.json` |
| Deckbuilding A/B | `docs/DECKBUILDING_QUICKSTART.md` |

Les workflows conservés concernent la validation courante,
le test réel Forge, la légalité et le deckbuilding.
Les anciennes expérimentations restent récupérables dans
l'historique Git, sans encombrer les nouveaux développements.
