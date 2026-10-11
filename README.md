**Deckbuilding avec une seule IA V43 à chaque rotation (opt-in).**
Le pipeline de decklists accepte `V43-single-seat-generic` à côté de
la référence V13. Le pilote ciblé suit le siège de la liste évaluée
et les trois adversaires conservent Forge. Le cache de référence refuse
tout mélange de politiques et identifie les sources Java compilées.
[Guide utilisateur](docs/DECKBUILDING_QUICKSTART.md).

**V43 — comparaison directe contre Forge.**
Le mode `v43_commander_single_seat` active l'IA générique pour
un unique joueur par partie et maintient trois adversaires contrôlés
par la politique Forge de référence. Les rotations couvrent plusieurs
decks et un audit vérifie chaque identité `Ai(n)-Name=`.
L'ancien mode V42 sur les quatre joueurs mesure seulement l'intégration
multideck. [Protocole et limites](docs/V42_GENERAL_COMMANDER_AI.md).

**V43 — fiabilisation des traces de vraies parties (sans nouveau workflow).**
Les premiers benchmarks génériques ont révélé le format des identifiants
réels `Ai(n)-Name=` dans Forge, différent des fichiers de decks.
L'audit confirme maintenant strictement le siège et le label du deck,
et les politiques historiques distinguent cette erreur d'un échec
stratégique. Le planificateur ne confond plus valeur de mana imprimée
et coût réellement payable. [Constats et retests](docs/V42_GENERAL_COMMANDER_AI.md).

## V42 — vers une IA Commander générique (expérimental)

Le nouveau mode `v42_commander_general` utilise un évaluateur fondé sur
le plateau public, les ressources et les capacités Forge réelles : **pas de
liste de cartes ou d'identité Brimaz dans ses règles de décision**.
Il peut s'activer pour les quatre joueurs, quel que soit leur commandant.
Le comparateur `v37_stock_control` partage le même Forge patché mais
n'active pas V42. Tests et benchmark A/B avec sièges Kaal + Brimaz :
[architecture, commandes et limites](docs/V42_GENERAL_COMMANDER_AI.md).

**Important :** c'est une première base générique pour les permanents
non ciblés, pas encore une IA complète de combat, interaction sur la pile,
combos ou évaluation probabiliste de decklists. Les statistiques de victoire
ne valent rien avant les vrais journaux et les audits d'actions approuvées.

**Audit du moteur de sacrifice V41 :** chaque partie réelle produit
désormais un diagnostic automatique des raisons pour lesquelles
Brimaz ne transforme pas ou ne sacrifie pas ses jetons.
Ce diagnostic distingue la présence du commandant, des jetons
Phyrexian *déjà créatures*, les exutoires activables et les décisions
réellement approuvées par Forge. Il évite de transformer une simple
proposition en victoire supposée.
[Documentation et limites](docs/V36_EVIDENCE_POLICY.md).

**V41 — correction du vrai pilote Brimaz et accès contrôlé aux sacrifices.**
Le module précédent ne transformait les Incubateurs que dans les miroirs :
`Brimaz_V3`, le siège canonique contre Kaal, était exclu.
V41 répare cette isolation et prend en charge les véritables capacités
d'Ashnod's Altar et de Phyrexian Altar, avec validation de Forge,
sans débrider les capacités ciblées ou celles des adversaires.
[Résultats historiques et méthode](docs/V36_EVIDENCE_POLICY.md).

**V40 : défaut critique d'isolation entre joueurs corrigé.**
V38/V39 partageaient un verrou de transformation entre les deux
joueurs challengers d'une même partie, et consommaient ce verrou
dès la proposition plutôt qu'après approbation par Forge.
V40 suit l'approbation par identité de joueur/numéro de tour,
et expose les diagnostics de sacrifice pour chacun.
[Analyse empirique et protocole](docs/V36_EVIDENCE_POLICY.md).

