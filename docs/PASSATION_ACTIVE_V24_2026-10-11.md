# PASSATION ACTIVE V24 — accélération des combats Forge à quatre IA

**11 octobre 2026.** Entrée technique prioritaire pour les futurs chats.
Consulter ensuite `NEXT_CHAT_START_HERE.md` sur `main` et les
passations V23/V22/V20 de cette branche.

## 1. Branche courante / PR

- Dépôt : https://github.com/Toko177/brimaz-forge-lab
- **Branche active :**
  `feature/v24-combat-trigger-fast-negatives-20261011`
- **PR #17 draft :** https://github.com/Toko177/brimaz-forge-lab/pull/17
- Base : `feature/v23-ai-timeout-cooldown-20261010` (PR #16),
  elle-même basée sur la candidate de consolidation
  `integration/four-ai-commander-simulator-20261010` (PR #15)
  dirigée vers `main`.
- `main` possède un **lanceur GitHub stable** et le pointeur de reprise,
  mais surtout l'ancien moteur V6. **Ne pas prétendre que V24 est
  fusionnée sur main.**
- Toujours utiliser le vrai moteur **Forge 2.0.15 / Java 21**,
  sept decks canoniques vérifiés SHA256, deux pods
  `artifact` et `aristo`, quatre sièges IA indépendants.

## 2. Résultats V23 — prouvés, négatifs pour la vitesse

V23 :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38090320826
**SUCCESS dans les deux jobs**, 18 tests Java, quatre vrais processus
Forge à quatre sièges.

| Matrice | Sans mise à l'écart | Avec mise à l'écart | Partie |
|---|---|---|---|
| aristo rotation 1 | 3 timeouts IA | 3 timeouts IA | deux fois `clock_censored` |
| artifact rotation 2 | 1 timeout IA | 1 timeout IA | deux fins naturelles, même gagnant, événements différents |

Quatre exclusions provisoires d'ID de carte ont été observées, MAIS
**aucune diminution du nombre de timeouts**. La variation de temps
218,58 -> 202,53 secondes du pod artifact n'est **pas** une preuve
d'accélération fiable : les événements ont divergé. V23 reste
**désactivée** sauf expérience explicite.

Les huit logs correspondants ont été inspectés dans les artefacts
GitHub Actions, notamment :
- `four-ai-v23-timeout-aristo-rot1` ;
- `four-ai-v23-timeout-artifact-rot2`.

Plusieurs `AI eval thread at timeout` montrent de vrais calculs
dans `ComputerUtilCombat.combatTriggerWillTrigger`,
`AiBlockController.makeRequiredBlocks`,
`Card.getStaticAbilities`, `ReplacementHandler` et
`CombatUtil.mustBlockAnAttacker`.

**Le nom `lastCandidate=Magic Damper` ou
`lastCandidate=Vault of the Archangel` n'est PAS une cause prouvée.**
Ne pas construire une liste noire par nom de carte.

## 3. V24 : optimisation conservatrice du hot path de prédiction

Nouveaux fichiers :
- `patches/java/forge/ai/CombatTriggerNegativePrune.java`
- `scripts/patch_forge_combat_trigger_prune.py`
- `tests/java/forge/ai/CombatTriggerNegativePruneChecks.java`
- `scripts/audit_v24_combat_prune.py`
- `.github/workflows/four-ai-v24-trigger-prune.yml`

Le patch s'insère **uniquement** dans
`forge.ai.ComputerUtilCombat.combatTriggerWillTrigger`, soit une
**estimation hypothétique d'IA**, et ne touche PAS le moteur des
triggers réels `TriggerHandler` ni la pile Magic.

Quand `-Dbrimaz.fastCombatTriggerNegativePrune=true`, il retourne
`false` avant la vérification `trigger.requirementsCheck(game)`
pour des conditions où le Forge original retourne **déjà toujours
`false` après cette vérification** :
- un attaquant déjà déclaré ne peut pas déclencher une seconde
  prédiction `Attacks` ;
- `Alone` avec plusieurs attaquants prévus ;
- `AttackerUnblocked` alors qu'un bloqueur est présent ;
- `Blocks`, `AttackerBlocked`, `AttackerBlockedByCreature`
  ou `DamageDone` sans carte défensive dans l'hypothèse testée.

**Aucune possibilité précédemment positive n'est volontairement
modifiée.** Le cas de zones, coûts, mots-clés complexes et
`requirementsCheck` demeure géré par Forge lorsque le déclenchement
est possible. La propriété Java reste `false` par défaut ; flag
`-Dbrimaz.fastCombatTriggerTrace=true` pour le nombre de
prédictions négatives réellement évitées à la fin du processus.

Tests : **16 invariants Java** sur les cas négatifs et positifs,
plus jeux A/B réels : pod aristocrates rotation 1 + artefacts rotation 2,
une partie par politique, mêmes seeds/decks, horloge 420 s,
log du nombre de calculs évités. L'audit **refuse un ratio de
vitesse** si les parties ne sont pas toutes deux naturellement
terminées avec exactement les mêmes événements observables.

**Validation statique réussie le 11 octobre :** tag original
`forge-2.0.15`, source upstream SHA
`0c917c4645ad297a487229e3e49db682170d69c3`,
**un seul point d'injection exact**, options A/B présentes,
aucune modification du moteur des triggers dans le helper.

**Validation dynamique non réalisée** à cette étape : nouveaux jobs
Actions https://github.com/Toko177/brimaz-forge-lab/actions/workflows/four-ai-v24-trigger-prune.yml
ont échoué en **2 à 3 secondes, avec `runner_id=0`, zéro
étape et aucun journal téléchargeable**. La cause d'infrastructure
(quota, paiement, indisponibilité de runners, autre) est
**inconnue** ; ne pas présenter ceci comme un échec du Java ni
comme une preuve de compatibilité réelle. Ne pas multiplier
les reruns identiques sans résoudre l'allocation du runner.

## 4. Contournement du blocage Actions : simulateur local

Nouveaux fichiers :
- `scripts/run_local_four_ai.py`
- `tests/test_run_local_four_ai.py`
- [Guide d'utilisation local](RUN_LOCAL_4AI_COMMANDER.md)
- `scripts/analyze_four_ai_timeout_stacks.py`
- `tests/test_analyze_four_ai_timeout_stacks.py`

Le lanceur vise **Windows ou Linux** avec Python et Java 21.
Les entrées sont :
1. le vrai JAR officiel Forge 2.0.15 déjà extrait ;
2. les **sept decks canoniques** issus de l'artefact
   `forge-seven-decks-canonical-verified` (run
   https://github.com/Toko177/brimaz-forge-lab/actions/runs/37966009166)
   + rapport de normalisation de ce même artefact ;
3. un pod ou `both`, 1 à 5 parties par rotation, 1 à 4 JVM
   parallèles, 360/420/480 s d'horloge, un profil Forge
   **identique aux quatre IA**, et une politique sélectionnée.

Le pilote **copie** le JAR avant compilation, valide les sept SHA256,
applique les patchs épinglés et archive chaque sortie réelle sous
`results/local_campaigns/` : vrais logs, manifestes de match,
gagnants naturels ou censures, `provenance.json`,
`tournament.md/json`, chronologie de chaque IA et piles de timeout.
`--preflight-only` vérifie la préparation sans déclencher de
parties ni accéder à GitHub.

**Limite honnête :** le lanceur local n'a pas encore été exécuté
entièrement sur Windows ou Linux ; ses correctifs Java téléchargent
les sources officielles, nécessitant l'accès à GitHub.
Les tests de garde-fous Python sont écrits mais n'ont pas encore
passé la nouvelle CI faute de runner.

## 5. Références de parties réelles à préserver

- [16 vrais jeux V13, 14 naturels, 2 censurés, 1 victoire Brimaz observée](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38089750692).
- [Partie gagnante Brimaz, graine 20830001, artifact rotation 2](https://github.com/Toko177/brimaz-forge-lab/blob/main/docs/REAL_FOUR_AI_BRIMAZ_WIN_REFERENCE.md).
- [Smoke E2E de l'intégration #15 : succès de pipeline, partie censurée à 360 s](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38088096334).
- [V20 : 804 évaluations de ciblage légales, aucun changement
  de meilleure cible causé par la politique V19](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38086336596).

## 6. Consignes impératives pour le prochain chat

1. Vérifier **en premier** la dernière CI V24 et le statut d'allocation
   des runners, puis exécuter localement le test de compilation
   contre le vrai JAR si les runners restent bloqués.
2. **Ne pas activer automatiquement V23/V24** sans benchmark de
   non-régression de règles, de temps et de qualité tactique.
3. Évaluer la proportion des vrais timeouts relevant des prédictions
   du combat vs des scans de capacités statiques ou de remplacement
   (les catégories se chevauchent). Le profiler Java donne les
   piles mais pas une attribution causale automatique.
4. Prioriser ensuite les **choix réellement différents à état public
   identique**, notamment réponse sur pile, budget de décision et
   coût de relance des commandants. Toujours les quatre IA.
5. Utiliser la nouvelle voie locale avec les decks non modifiés
   si GitHub Actions ne démarre plus ; faire d'abord `--preflight-only`.
6. Mettre à jour ce document et le pointeur `NEXT_CHAT_START_HERE.md`
   de `main`, plus PR #17 et la PR d'intégration #15.
7. **Ne pas confondre tests Java, fin naturelle, qualité de stratégie
   et légalité Oracle**. Une victoire observée ou un ratio sur deux
   parties n'est pas un taux réel prouvé.



## 7. Session suivante — voie de validation et comparaison locale complète

**Toujours sur V24 / PR #17, 11 octobre 2026 :**

En raison des jobs GitHub Actions qui échouent avec `runner_id=0`,
aucune nouvelle prétention de victoire ou d'accélération n'est établie.
Plusieurs améliorations d'exploitation ont été ajoutées **au code réel**
mais restent à valider sur machine :

- `scripts/setup_and_run_four_ai.ps1` : lancement Windows depuis le
  clone GitHub, vérification SHA256 de l'archive originale Forge
  2.0.15, extraction du véritable fat JAR, téléchargement via
  `gh run download` des **sept decks canoniques** déjà validés
  dans le dépôt privé, refus d'écraser un deck divergent.
  Pré-requis : `gh auth login`, PowerShell, Python et JDK 21.
- `-PreflightOnly` : vérifier l'installation sans aucun match.
- `-CompileOnly` : appeler
  `scripts/verify_v24_real_jar_compile.py`, patcher une **copie**
  de l'original, contrôler les classes Java injectées dans le JAR,
  confirmer par `javap` la présence de l'appel de V24
  dans `ComputerUtilCombat`, et lancer les 16 invariants Java.
  Ne simule aucun match ; ce test **n'a pas encore été exécuté**.
- `scripts/run_local_four_ai.py` : copie de JAR versionnée mais
  exécution des JVM avec le `--runtime-dir` de Forge d'origine ;
  cela résout la dépendance éventuelle aux ressources du dossier
  d'installation. Le patching ne modifie jamais l'installation
  source. Si un JAR original de confiance est fourni, les
  7 decks/pods/rotations/profils restent identiques pour les
  quatre sièges.
- `scripts/compare_local_four_ai_campaigns.py` : comparaison de
  campagnes **réelles** Forge sur les mêmes graines, 4 rotations,
  deux pods, sept SHA256 de listes identiques, politique/profile/clock
  explicites ; refus des rapports incomplets, de l'asymétrie des
  profils IA et des parties privées de logs. Ratios de vitesse
  uniquement lorsque les deux parties sont naturelles et les
  événements identiques.
  Test de régression :
  `tests/test_compare_local_four_ai_campaigns.py` avec des
  fixtures **SYNTHÉTIQUES, jamais comptées comme parties réelles**.
- `--scryfall-legality-report results/legality/report.json` :
  certification indépendante optionnelle des sorties naturelles
  par `certify_commander_games.py`; discordance entre gagnant
  déclaré et preuves documentaires → erreur, conservation de
  chaque journal. Une partie censurée ne devient jamais un win.
- `--jfr` / `-Jfr` : profilage CPU **par vrai processus Java 21**,
  enregistrement `.jfr` plafonné à 128 MiB, vues
  `jfr view hot-methods` et `thread-cpu-load`, conservation
  des piles d'échantillonnage. Les rapports de vitesse ne sont
  PAS comparables lorsqu'un profilage JFR est activé.
- `scripts/analyze_four_ai_timeout_stacks.py` catégorise les
  véritables piles `AI_EVAL_TIMEOUT_V10` entre combat, triggers,
  statics, remplacements, et indique explicitement que la
  dernière carte visitée **n'est pas une cause CPU prouvée**.
  Test synthétique `tests/test_analyze_four_ai_timeout_stacks.py`.
- `assess_simulator_readiness.py` produit désormais un
  `readiness.json` dans chaque campagne locale. Les
  résultats distinguent la validité de l'exécution, les
  défaites/censures, les quatre sièges actifs et les
  limites de compétence stratégique humaine.

**Documentation détaillée pour le PC Windows :**
[RUN_LOCAL_4AI_COMMANDER.md](RUN_LOCAL_4AI_COMMANDER.md).

**Instruction pratique lors du prochain chat :**
1. Vérifier l'état GitHub Actions / les quotas et les budgets dans
   GitHub Settings → Billing & Licensing → Usage / Budgets →
   Actions pour ce dépôt privé. Les erreurs observées sont
   pré-exécution et peuvent correspondre à divers blocages de
   provisionnement ; **aucune cause de facturation n'est
   confirmée**. Éviter de relancer des jobs sans runner.
2. Si les runners restent indisponibles, lancer sous PowerShell :
   `scripts/setup_and_run_four_ai.ps1 -CompileOnly`, puis
   `-PreflightOnly`, puis `-Pod both -GamesPerRotation 1
   -Policy v17_strict` (8 vrais processus).
3. Comparer la politique `v24_trigger_prune` sur ces mêmes
   graines/decks/profils, rapport A/B par événements et
   censures. Exécuter un petit run `-Jfr` séparé uniquement
   pour l'échantillonnage CPU.
4. **Ne pas fusionner la PR #17**, ni dire que les 16 assertions
   ont réussi, tant que ces tests ne se sont pas exécutés.
5. Conserver la candidate d'intégration **PR #15** et éviter
   d'accumuler des branches spéculatives non testées.
