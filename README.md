# Brimaz Forge Lab

Simulateur **Magic: The Gathering Commander à quatre IA** avec le vrai moteur
[Forge 2.0.15](https://github.com/Card-Forge/forge), Java 21, parties
indépendantes, sept decks canoniques épinglés par SHA256, journalisation,
certification et comparaisons de politiques.

## Brimaz V4 B3 — victoire par le board, pas les cartes « auto-include »

**Liste Commander de 100 cartes pour le playgroup Bracket 3.**
Plan principal : **Incubation → prolifération des marqueurs →
transformation des Phyrexians → anthems/évasion → dégâts de combat**.
Le drain est secondaire. La construction évite volontairement les
staples génériques chers ou socialement oppressifs (Esper Sentinel,
Urza's Saga, Phyrexian Altar, Diabolic Intent, The Meathook Massacre),
remplacés par des outils qui dépendent du plan Brimaz :
**Phyrexian Rager, Steel Overseer, Lightning Greaves,
Phyrexian Awakening, Command Beacon**.
**Mondrak et Yawgmoth** restent des exceptions chères mais
fortement synergiques, sans plafond de prix rigide.
La V4 comporte **23 différences nettes** par rapport à V3 ;
la V3 et les sept DCK originaux ne changent pas.
La V4 bénéficie désormais aussi d'un **inventaire de l'ensemble des
12 763 cartes Commander légales Orzhov/incolores sans Game Changer**
sur 38 751 Oracle examinées. Trois corrections défensives issues
de cette recherche : **Sunder the Gateway**, **Stroke of Midnight**
et **Phyrexian Scriptures**.
Après le benchmark réel du playgroup, trois ajustements supplémentaires corrigent le **goulet de mana pour payer {2} par Incubateur** et les pertes de valeur après wrath : **Everflowing Chalice, Steel Overseer, Scrap Trawler** remplacent Anointed Procession, Aron, Benalia's Ruin et Activated Sleeper. Les autres cartes de combat, de protection et d'interaction sont conservées. Mondrak reste le multiplicateur de jetons Phyrexian.
**Révision du 13/10 : dépendance au commandant** —
Sculpted Perfection, Phyrexian Rager, Selfless Spirit,
Lightning Greaves et Command Beacon rendent le développement
moins conditionnel à un Brimaz vivant et facilitent sa protection/
relance. [Audit détaillé avec pièges de règles](docs/BRIMAZ_COMMANDER_DEPENDENCY_REVIEW_2026-10-13.md).
Pas de poison ou d'infect dans la V4 actuelle.
**La V4 n'est pas démontrée supérieure en partie.**

- [V4 importable Moxfield / Archidekt](decks/Brimaz_V4_B3.txt) ;
  [V4 Forge DCK](deck_candidates/Brimaz_V4_B3.dck).
- [Les 23 changements et le plan de jeu](docs/BRIMAZ_V4_B3_DECISIONS.md) ;
  [les 100 cartes individuellement](docs/BRIMAZ_V4_B3_CARD_BY_CARD.md) ;
  [audit de dépendance à Brimaz](docs/BRIMAZ_COMMANDER_DEPENDENCY_REVIEW_2026-10-13.md).
- [Benchmark de six decks budget du playgroup (KaalDeagle)](docs/BRIMAZ_KAAL_PLAYGROUP_BENCHMARK_2026-10-12.md) : budgets, ramp, interaction, protection, moteurs et pistes de tests.
- [Politique playgroup / auto-includes / prix sourcés](docs/BRIMAZ_V4_B3_SOCIAL_BUDGET_POLICY.md) ;
  [les 78 cartes considering](docs/BRIMAZ_CONSIDERING_AUDIT_2026-10-12.md) ;
  [recherche exhaustive du pool Oracle actuel](docs/BRIMAZ_FULL_ORACLE_POOL_2026-10-12.md).
- `python3 tests/test_audit_brimaz_v4.py` vérifie les 100 cartes
  et les 23 changements. Les probabilités de cartes vues ne sont
  **pas** des simulations de parties ni une preuve de winrate.
- Vérifier Oracle / Game Changers en direct avec
  `.github/workflows/commander-legality.yml` avant achat.

## Groupes de parties — mise à jour du 12 octobre 2026

**Amalia est remplacée dans le groupe artifact par Dungeon Party Time**,
une des sept listes déjà épinglées. Brimaz, Lathril, Urza et Dungeon
Party Time composent désormais ce groupe. Le groupe aristo ne change
pas. Les sept fichiers DCK restent strictement identiques et Amalia
n'est pas supprimée. Les deux groupes partagent désormais Dungeon ;
leurs archives et résultats antérieurs ne doivent pas être mélangés
avec les nouveaux.
[Compositions, source de vérité et règles de comparaison](docs/ACTIVE_COMMANDER_PODS_2026-10-12.md).

## Politique active et parcours utilisateur

Le moteur Commander **V43 expérimental** propose des décisions de
développement non ciblées à partir du plateau public et des capacités Forge
réelles, sans règles spécifiques à Brimaz. Les sorts, paiements, combats et
résolutions restent régis par Forge 2.0.15. **Ce moteur n'est pas encore
une IA Commander de niveau humain.**

- **Tester une liste** : la comparaison A/B de decklists conserve V13 par
  défaut ; elle propose `V43-single-seat-generic` en option. Le pilote suit
  le siège du deck évalué lors des quatre rotations, avec trois adversaires
  Forge inchangés. [Guide deckbuilding](docs/DECKBUILDING_QUICKSTART.md).
- **Comparer une IA à Forge** : `v43_commander_single_seat` active
  exactement un challenger par partie, contre trois références, pour
  évaluer le logiciel indépendamment des changements de cartes.
  [Protocole et limites](docs/V42_GENERAL_COMMANDER_AI.md).
- **Traçabilité** : les noms réels `Ai(n)-Name=` sont rapprochés
  strictement des fichiers DCK, les actions approuvées sont séparées
  des résolutions, les censures ne deviennent jamais des victoires.
  Le cache SHA256 interdit le mélange V13/V43 ou de sources Java.
- **Historique V35 à V41** : conservé dans
  [les preuves expérimentales](docs/V36_EVIDENCE_POLICY.md) et dans Git,
  sans accumulation d'annonces de versions dans cette page.

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
