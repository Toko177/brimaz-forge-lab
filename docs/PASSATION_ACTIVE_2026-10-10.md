# PASSATION ACTIVE — Brimaz Forge Lab / quatre IA Commander

Dernière édition : **10 octobre 2026**, après ajout de la politique V9
(mulligan conservateur) et lancement des workflows associés.

> LIRE CE DOCUMENT AU DÉBUT DU PROCHAIN CHAT, PUIS CONTRÔLER L'ÉTAT ACTUEL
> DES GITHUB ACTIONS. Il complète (ne remplace pas) le rapport historique
> \`docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md\` et la calibration
> \`docs/EDH_EMPIRICAL_PACING_AND_AI_CALIBRATION.md\`.
> L'état de GitHub prévaut sur le statut de jobs indiqué à la date ci-dessous.

## 1. Objectif utilisateur et règles NON NÉGOCIABLES

Le propriétaire du dépôt \`Toko177/brimaz-forge-lab\` veut optimiser sa
**liste Brimaz V3 de 100 cartes**, légalement en EDH et dans un cadre
Bracket 3 sans Game Changers, avec un simulateur **réel, piloté par quatre
IA jouant les règles Magic**, et un taux de victoire objectif **>= 20%**.
Ce 20% est une *hypothèse à mesurer*, jamais une cible autorisant
une manipulation des résultats. Les 3 autres IA doivent être également
intelligentes; les parties doivent conserver les mêmes règles Magic.
Ne jamais simuler simplement des distributions de mains, attribuer
des victoires artificielles, modifier le deck adverse, réduire les PV,
introduire du poison absent de la V3, ou compter des fins censurées.
L'objectif est d'obtenir une évaluation honnête, reproductible dans
la mesure du possible, avec les biais explicitement identifiés.

Le propriétaire souhaite que l'assistant **modifie lui-même le repo GitHub
et exécute les expériences Actions**, sans redemander les coordonnées du
projet. Toujours contrôler résultats et logs avant d'affirmer
une amélioration.

Repo : https://github.com/Toko177/brimaz-forge-lab
Branche active : \`improve/realism-and-ai-diagnostics\`
PR **#1** : https://github.com/Toko177/brimaz-forge-lab/pull/1
Laisser **en brouillon** tant que la validité / les comparaisons sont
insuffisantes; \`main\` n'a pas reçu cette branche expérimentale.
Ne PAS effacer \`docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md\`.

## 2. État du simulateur et corpus

- Forge **2.0.15**, JAR Java 21 officiel installé en Actions; archive Forge
  release SHA256 attendue :
  \`4468f182b60f6ca62d89697baa208981085af744f116781af751c611826db600\`.
- \`scripts/patch_forge_charm_context.py\` : correction ciblée d'une NPE
  \`CharmEffect\` liée au contexte d'activation manquant.
- Sept decks distincts légaux reconnus par Forge et Scryfall; copies
  normalisées et HASH-PINNÉES depuis le workflow de validation
  **37966009166** et audit de légalité **37965067128**.
- \`decks/Brimaz_V3.txt\` : la liste originale **ne doit pas être modifiée
  secrètement**. Commander \`Brimaz, Blight of Oreskos\`.
- Pods :
  - \`aristo\`: \`Brimaz_V3\`, \`Kaal_9594008\` (Radha),
    \`Kaal_10347090\` (dungeon), \`Kaal_21930525\` (Zimone et Dina).
  - \`artifact\`: \`Brimaz_V3\`, \`Kaal_23328062\` (Lathril),
    \`Kaal_11485202\` (Urza), \`Kaal_22193355\` (Amalia).
- \`scripts/batch.py\` : exécution \`java -jar ... sim -f Commander\`
  avec 4 sièges, \`-s <seed>\`, \`-c <clock_seconds>\`, rotation,
  profile, sortie \`games.json\` et log brut. Toutes les parties
  jouées dans de vrais processus JVM indépendants.
- \`scripts/certify_commander_games.py\` +
  \`scripts/forge_result_evidence.py\` : Scryfall +
  certification du transcript 4 joueurs, 1 vainqueur naturel,
  3 issues individuelles perdantes, délais et logs hashés.
  Légitimité de victoire ≠ preuve complète de toutes les règles Oracle.
- Captures \`ai_quality_signatures\` : timeouts d'évaluation IA, repli
  après attaque invalide, avertissements d'Incubate.
- GitHub Actions parallélise par pod/rotation, collecte artefacts et
  recertifie après chaque campagne. Un job \`success\` veut dire que
  la CI a exécuté les contrôles demandés, pas que Brimaz a gagné.

## 3. Ce qui est EMPIRIQUEMENT mesuré (V1–V8)

- Historique 32 parties : 29 naturelles selon l'ancien contrôle,
  3 censurées, **0 victoire Brimaz**. Après le contrôleur renforcé
  **12/16 acceptées, 4 exclues** sur un sous-ensemble historique
  (certains logs ne contiennent que 3 issues).
- Une *première victoire historique* \`seed 20291010\`, clock360s,
  356476ms, Brimaz siège 2, deck aristo, Forge stock + Charm,
  **NON REPRODUITE** à clock900s : Radha gagne à ~437493ms;
  les traces divergent au tour Forge33 par le choix de donjon d'un
  autre joueur, et contiennent 2 vs 6 timeouts d'IA.
  **NE JAMAIS** la présenter comme une preuve de winrate positif,
  ni prétendre que le clock différent est la cause exclusive.
- Deux répétitions avec **seed ET clock 600 identiques** :
  l'une est naturelle (Dungeon gagnant), l'autre censurée;
  leurs traces divergent au tour Forge40, 6 vs 19 timeouts IA.
  Le \`-s\` Forge appelle pourtant \`MyRandom.setRandom(new Random(seed))\`;
  il y a donc une **non-reproductibilité effective** à expliquer.
- Forge \`Game.AI_TIMEOUT\` par défaut **5 s PAR DÉCISION**;
  \`AiController\` attend un FutureTask et abandonne l'évaluation
  lorsqu'elle dépasse le délai. Patch optionnel 10s testé.
  Quatre parties avec 5s/10s : 0 Brimaz gagne dans chaque bras
  (2 pods × 2 budgets), aucun gain clair; les timeouts demeurent
  dans la partie aristo.
- V6 : 4/4 naturelles, Brimaz 0/4; 7 déclenchements d'étape de fin
  de Brimaz (calcul audit), transformations d'Incubateurs et moults
  casts, mais absence de propositions de sacrifice V6.
- V7 : **instrumentation sans modification de V6**, 4/4 naturelles,
  0/4 victoire; 166 fenêtres MAIN2 observées; 64 avec Brimaz en
  jeu; 44 sans jeton Phyrexian candidat, 17 avec jeton mais sans
  outlet sur table, 3 avec outlet mais absent de la liste d'actions
  standard (KCI est une capacité de MANA hors pile!).
- V8 : ajoute transformation d'Incubateur defensif en MAIN2
  si situation menaçante et mana payable, sans violer règles;
  8 tests Java OK, 4/4 parties naturelles, 0 victoire,
  **AUCUN \`BRIMAZ_DEFENSE\` observé** => pas de gain démontré.
- IMPORTANT : \`Turn: Turn 40\` du log Forge signifie environ 10
  tours personnels PAR joueur à 4 joueurs en vie, PAS 40 rotations.
  \`PhaseHandler.turn\` incrémente à CHAQUE tour de joueur; après
  éliminations, diviser par quatre est faux.
- Audit \`scripts/audit_edh_pacing.py\` :
  5 tests, 4 parties V8, médiane du maximum des tours personnels =13.
  Deux sorties mana faibles :
   * \`artifact/20281009\` : Brimaz 7 tours personnels, seulement
     3 terrains joués, commandant jamais lancé;
   * \`aristo/20281009\` : Brimaz 15 tours personnels,
     seulement 3 terrains joués avant son 9e tour,
     premier cast Brimaz au tour personnel 9.
  Deux autres sorties : Brimaz lancé normalement au tour personnel 4.
  **Ces constats ne prouvent PAS un mauvais mulligan.**
  Aucun mulligan Brimaz dans les 4 historiques V8; mains de 7 gardées.

## 4. Sources comparatives humaines (citées, NE PAS surinterpréter)

- \`https://playgroup.gg/about\` : 720 000+ parties EDH déclarées,
  pas des millions de trajectoires complètes d'actions.
- \`https://playgroup.gg/commander/how-to-play\` :
  547279 parties multijoueurs, ~9 rotations médianes,
  durée médiane 58 minutes.
- \`https://playgroup.gg/commanders/2396-brimaz-blight-of-oreskos\` :
  2466 parties Brimaz de LISTES DIVERSES, taux publié ~19%
  (NON applicable directement à V3 / ses deux pods).
- \`https://playgroup.gg/playgroup-live/how-sparring-works\` :
  ~6934 parties Live détaillées, ~21480 interactions :
  58% retrait ciblé, 19% contresorts, 13% wraths.
  Ce sont des fréquences descriptives, pas des priorités
  magiquement intégrables à l'IA. Ne pas prétendre disposer
  des trajectoires détaillées des centaines de milliers de parties.

## 5. Travaux en cours : V9 POLICY **BRIMAZ ONLY**

\`scripts/patch_forge_brimaz_v9.py\` part de V8 (pas de nouveau
moteur Magic), compile :
- \`AiController.java\` (V8, selection des actions pour Brimaz),
- \`BrimazTurnPlanner.java\` (V8),
- \`PlayerControllerAi.java\` (une SEULE modification :
  \`mulliganKeepHand\` consulte \`BrimazMulliganPolicy\`),
- \`BrimazMulliganPolicy.java\` (politique pure + instrumentation).
Il ne change aucun autre joueur, ni les cartes, ni les règles
London mulligan, ni la taille de main.

Heuristique à tester, seulement lorsque \`cardsToReturn==0\`
(mulligan gratuit Commander) ET l'IA stock garderait la main :
**exactement deux terrains potentiellement jouables** (MDFCs
\`Agadeem's Awakening\`, \`Malakir Rebirth\`,
\`Witch Enchanter\` comptées comme terrains possibles),
**zéro source de ramp économique** (Sol Ring, Arcane Signet,
Talisman of Hierarchy, Orzhov Signet, Ornithopter of Paradise,
Gold Myr), **zéro pioche à faible coût garantie**, et
**au moins 2 sorts CMC >=3**. Rejette alors cette main et
laisse Forge effectuer un mulligan normal et mélanger. Tous les
autres cas utilisent \`ComputerUtil.wantMulligan\` intact.
C'est une politique prudente et expérimentale, PAS une
preuve de meilleur mulligan ou de probabilité de victoire accrue.
Le comportement peut être modifié uniquement après observation.

- Tests statiques Java :
  \`tests/java/forge/ai/BrimazV9MulliganChecks.java\` (9 cas)
- Analyseur de vraies mains gardées et décisions :
  \`scripts/audit_brimaz_mulligan.py\` et tests
  \`tests/test_brimaz_mulligan_audit.py\`.
- Workflow pilote :
  \`.github/workflows/brimaz-v9-mulligan-pilot.yml\`
  et runs de départ : **37998299819** (snapshot avant commit
  de l'analyseur, susceptible d'échouer au job audit)
  et **37998385269** (snapshot incluant analyseur et tests).
  À la rédaction, ces runs étaient en cours. **RECONSULTER
  LEUR ÉTAT, NE PAS INVENTER LES RÉSULTATS**.

Il faut vérifier :
1. 9 tests Java et 5 tests Python (mulligan) réellement réussis;
2. 4 parties naturelles correctement certifiées ;
3. existence de \`BRIMAZ_MULLIGAN: V9\` dans les LOGS BRUTS
   de Brimaz; si absents, peut-être que ZoneType.Command
   n'est pas encore initialisé au moment du mulligan;
4. \`free_mulligan_overrides\` >0 ? Si 0, V9 n'a pas été
   effectivement exercée, ne pas en déduire une amélioration;
5. \`audit_edh_pacing.py\` : terrain joué à tour 4/6/8,
   premier cast Brimaz et nombre de tours par joueur;
6. comparaison V8/V9 descriptive; **mêmes seeds Forge non
   déterministes**, donc le changement d'issue ne prouve
   pas nécessairement l'effet du mulligan.

Ne pas créer de version V10 arbitrairement si la V9 plante;
corriger d'abord les tests, la télémétrie ou les décisions incorrectes.

## 6. Carte des chemins de code et des workflows

- \`decks/Brimaz_V3.txt\` : liste fixe.
- \`scripts/batch.py\` : exécuteur parties, \`--clock\`,
  \`--timeout\`, \`--seed-base\`, \`--rotation\`,
  \`--games-per-rotation\`, \`--policy-label\`,
  \`--require-canonical-decks\`.
- \`scripts/patch_forge_charm_context.py\` : bugfix Charm.
- \`scripts/patch_forge_brimaz_v6.py\` : test ancien,
  \`patch_forge_brimaz_v7.py\` : observation,
  \`patch_forge_brimaz_v8.py\` : transformation défensive,
  \`patch_forge_brimaz_v9.py\` : mulligan ciblé.
- \`scripts/patch_forge_ai_budget.py\` : budget optionnel
  10 secondes / décision pour TOUS les joueurs (pas généraliser
  sans évaluation).
- \`scripts/forge_result_evidence.py\` et
  \`scripts/certify_commander_games.py\` : filtre des résultats
  naturels et signatures d'erreurs.
- \`scripts/audit_matched_replay.py\` : compare deux vrais logs,
  trouve première action divergent;
  \`scripts/audit_edh_pacing.py\` : compte vrais tours par siège,
  suivi de mana et du premier cast Brimaz;
  \`scripts/analyze_ai_gameplay.py\` : comportements résolus
  sur la pile; \`scripts/audit_brimaz_windows.py\` :
  opportunités MAIN2; \`scripts/audit_brimaz_mulligan.py\` :
  mains de départ V9.
- \`.github/workflows/brimaz-v9-mulligan-pilot.yml\` : expérimentation.
- \`.github/workflows/commander-evidence-and-ai-audit.yml\` :
  garde-fous CI, 14 unit tests.
- \`.github/workflows/brimaz-seed-stability.yml\` :
  reproductibilité, mise en évidence des divergences.
- \`.github/workflows/brimaz-ai-timeout-pilot.yml\` :
  5s contre 10s de décision.
- \`.github/workflows/edh-empirical-pacing.yml\` :
  déploiement Brimaz et mana sur 4 parties V8,
  **run 37997796527 SUCCESS**.
- \`.github/workflows/brimaz-v8-defense-pilot.yml\` :
  run **37995083458 SUCCESS**, 0/4 victoires Brimaz.
- \`docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md\` :
  architecture historique très détaillée;
  \`docs/REPRISE_2026-10-09_CI_V7.md\` :
  V6–V8, changements pour la qualité IA;
  \`docs/EDH_EMPIRICAL_PACING_AND_AI_CALIBRATION.md\` :
  données humaines réelles et conversions de tours;
  **CE document** : passation active post-V8 / V9.

## 7. Règles de rigueur et écueils constatés

- **Important** : capacités de mana (Krark-Clan Ironworks)
  **ne passent pas par la pile**. Le fait de ne pas voir
  \`Add To Stack\` pour KCI N'EST PAS une preuve d'inutilisation.
- Brimaz se déclenche au début de **chaque étape de fin** si
  un Phyrexian contrôlé par Brimaz est mort **AVANT**
  le début de cette étape; sacrifier après le début est trop tard.
- Un jeton Incubateur **n'est pas une créature** avant
  transformation; son coût de transformation doit être payé,
  et l'invocation des créatures doit respecter le mal
  d'invocation pour attaque/tap, mais le coût de transformation
  n'est pas en soi interdit par la summoning sickness.
- \`status == complete\` dans \`batch.py\` ne suffit pas :
  toujours lancer \`certify_commander_games.py\`.
- \`status=clock_censored\`, \`engine_fault\`, \`process_timeout\`,
  \`unparsed\` ou erreur de certification ne comptent pas
  comme des défaites ni des victoires naturelles.
- Corriger les timeouts IA sans violer les règles.
  Une exception \`TimeoutException\` de \`AiController\`
  **n'est pas** une exception du moteur de règles;
  elle indique une faiblesse de décision / reproductibilité.
- La recherche de 20% exige des campagnes de plusieurs centaines
  de parties et intervalles de confiance; ne PAS extrapoler un
  0/4 ou un 1/4.
- La priorisation des cartes Magic en tant que moteur de mana,
  carte double-face ou capacité ciblée nécessite validation
  selon le moteur de règles, pas uniquement un nom dans un tableau.
- Les artefacts GitHub contiennent les logs brut véritables;
  un tableau récapitulatif sans les logs ne suffit pas.

## 8. Reprise technique dans un NOUVEAU chat

1. Lire cette passation + rapport historique + calibration.
2. Connecteur GitHub déjà associé au repository privé :
   \`mcp__GitHub__fetch_file\` permet de lire un chemin sur
   \`ref="improve/realism-and-ai-diagnostics"\`; \`fetch\`
   supporte l'API REST GET publique/privée selon droits.
   \`fetch_workflow_run_jobs\`, \`fetch_workflow_job_logs\`,
   \`fetch_workflow_run_artifacts\` pour résultats.
   \`create_file\` et \`update_file\` (SHA du fichier obligatoire)
   permettent de committer directement.
3. Appeler
   \`GET https://api.github.com/repos/Toko177/brimaz-forge-lab/actions/runs?per_page=20\`,
   lire les run IDs V9 depuis le dépôt actuel.
4. Inspecter les jobs et leurs logs pour statut V9.
5. Si 4/4 sont certifiés et la politique a vraiment été
   exercée : comparer V9 avec V8 sans faux causalisme,
   commencer analyse améliorations post-mulligan.
6. Si la politique n'est pas exercée, vérifier le
   \`ZoneType.Command\` au moment du mulligan :
   ne pas inventer un winrate ou augmenter son agressivité
   aveuglément.
7. Explorer correction plus générale des timeouts et
   des décisions de mana et d'interaction des quatre IA :
   un moteur de simulation "utilisable" doit être cohérent
   même lorsque Brimaz perd.
8. Actualiser CE DOCUMENT après chaque itération
   avant de fermer le chat; garder son lien dans README.

## 9. Statut et liens incontournables

- PR #1 (travaux expérimentaux) :
  https://github.com/Toko177/brimaz-forge-lab/pull/1
- Audit historique V6 14 tests :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995808086
- Re-certification historique :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995793455
- Première victoire 360s vs 900s :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37994894861
- Réplication exactement même seed et 600s :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995223230
- Comparaison AI 5s/10s :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995525927
- V7 observation :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37992540124
- V8 :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995083458
- Audit 4 V8 en tours personnels :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37997796527
- V9 :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37998385269

**À garder** : chaque état expérimental doit documenter commit,
patch et règles modifiées (ou intactes), graine, pod, rotation,
horloge, status, winner, censure et source réelle de l'événement.
Une victoire n'a de valeur que si elle est une vraie victoire légale
obtenue à quatre joueurs grâce à une IA compétente et évaluée.