**V39 (expérimental) :** gestion contextuelle des Incubateurs. Un petit jeton n'est transformé pour préparer un sacrifice que si Brimaz et un vrai moteur de sacrifice sont présents et que la prolifération des compteurs visibles compense sa perte. Le planificateur évite également de consommer le mana d'un accélérateur immédiatement payable, sauf urgence défensive. Toujours contrôlé par les règles et les coûts de Forge. [Protocole et mesures](docs/V36_EVIDENCE_POLICY.md).

**V38 — changement concret de gameplay :** les Incubateurs ne sont pas des créatures tant qu'ils ne sont pas transformés. Le challenger peut maintenant activer sélectivement une transformation légale en phase principale 2, par les vrais coûts Forge, pour créer de véritables bloqueurs/attaquants et alimenter les synergies Phyrexian. Le contrôle original ne reçoit pas cette politique. [Code et protocole](docs/V36_EVIDENCE_POLICY.md).

**Nouvelle validation directe V37 :** deux decks Brimaz strictement identiques
(à l'exception de leur nom) jouent dans **une même partie Forge** :
l'IA V37 affronte la référence sur les mêmes cartes, règles, tirages globaux
et adversaires. Les copies sont temporaires et les 7 decks canoniques
ne sont jamais modifiés. Le test ne certifie une amélioration qu'avec
des résultats naturels répétés sur plusieurs graines.
[Protocole](docs/V36_EVIDENCE_POLICY.md).

[V36 policy and exact inherited V17 vs Forge distinction](docs/V36_EVIDENCE_POLICY.md).

**V36 — challenger à décision conditionnelle :** désormais un moteur
expérimental réel, branché sur Forge 2.0.15, n'intervient que pour des
ordonnancements Brimaz/Phyrexian ou un déverrouillage de mana démontrable
sur les cartes connues, et vérifie le paiement par le moteur Forge.
Sans avantage local suffisant, elle laisse décider Forge.
La qualité compétitive reste à mesurer, séparément de la compilation.
[Documentation V36](docs/V35_STRATEGIC_SEARCH.md).

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

**Nouveau banc d'essai avec sièges mixtes :** l'option
`v35_brimaz_duel` active le nouveau planificateur uniquement pour
Brimaz, laissant les trois autres IA sur une référence V17 identique.
C'est un test compétitif plus proche d'un véritable duel, distinct
de la comparaison au JAR Forge original non modifié.

**Contrôle expérimental avec stabilité vérifiée :**
`forge_stock_compat` utilise l'IA Forge originale avec uniquement un
correctif commun de contexte `CharmEffect`, distinct de `forge_stock`
qui conserve le JAR strictement original. Le benchmark précédent a
échoué sur une initialisation concurrente du profil et des NPE du
moteur stock, pas sur une différence de victoires probante.

**Évaluation scientifique corrigée :** la campagne de référence `v17_strict`
n'utilisait pas Forge d'origine. Le protocole vérifiable
`forge_stock` conserve désormais le JAR originel byte-à-byte
(aucun patch, aucune propriété spécifique). Le nouveau benchmark
sépare résultats naturels et censures, victoires de Brimaz, taille de
l'échantillon et incertitude. **Aucune supériorité IA face à Forge stock
n'est revendiquée avant mesure suffisante.**
[Limites méthodologiques](docs/V35_STRATEGIC_SEARCH.md).

**Dernier benchmark (32 JVM planifiées, #38139342755)** :
trois groupes réussis, **11 paires naturelles analysables**, et
un groupe bloqué par un journal Forge manquant. La comparaison à IA
Forge stock + correctif technique ne montre **aucune victoire Brimaz
dans les deux bras sur 7 paires exploitables** ; le duel Artifact
donne **V17 1 — V35 0** sur quatre paires. Aucun gain prouvé.
[Rapport détaillé](docs/V35_STRATEGIC_SEARCH.md).

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
