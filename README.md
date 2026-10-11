# Brimaz Forge Lab

Simulateur **Magic: The Gathering Commander à quatre IA** avec le vrai moteur
[Forge 2.0.15](https://github.com/Card-Forge/forge), Java 21, parties
indépendantes, sept decks canoniques épinglés par SHA256, journalisation,
certification et comparaisons de politiques.

**Branche stable : `main`.** Une seule expérimentation active :
`feature/v35-strategic-search-20261011` ([PR #29](https://github.com/Toko177/brimaz-forge-lab/pull/29)),
en plus de l'archive historique `archive/experimental-branches-20261011`.
Nettoyage global effectué le 11 octobre 2026 :
[30 anciennes branches supprimées](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38131746597),
[PR de consolidation #28](https://github.com/Toko177/brimaz-forge-lab/pull/28).
L'historique de `main` et de toutes les branches expérimentales a été préservé.

Le workflow **Commander four-AI manual real Forge games** dans GitHub Actions
permet les campagnes de vraies parties, seules ou appariées A/B, en utilisant
les decks canoniques versionnés. [Guide de reprise](NEXT_CHAT_START_HERE.md)
et [historique du nettoyage](docs/GLOBAL_GITHUB_REPOSITORY_AUDIT_2026-10-11.md).

## Recherche stratégique expérimentale V35 (en développement)

[PR #29](https://github.com/Toko177/brimaz-forge-lab/pull/29) — branche unique
`feature/v35-strategic-search-20261011`, basée sur `main`.
Recherche bornée d'un plan de **trois sorts sur deux tours**,
synergies Brimaz jetons/sacrifice/mort, ressources, sécurité et
menaces visibles des trois adversaires, priorisation des retraits
et protection contre les menaces publiques critiques sur la pile.
Toute vraie action doit rester
validée par `AiController.canPlayAndPayFor` de Forge ; la proposition ne
constitue pas un sort joué. La **qualité stratégique V35 n'est pas encore
démontrée par des parties réelles**.

[Architecture, hypothèses, tests et limites](docs/V35_STRATEGIC_SEARCH.md).
Ne pas fusionner sans vérifier la compilation Java 21 réelle,
les journaux de décisions approuvées et les parties A/B, sans toucher
aux sept decks épinglés par SHA256.

**Pilotage tactique complémentaire :** la V35 évalue désormais les
retraits urgents, les remises à zéro de plateau et la reconstruction depuis
le cimetière, toujours avec le contrôle original de Forge. Le pilote
initial sur 16 JVM a enregistré **230 choix approuvés** (15 fins
naturelles, 1 censure), sans preuve de gain de victoire ; les modifications
tactiques ultérieures nécessitent une nouvelle mesure.

**Évaluation scientifique corrigée :** la campagne de référence `v17_strict`
n'utilisait pas Forge d'origine. Le protocole vérifiable
`forge_stock` conserve désormais le JAR originel byte-à-byte
(aucun patch, aucune propriété spécifique). Le nouveau benchmark
sépare résultats naturels et censures, victoires de Brimaz, taille de
l'échantillon et incertitude. **Aucune supériorité IA face à Forge stock
n'est revendiquée avant mesure suffisante.**
[Limites méthodologiques](docs/V35_STRATEGIC_SEARCH.md).

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
La priorité est de **valider la V35 sur de vrais matchs**, puis de réauditer les journaux V33 avec le parseur corrigé,
puis d'évaluer les refus éventuels de Forge et d'améliorer la décision
sans déformer les règles.

### Installation et exécution (Windows)

Prérequis : Python 3.10+ et JDK 21 ; `gh` uniquement pour les anciennes branches dont les decks ne sont pas versionnés.
Le programme récupère l'archive officielle Forge et vérifie son SHA256.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v35_strategy -Pod both -GamesPerRotation 1 -Parallel 2 -Clock 420 -PreflightOnly
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
