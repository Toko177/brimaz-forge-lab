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

## V41 — contrôle de l'identité des pilotes et des sacrifices

Dernier verdict V40 : [campagne #38166387534](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38166387534)
— 11–10 en vingt-et-un miroirs naturels à quatre Brimaz,
0–1 en vingt parties naturelles contre Kaal, et 0–1 dans les
sept paires naturelles des campagnes appariées. Pas de gain prouvé.

V41 corrige une vraie erreur : la transformation des Incubateurs
reconnaissait seulement `Brimaz Challenger`, pas `Brimaz_V3`.
Elle active aussi une liste strictement contrôlée de sacrifices
sur Ashnod's Altar et Phyrexian Altar, et sépare nettement les
jetons phyrexians créatures des Incubateurs non transformés.
Les nouveaux tests sont dans
`tests/java/forge/ai/MultiplayerSacrificeAccessV41Checks.java`.
Prochain benchmark sur graines `20280409`, non fusionné.

## Correction du pilote V41 : contrôle des identifiants des sièges

Le run [#38170566763](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38170566763)
a révélé 258 fenêtres non autorisées (sur 258) contre Kaal.
Cause : nom d'affichage `Brimaz Challenger A` différent du
deck ID `Brimaz_Challenger_A`. La liste d'identités est corrigée,
la télémétrie rejette désormais les résultats avec mauvais pilote,
et les deux autels sont comptés sous V41. Graines de retest
`20281019`. Lire `docs/V36_EVIDENCE_POLICY.md`.

## V43 — identité réelle des pilotes Forge et coût réel

La campagne V42 historique [#38175519441](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38175519441)
a exécuté 16 JVM réelles, 7/8 paires naturellement terminées, mais
l'audit échouait en comparant `Ai(n)-Name=` aux IDs `Kaal_...`.
La V43 ajoute `scripts/forge_seat_identity.py`, un mapping strict
et vérifié contre les 7 decks originaux. Cela corrige V41 et V42
sans désactiver les contrôles. Elle cesse aussi de rejeter une carte
Forge-payable sur la seule base de son CMC imprimé.
Les nouveaux tests sont dans `tests/test_forge_seat_identity.py`
et dans les tests Java V41/V42. Graines 20261213/20261217.
Pas de victoire supérieure revendiquée. Conserver une seule PR draft.

## V43 — évaluation contre trois contrôleurs Forge

Le mode `v43_commander_single_seat` modifie seulement Ai(1) dans
chaque partie ; les autres sièges utilisent la référence Forge et
le banc d'essai tourne quatre positions sur plusieurs decks.
`audit_v42_generic_commander.py` contrôle les identités et les
victoires spécifiques du challenger sur les parties naturelles.
Graine indépendante `20261221`. Documentation détaillée :
`docs/V42_GENERAL_COMMANDER_AI.md`. PR unique, toujours draft.

## Connexion V43 au deckbuilding (opt-in)

Le pipeline `deckbuild-ab.yml` prend maintenant un choix
`ai_policy` entre `V13-incubate-adaptive` (défaut inchangé)
et `V43-single-seat-generic`. En V43 le siège-candidat suit la
rotation des 4 joueurs ; les trois Kaal restent sur Forge.
`deckbuild_run.py` marque une partie `policy_unverified` si
aucune décision V43 n'apparaît réellement, et `policy_fault`
si V43 touche un adversaire. L'archive et le certificat
conservent ces censures, jamais traitées en défaites ou victoires.

`deckbuild_cache.py` v2 est maintenant conditionné par la
politique et les SHA256 des vraies classes Java compilées, afin
qu'aucune référence V13 ne soit réutilisée en V43.
Tests : `test_deckbuild_pipeline.py`, `test_deckbuild_cache.py`.
Guide : `docs/DECKBUILDING_QUICKSTART.md`. Garder PR #29 draft.

## 12/10/2026 — remplacement d'Amalia dans les groupes actifs

L'utilisateur demande un autre adversaire issu de la liste existante
à la place d'Amalia. Le groupe artifact devient : Brimaz_V3,
Kaal_23328062 (Lathril), Kaal_11485202 (Urza) et Kaal_10347090
(Dungeon Party Time). Le groupe aristo conserve Radha, Dungeon,
Zimone/Dina. Les 7 fichiers DCK canoniques restent intacts ; Amalia
est exclue des matchs futurs, pas de l'archive. **Dungeon est donc
partagé entre les deux groupes**, jamais deux fois dans un match.
`scripts/commander_pods.py` est la source unique des pods actifs.
Ne jamais attribuer les résultats des anciennes parties Amalia à
Dungeon ; nouveaux runs/retests nécessaires. Doc complète :
`docs/ACTIVE_COMMANDER_PODS_2026-10-12.md`.

## 12/10/2026 — objectif de la V4, état le plus récent

L'utilisateur veut une liste Brimaz pour gagner **par le board et
les dégâts de combat** (Incubateurs transformés, marqueurs +1/+1,
prolifération, vol, anthems), **pas** par le drain.

Préférence sociale explicite : éviter autant que possible les
cartes génériques chères et individuellement écrasantes
comme Esper Sentinel, Rhystic Study ou Smothering Tithe.
Pas de plafond budgétaire strict ; Mondrak et Yawgmoth peuvent
rester car leur synergie avec Brimaz est exceptionnelle.

Dans la V4 actuelle, cinq dernières substitutions :
Esper Sentinel -> Gixian Infiltrator ;
Phyrexian Altar -> Aron, Benalia's Ruin ;
Diabolic Intent -> Resourceful Defense ;
The Meathook Massacre -> Phyrexian Awakening ;
Urza's Saga -> Vault of the Archangel.
**16 changements nets V3->V4**. V3 contenait déjà Vault :
elle reste finalement présente, War Room remplace donc Urza's Saga
dans la comparaison nette V3/V4.
Voir `docs/BRIMAZ_V4_B3_SOCIAL_BUDGET_POLICY.md`,
`docs/BRIMAZ_V4_B3_DECISIONS.md` et
`decks/Brimaz_V4_B3.txt`.

Tous les sept DCK canoniques restent SHA256 inchangés.
Aucune preuve de winrate V4 par jeu réel ou humain.
Ne pas repartir sur une IA V44 sans démonstration réelle.
