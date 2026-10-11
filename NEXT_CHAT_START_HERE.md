# Brimaz Forge Lab — REPRENDRE ICI (V32)

**Version de travail 11 octobre 2026 :**
[docs/PASSATION_ACTIVE_V32_2026-10-11.md](docs/PASSATION_ACTIVE_V32_2026-10-11.md)
pour les sept decks canoniques désormais **permanents**, le moteur
Forge 4 IA et les contrôles de provenance ; puis
[docs/PASSATION_ACTIVE_V31_2026-10-11.md](docs/PASSATION_ACTIVE_V31_2026-10-11.md)
pour l'orchestrateur A/B de huit ou seize vrais processus Forge.

V32 est une branche fille de V31 (PR #24), elle-même basée sur V30,
et **n'est pas fusionnée dans main**. Source originelle des decks :
[run 37966009166](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37966009166).
La récupération/commit SHA vérifiés sont **réellement réussis** :
[run 38127191276](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38127191276).
L'exécution des nouveaux tests et huit JVM V31/V32 est à vérifier
séparément. Ne jamais déduire qualité IA ni vrai winrate d'une CI verte.

---

# Reprise du développement — Brimaz Forge Lab

**Version de travail : V31, 11 octobre 2026.**
Lire d'abord [PASSATION_ACTIVE_V31_2026-10-11.md](docs/PASSATION_ACTIVE_V31_2026-10-11.md).

- **Branche :** `feature/v31-reproducible-4ai-operator-20261011`, basée sur la V30.
- **Source de vérité :** les résultats GitHub Actions et les vraies traces Forge Java21, jamais le seul état vert d'une action.
- **Dernier pilote V30 réel :** [run 38096353743](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38096353743).
  3 matchs naturels sur le pod artifact, 3 censures sur aristo ;
  16 879 677 vérifications des cinq prédicats à état identique,
  aucune divergence observée, mais accélération globale non démontrée.
- **V25 :** [run 38094639616](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38094639616),
  14/16 parties naturelles, speed ratio médian 0,9959 (aucun gain établi).
- **Nouveau lanceur d'expérience A/B réelle :**
  `scripts/run_paired_four_ai.py`, modes `v17_strict`,
  `v30_exact_rules` et `v30_shadow_verify`.
- **Windows :** `scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v30_exact_rules -Pod artifact -GamesPerRotation 1`.
- **Portes de validation :**
  `.github/workflows/v31-operator-validation.yml` pour les tests
  de contrats synthétiques et `.github/workflows/v31-real-paired-forge.yml`
  pour huit vraies JVM (ne pas conclure que huit matchs finiront naturellement).
- **Ne pas confondre :** fonctionnement du moteur, conformité des règles,
  efficacité des décisions, validité statistique de winrate.

**Point crucial :** `main` contient encore l'ancien socle de
développement ; les PR V13–V30 restent empilées, expérimentales ou non
fusionnées. Consolider seulement après validation de l'intégration réelle.
Aucune des versions V14, V25 ou V30 n'a démontré une IA humaine compétente.
