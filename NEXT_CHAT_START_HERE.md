# REPRENDRE ICI — Brimaz Forge Lab / branche expérimentale V35

**PR #29** : https://github.com/Toko177/brimaz-forge-lab/pull/29
Brancher les travaux sur `feature/v35-strategic-search-20261011`,
depuis `main` consolidée. Les autres anciennes branches expérimentales
ne doivent pas être rouvertes. V35 introduit un planificateur borné de
séquences de 3 sorts sur 2 tours avec maintien de la validation légale
Forge ; lire d'abord [la note V35](docs/V35_STRATEGIC_SEARCH.md).
Résultat de qualité IA non démontré tant que les véritables A/B
et journaux d'interventions ne sont pas inspectés.

## Vérification « mieux que Forge original »

`v17_strict` est une IA déjà modifiée par nos scripts,
**pas l'original**. `forge_stock` est désormais le seul comparateur
strictement byte-identique au JAR officiel. Les A/B de politiques
uniformes par quatre sièges ne constituent pas un duel direct. La
validation d'une IA meilleure doit inclure des parties avec politiques
mixtes, des nombres de parties suffisants et des résultats naturels
non censurés. Le benchmark stock-vs-V35 actuel n'a aucune conclusion
de qualité tant qu'il n'est pas complet.

## Nouveau protocole sièges mixtes

`v35_brimaz_duel` : seules les décisions de Brimaz reçoivent V35,
les trois autres sièges restant sous V17 dans la même partie.
La CI matrice sépare aussi les comparaisons stock Forge original
contre V35 généralisée. Ce duel ne prouve pas une supériorité
sur Forge original, mais il isole mieux l'effet de Brimaz V35.

## Incidents réels du benchmark stock / V35

Voir `docs/V35_STRATEGIC_SEARCH.md` : 2 jobs réussis, 2 échoués
sur #38136545704 ; V17 échoue sur la création concurrente de
`~/.forge/decks/planar`, le Forge strictement original sur des NPE
de `SpellAbility.getActivatingPlayer()`.
La nouvelle référence `forge_stock_compat` conserve le scoring AI
officiel et applique le seul hotfix commun `CharmEffect`; elle n'est
**pas un JAR stock byte-identique**.
Le nouveau benchmark et sa preuve devront être vérifiés séparément.

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

## Campagne répliquée 32 JVM : conclusion négative / non démontrée

[CI #38139342755](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38139342755) :
trois groupes exploitables (11 paires naturellement terminées), un
groupe en échec. Stock Forge + Charm fix : Brimaz 0 victoire dans
les deux bras sur 7 paires valides. Duel Brimaz V35 sur pod Artifact :
1 victoire V17 et 0 V35 sur quatre paires.
`aristo/v17_strict` a une JVM rotation 0 sans log d'actions.
**Aucune démonstration que V35 est supérieure à Forge.**
Lire `docs/V35_STRATEGIC_SEARCH.md` pour les censures et la méthode.

## Challenger V36 (non fusionné)

La version `v36_brimaz_challenger` utilise
`patches/java/forge/ai/MultiplayerEvidenceGateV36.java`.
Futur connu uniquement, contrôles de coût Forge, repli stock sur les
situations sans preuve locale. Les adversaires sont strictement
V17 inchangés. Benchmark sur nouvelles graines `20270131`,
voir `docs/V35_STRATEGIC_SEARCH.md`. Une compilation réussie ne
constitue pas une preuve de victoire ou d'amélioration.

- V36: voir `docs/V36_EVIDENCE_POLICY.md` ; défaut majeur détecté : le planificateur V17 forçait déjà Brimaz sans évaluer les dégâts cumulés des créatures ennemies. V36 supprime cette priorité automatique sous forte pression, sans inventer de résultat de combat. L'abstention revient à la base V17, **pas** à un Forge pur.

## V38 — activation réelle des Incubateurs

La V37 ne produit AUCUN sacrifice approuvé sur les 16 parties du
premier miroir réel (#38149374175). L'une des raisons possibles
identifiées dans la logique : une unité Incubator non transformée n'est
pas une créature ; nos anciens automatismes de transformation
étaient désactivés pour l'A/B. V38 (`MultiplayerIncubatorTempoV38`)
sélectionne uniquement une vraie capacité Forge de transformation
payable en phase principale 2, sous condition d'effectif / taille /
menace. Les miracles et moteurs adversaires ne sont pas imaginés.
Un nouveau protocole direct est lancé avec graines 20270903.

## V39 — synthèse des derniers tests et hypothèse de décision

V38 (#38152203947), 32 vraies parties miroir : 31 naturelles ;
les 16 miroirs « quatre Brimaz identiques » donnent 8 victoires
challenger et 8 référence. Le pod artifact/aristo ne modifie
**aucun des quatre decks de ces miroirs** : seule la famille des
graines change. Kaal (15 parties naturelles) : V38 4 victoires,
référence 0, Kaal 11. Les sacrifices V38 approuvés restent à zéro,
les transformations Forge réelles sont observées.

V39 : `MultiplayerIncubatorEngineV39` ajoute les bénéfices
observables d'un sacrifice de petite créature phyrexiane et
une règle de préservation du mana pour le ramp payable de la main.
Un nouveau benchmark hors échantillon (seed 20271119)
réplique les miroirs avec 3 répétitions par rotation/pod et
les parties d'évaluation 4AI. Seuls les résultats réels comptent.

## V40 — corrections d'isolation et résultats V39

[V39 CI #38154331237](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38154331237)
termine ses 6 jobs, 8–12 dans vingt miroirs Brimaz identiques,
2–1 en duel Brimaz avec Kaal (21 parties naturelles), et
0–2 dans les autres campagnes appariées (6 paires exploitables).
Ceci **ne prouve pas une IA supérieure**.

V40 `v40_brimaz_challenger` corrige le verrou `latestTurn`
global partagé entre plusieurs IA et le fait de consommer
l'activation à la proposition, même rejetée. Log d'approbation
`FOUR_AI_V40_TRANSFORM_APPROVED_BY_SEAT`. Le compteur diagnostic
de sacrifice devient aussi par joueur. Conserver la PR en draft,
sans modifier les decks.
