# V32 — Dépôt autonome de sept decks Commander SHA256 canoniques

**11 octobre 2026 — passation.** Branche active
`feature/v32-persistent-canonical-commander-decks-20261011`,
basée sur `feature/v31-reproducible-4ai-operator-20261011` (PR #24).
État antérieur V31 : [passation](PASSATION_ACTIVE_V31_2026-10-11.md).

## Constat vérifié et correction

Le pilote Forge 2.0.15 réutilisait les **sept decks originaux normalisés**
dans l'artefact `forge-seven-decks-canonical-verified`, run
[37966009166](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37966009166),
qui expire **le 7 janvier 2027**. La dépendance rendait impossible
de reproduire une expérience après cette date sans une copie manuelle.

Le workflow
[38127191276](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38127191276)
a **réellement téléchargé cet artefact**, contrôlé la liste exacte,
l'absence d'erreurs, le SHA256 de chaque deck et la structure Forge
`[Main]` + `[Commander]`, puis commité les **sept fichiers octet pour
octet** dans `forge_decks/` et le rapport original dans
`canonical/results/forge_normalization/report.json`. Le commit bot
a été vérifié : `743b8e5e1e1a7b57d1562e2822dc2f30d912eb09`.

## Invariants et modifications du code

- `scripts/run_local_four_ai.py` conserve **en dur** les sept SHA256
  originaux dans `CANONICAL_DECK_SHA256`; il compare chaque deck
  au rapport **ET** à ces constantes. Une modification coordonnée
  du deck et de son rapport échoue également. Le benchmark reste figé
  sur ces sept listes afin de garantir les expériences reproductibles.
- `scripts/setup_and_run_four_ai.ps1` lit normalement les decks et le
  rapport **directement du dépôt**, sans `gh auth login`. `gh` n'est
  utilisé que pour récupérer un vieil artefact si un clone historique
  ne dispose pas des fichiers.
- `.github/workflows/v31-real-paired-forge.yml` sur la branche V32
  vérifie les decks versionnés directement : aucune dépendance aux
  artefacts de decks pour ses huit vrais matchs Forge.
- `tests/test_run_local_four_ai.py` protège les sept SHA réels et
  rejette deck modifié, rapport+deck falsifiés et deck manquant.
  Ces tests **ne simulent aucune partie**.
- `.github/workflows/v32-offline-decks-test.yml` exige Python
  3.10 et 3.12 sur Linux, plus l'analyse syntaxique du lanceur
  PowerShell sur Windows. Regarder les **runs effectifs** avant de
  dire que cette CI a réussi.

## Exemple réel Windows

Depuis cette branche, avec Python 3.10+, Java/JDK 21, les commandes
`java`, `javac`, `jar`, `tar` et accès HTTPS pour télécharger
Forge officiel (pas de `gh` obligatoire) :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v30_exact_rules -Pod artifact -GamesPerRotation 1 -Parallel 2 -Clock 420 -PreflightOnly
```

Supprimer `-PreflightOnly` pour lancer **huit parties réelles** :
deux variantes du moteur sur quatre rotations du pod artifact.
`-Pod both` couvre 16 processus distincts. Les parties interrompues
restent censurées, pas des défaites inventées. Le dossier
`results/local_pairs` contient les vrais journaux, les preuves de
provenance et la comparaison.

## État honnête et suites

V25 : 14/16 JVM naturellement terminées ; gain de rapidité médian
non démontré. V30 : 3/6 naturellement terminées (3 censures aristo) ;
16 879 677 comparaisons de prédicats à même état, zéro divergence
observée, mais ni conformité Oracle exhaustive ni équivalence
stratégique humaine. Ces résultats **ne valident pas encore V32
en production**.

Après validation de V32 : examiner les rapports des huit véritables
JVM du workflow V31/V32 ; éliminer les goulets de calcul du combat
sur les piles JFR sans toucher aux règles, puis tester des alternatives
de décision **légales Forge au même état** et une campagne plus large.
Ne pas fusionner automatiquement les PR empilées dans `main` tant
que la porte de release de l'intégration n'a pas été franchie.
