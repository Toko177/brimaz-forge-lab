# Brimaz Forge Lab

Projet : simulation réelle de Magic: The Gathering Commander à **quatre IA Forge 2.0.15**, avec contrôle de légalité des 100 cartes, parallélisation GitHub Actions, audit des décisions IA et certification des parties.

## Point d'entrée pour reprendre le projet

**[PASSATION ACTIVE — état post-V8, V9, CI, limites et prochaines actions](docs/PASSATION_ACTIVE_2026-10-10.md)** — à consulter en premier lors d'un nouveau chat. Informations vérifiées, liens GitHub Actions, scripts, contrôles de règles, historique non reproductible et protocole de continuation.

**[Lire le rapport de transmission intégral du 9 octobre 2026](docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md)** — **447 lignes**, contexte, architecture, scripts, données, chronologie chiffrée, limites, bugs corrigés, V1–V6, première victoire de Brimaz, liens vers les actions et étapes prioritaires.

Documentation spécialisée :
- [Postmortem des 32 parties et victoire historique non reproduite](docs/canonical-postmortem-and-first-win.md)
- [Règles et critères de validité](docs/realism-protocol.md)
- [Qualité de l'IA et parallélisme](docs/ai-quality-and-parallelism.md)
- [Architecture du futur lookahead à quatre joueurs](docs/multiplayer-lookahead-roadmap.md)

## Mise à jour du 9 octobre 2026 : victoire historique non reproduite

**Attention :** la première victoire Brimaz (seed `20291010`, seuil moteur 360 s)
a satisfait la certification de sortie naturelle et de légalité, mais une
relecture avec seuil 900 s, IA Forge Default, mêmes cartes et sièges, a donné
**Radha vainqueur** (437 493 ms). La première divergence est au tour Forge 33,
sur un choix de donjon effectué par une IA adverse. L'horloge seule n'est
pas une cause démontrée ; la seed Forge n'assure pas ici une trace déterministe.
Ne pas compter la victoire historique comme résultat reproduit ni comme
preuve de performance de Brimaz.

[Comparaison forensique des journaux](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37994894861).
[V7 observateur : 4 parties certifiées, 0 victoire Brimaz](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37992540124).
V8 expérimente des transformations défensives d'Incubateurs, toujours
sous le moteur de règles Forge.

## Comparer et améliorer rapidement ses decks Commander

Le nouveau pipeline de **deckbuilding A/B** évite de créer une version Java/Forge pour chaque échange de cartes. Il prend deux listes de 100 cartes, vérifie leur légalité avec Scryfall et les confronte à trois véritables IA sur 4 sièges × 2 groupes d'adversaires. Il certifie indépendamment les journaux Forge et publie winrates, incertitude statistique, censures et erreurs de décision IA.

- **[Mode d'emploi : comparer des decklists en 16, 32, 64 ou 96 parties](docs/DECKBUILDING_QUICKSTART.md)**
- **[Modifier la liste candidate Brimaz](decks/Challenger.txt)** sur la branche expérimentale, puis commiter pour lancer automatiquement la campagne à 16 parties (sans fusionner la PR).
- **[Workflow de deckbuilding A/B](.github/workflows/deckbuild-ab.yml)** : 16 jobs Forge parallèles, Scryfall obligatoire, option future de saisir des swaps directement en lancement manuel lorsque le workflow sera disponible sur la branche par défaut.
- **[Tests de l'outil A/B](.github/workflows/deckbuild-regression.yml)** : contrôle du nombre de cartes, commandant, SHA256, vrais résultats et intervalles de confiance.

Une comparaison A/B où les deux listes sont initialement identiques est un **test de fonctionnement**, pas un progrès du deck. **[Premier test réel A/A : SUCCESS, 16/16 parties naturelles certifiées](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38004900250)**, 0/8 victoires dans chaque bras, aucune censure, zéro timeout IA, deux replis d'attaque. C'est le bon résultat pour vérifier le pipeline, pas une mesure utile de progression des cartes. Le résultat V12 1/31 reste l'échantillon indépendant de référence, et le V13 1/14 ne démontre pas une compétence supérieure de l'IA.

## Résultat certifié et expérience V13

- **V12 : 31/32 parties naturelles certifiées, 1 vraie censure, 1 victoire Brimaz** ; taux observé **3,23 %**, Wilson 95 % **0,57 à 16,19 %**, sans généralisation au Commander humain. [Rapport et certificats indépendants](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002649987).
- **21/31 parties naturelles sans avertissement IA surveillé**, dont l'unique victoire Brimaz (seed `20610001`, adversaires éliminés à 0 PV, sans timeout ni repli d'attaque).
- **33 dépassements IA**, dont 32 profils de calcul profond de combat ; le frein majeur n'est plus le premier lancement de Brimaz (31/31 parties naturelles, médiane tour personnel 4).
- Correction : les pertes à **21 blessures de commandant** étaient rejetées à tort par l'ancienne certification ; désormais correctement reconnues. [81 tests de régression réussis](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002628580).
- [Audit de reproductibilité des 32 graines répétées](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002258622) : 25/32 mêmes séquences d'événements suivis ; 1/30 paires naturellement finies change de vainqueur. Ne pas compter ces répétitions comme des graines indépendantes.
- **V13** : [pilote 16 matchs sur 8 jobs](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002838904), conservation du support Incubate avec délai de réflexion **partagé** entre quatre IA, adapté 5→10→15 s après timeouts. Aucun gain de compétence ni winrate n'est proclamé sans les résultats.

## Campagne de validation V12 à 32 parties

- [Campagne V12 équilibrée à 32 véritables parties](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38001534517) : **16 jobs Github Actions, 12 simultanés maximum**, 2 pods × 4 sièges × 2 séries de graines préenregistrées × 2 parties.
- Les taux de victoire utilisent exclusivement les certificats indépendants des journaux Forge, avec **intervalles de Wilson 95 %**, répartition par pod/siège, rejets, censures et exceptions d'IA. Une sortie `status=complete` du lanceur ne suffit pas à accepter une victoire.
- `scripts/audit_balanced_commander_campaign.py` impose 32 traces, 32 empreintes SHA256, 32 certificats, la rotation équilibrée et des graines distinctes. `tests/test_balanced_commander_campaign.py` protège ces invariants.
- Le premier lancement [38001496914](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38001496914) utilisait déjà les mêmes 32 graines mais contenait une assertion d'audit finale erronée (4 logs attendus au lieu de 32). Il sert de répétition technique : **ses résultats ne doivent pas être additionnés comme 32 graines indépendantes supplémentaires**. `scripts/audit_same_seed_campaign.py` permettra de comparer les divergences réelles sur les mêmes parties.
- Les workflows sont asynchrones sur GitHub : consulter les jobs terminés et la [passation active](docs/PASSATION_ACTIVE_2026-10-10.md) pour connaître l'état vérifié, sans déduire le winrate d'une campagne encore partielle.

## État V10–V12 (10 octobre 2026)

- **Première victoire Brimaz V10 indépendante des anciennes expériences** : seed `20281010` (aristo, siège 3), fin naturelle à **164,227 secondes**. Les quatre issues sont présentes : Brimaz survit, deux adversaires perdent à 0 PV, un troisième à bibliothèque vide. [Certification stricte 4/4 résultats, 1/4 Brimaz](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38000153841).
- Cette victoire comporte **4 dépassements du délai de réflexion IA** et une déclaration d'attaque invalidée puis corrigée par Forge : ce n'est ni une mesure du winrate réel, ni la preuve d'un gain de stratégie V10 (observation seule).
- V11 : [4/4 parties certifiées, 2 timeouts, Brimaz 0/4](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999839503), budget IA adaptatif équitable 5→10→15s : expérimental, pas un gain démontré.
- V12 : [gestionnaire IA natif d'Incubate en cours de tests](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38000469712), mêmes règles pour les quatre IA.
- Les scripts de contrôle reconnaissent désormais les pertes par bibliothèque vide `has lost trying to draw`, tout en exigeant quatre résultats cohérents, et publient les causes d'élimination sans inventer la causalité des kills.
- **[Passation active à jour](docs/PASSATION_ACTIVE_2026-10-10.md)** pour reprendre toutes les expériences et le développement dans un nouveau chat.

## Résultat actuel à ne pas mal interpréter

- 32 parties canoniques avant correction moteur : 29 naturelles certifiées, 3 censurées ; Brimaz 0/29.
- Correction ciblée du bug Forge `CharmEffect`, puis **une victoire Brimaz historique non reproduite** sur graine de régression, à 356,476 secondes : [résultat d'origine](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744) et [replay divergent à 900 secondes](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37994894861).
- Cette victoire ne mesure pas encore le taux de victoire du deck ; la priorité reste la qualité du pilotage IA et l'audit des règles.
- V5/V6 sont des pilotes d'amélioration de l'IA, sans gain de winrate démontré.

## Développement post-V8

- [Calibration des tours personnels et des ouvertures Commander](docs/EDH_EMPIRICAL_PACING_AND_AI_CALIBRATION.md) : 4 parties V8, 2 sorties mana faibles, médiane 13 tours du joueur le plus actif, face à 9 rotations médianes humaines.
- [Audit des parties réelles V8](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37997796527) : 5 tests réussis, 4/4 parties naturelles.
- [V9 — choix de mulligan prudent propre à Brimaz](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37998385269) : tests et parties pilotes, vérifier les logs avant de conclure à un gain.
- **Ne pas confondre qualité des règles, qualité de l'IA et taux de victoire.** N'importe laquelle de ces dimensions peut invalider une mesure de winrate.
