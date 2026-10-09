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


## 10. Première observation V9 EFFECTIVEMENT vérifiée (avant certification complète)

Sur l'artefact réel \`brimaz-v9-mulligan-artifact-2\` du run
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37998299819 :

- \`artifact/20281009\` :
  trace \`BRIMAZ_MULLIGAN: V9 hand=7 actualLands=2
  potentialLandDrops=2 cheapRamp=0 cheapDraw=0 expensive=4
  cardsToReturn=0 stockKeep=true overrideFreeMulligan=true\`.
  Forge montre ensuite un mulligan gratuit, puis une main conservée
  de 7 cartes, 3 terrains. Brimaz joue **6 terrains en 7 tours
  personnels**, et invoque pour la première fois le commandant
  au tour personnel **5**; Amalia gagne naturellement. En V8,
  même seed (NON nécessairement même déroulement aléatoire) :
  **3 terrains en 7 tours**, commandant jamais lancé, Amalia gagne.
- \`artifact/20281010\` : V9 n'effectue aucun mulligan forcé;
  main initiale 3 terrains physiques (+1 MDFC possible); Brimaz
  joue 7 terrains en 8 tours, est invoqué au tour 4; Amalia
  gagne aussi naturellement.
- **9 tests Java V9 réussis**, au moins deux parties pilotes
  artefact terminées avec 0 victoire Brimaz. L'artefact
  est issu du premier workflow, dont l'auditeur V9 n'était
  pas encore présent au SHA de déclenchement.
- Le second workflow V9 https://github.com/Toko177/brimaz-forge-lab/actions/runs/37998385269
  a été déclenché APRES inclusion de l'auditeur et des tests
  Python. À recontrôler pour confirmer le statut de 4/4.

Cette observation est **un changement de décision V9 réellement exercé**,
PAS une preuve de winrate supérieur, ni une paire de parties identiques
(surtout lorsque le mulligan change les cartes et le flux RNG).
La V9 doit être évaluée sur beaucoup plus de départs indépendants.


## 11. Mise à jour V9 : première campagne de 4 parties et 33 tests vérifiés

- Run **37998299819** :
  - 4 parties **\`complete\` et acceptées par
    \`certify_commander_games.py\`** ;
  - Brimaz **0/4 victoires** (donc pas de gain de winrate démontré) ;
  - **2/4 parties** ont eu un véritable
    \`BRIMAZ_MULLIGAN: overrideFreeMulligan=true\` ;
  - **6 exceptions d'évaluation IA** au total (sur 2 parties) ;
  - 1 partie avec déclaration d'attaque invalide rattrapée.
  - job final \`audit-windows\` en **failure** parce que ce
    workflow fut déclenché AVANT la création du script
    \`scripts/audit_brimaz_mulligan.py\` : la certification des 4
    parties s'est néanmoins exécutée et a réussi. Ne pas
    qualifier ce premier job \`failure\` de "parties invalides" !
    Le run suivant inclut le script et ses tests.
- Détails V8 → V9, mêmes seeds mais **sans reproductibilité
  exacte des RNG**, donc comparaison descriptive :

| Pod/seed | V8 terrains joués | V9 terrains joués | V8 1er cast Brimaz | V9 1er cast Brimaz | V9 mulligan forcé |
|---|---:|---:|---|---|---|
| artifact / 20281009 | 3 (7 tours perso) | 6 (7 tours perso) | jamais | tour perso 5 | oui |
| artifact / 20281010 | 7 (8 tours perso) | 7 (8 tours perso) | tour perso 4 | tour perso 4 | non |
| aristo / 20281009 | 5 (15 tours perso) | 10 (11 tours perso) | tour perso 9 | tour perso 4 | oui |
| aristo / 20281010 | 9 (13 tours perso) | 9 (13 tours perso) | tour perso 4 | tour perso 4 | non |

- Run \`37998385269\` est **la reproduction correcte V9**
  avec l'analyseur inclus et 5 unit tests Python du
  mulligan. Sa progression était encore en cours au dernier
  contrôle. **RECONSULTER les jobs** avant de conclure.
- Run **37998822473 SUCCESS** : la CI centrale exécute
  **33 unit tests Python réussis**, incluant le parseur
  du mulligan, le comparateur V8/V9 et les validations
  anciennes, puis **4/4 V6 recertifiées**.
- Ne pas confondre les meilleures sorties de mana observées
  à seed donnée avec une amélioration statistiquement
  démontrée du pilotage ou du winrate. Il faudra des
  dizaines de mains conservées/rejetées supplémentaires,
  idéalement des scenarios de mains dont la compétence
  peut être vérifiée indépendamment des RNG des matchs.


## 12. Résultat DÉFINITIF de la seconde CI V9 (code complet)

**Workflow V9 37998385269 = SUCCESS**, trois jobs
\`aristo rotation 2\`, \`artifact rotation 2\`, \`audit-windows\`
tous réussis. Résultats du job d'audit de ce run :

\`\`\`json
{
  "checked_games": 4,
  "accepted_natural_games": 4,
  "accepted_brimaz_wins": 0,
  "excluded_games": 0,
  "games_with_ai_eval_timeouts": 2,
  "total_ai_eval_timeouts": 7,
  "games_with_invalid_ai_attack_fallbacks": 1
}
\`\`\`

Mulligan réel (parser V9 + 5 tests passés) :
\`\`\`json
{
  "games": 4,
  "natural_games": 4,
  "free_mulligan_overrides": 2,
  "games_using_override": 2,
  "brimaz_natural_wins": 0
}
\`\`\`

Pacing réel V9 :
- médiane du maximum des tours personnels : 12,5 ;
- premier cast Brimaz **dans 4/4 parties**, médiane tour
  personnel 4 ;
- aucun premier cast après le sixième tour personnel.
Contraste descriptif avec V8 : 3/4 premiers casts,
dont 1 au tour personnel 9, médiane conditionnelle tour 4.
Ces chiffres NE suffisent PAS à démontrer une causalité,
un meilleur winrate ou une bonne qualité stratégique globale.

**Comparateur V8/V9** \`scripts/compare_pacing_experiments.py\`
et workflow \`.github/workflows/brimaz-v8-v9-paired-pacing.yml\` :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999007185.
Le résultat de ce dernier workflow doit être inspecté; son
nom annonce explicitement \`observational\` pour empêcher une
interprétation fausse de paires de graines non déterministes.

Le run de campagne initial V9 37998299819 affiche \`failure\`
UNIQUEMENT car son snapshot était antérieur à la création
du script \`audit_brimaz_mulligan.py\`; 4 parties certifiées
dans ce run mais ne pas utiliser ce vieux run en point
d'entrée. Utiliser **37998385269 SUCCESS**.


## 13. Comparaison V8/V9 CI finalement VALIDÉE (4 parties appariées, sans causalité)

**Workflow 37999007185 SUCCESS** :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999007185

Tests purs : 4 du comparateur, 5 du pacing, 5 du parser
mulligan réussis. 4 paires (pod + seed) réelles; les
8 parties (4 V8 + 4 V9) ont toutes une fin naturelle.
Dans les deux cas de mulligan V9 (\`aristo/20281009\` et
\`artifact/20281009\`) :
- meilleure progression vers huitième tour personnel :
  +4 terrains joués (3 → 7) en aristo, +3 (3 → 6) en artifact;
- premier cast Brimaz : aristo tour personnel 9 → 4,
  artifact jamais → tour personnel 5.
Dans les deux cas sans mulligan forcé, terrains jusqu'au
tour 8 inchangés à 7, premier cast au tour personnel 4.
**0 victoire Brimaz en V8 et V9.**

Échantillon 4 paires trop petit + Forge non déterministe :
**la politique semble améliorer le développement du mana sur
ces deux mains ciblées, MAIS l'inférence causale et l'amélioration
du winrate ne sont pas démontrées.** Il faut ensuite faire des
tests de mulligan sur davantage de distributions d'ouvertures
et progresser sur l'interaction / le combat / le moteur de
sacrifice. Conserver la V9 comme politique expérimentale,
pas l'adopter par défaut avant des échantillons plus larges.


## 14. Reprise V10 : profiler *tous* les sièges et isoler les lenteurs de combat

La campagne V9 a laissé **7 TimeoutException** sur 2/4
parties (aristo) et une correction d'attaque invalide.
Inspection directe des sept \`AI eval thread at timeout:\` du
run V9 \`37998385269\` : **7/7 traversent les calculs de combat
\`ComputerUtilCombat\`, \`AiBlockController\`, ou
\`ComputerUtil.predictNextCombatsRemainingLife\`**. Les premiers
frames varient : \`Card.updateStaticAbilities\`, \`Card.getName\`,
\`ReplacementHandler.getReplacementList\`,
\`Card.updateSpellAbilities\`, etc. Il s'agit de recalculs
d'évaluation des bloqueurs, des dégâts prévisionnels ou des
capacités statiques/règles, et PAS de preuves d'erreur
dans une carte en particulier.

### Code V10 créé
- \`scripts/patch_forge_brimaz_v10.py\` : reprend l'intégralité
  des décisions V9 (dont mulligan gratuit ciblé Brimaz) ;
  instrumente le \`FutureTask\` interne au
  \`AiController.chooseSpellAbilityToPlayFromList\` officiel,
  **sans changer le budget 5s, l'ordre des sorts, les décisions,
  ni le traitement des timeouts** ;
  journaux \`AI_EVAL_SLOW_V10\` pour décisions >=1s, et
  \`AI_EVAL_TIMEOUT_V10\` pour dépassements, avec joueur,
  tour global, phase, temps, budget, candidats analysés,
  carte examinée au moment du timeout.
- \`PlayerControllerAi.mulliganKeepHand\` : télémétrie
  \`AI_OPENING_V10\` des **4 sièges** (nombre de cartes,
  vrais terrains, sorts de faible coût), sans transmettre
  la main des adversaires à une autre IA ; la stratégie
  V9 Brimaz est préservée.
- \`scripts/audit_ai_eval_hotspots.py\` et
  \`tests/test_ai_eval_hotspots.py\` : parser/diagnostic des
  lenteurs et stacks, attribution du joueur/siège, carte
  en cours d'évaluation et type de point chaud. Tester
  la concordance des compteurs de timeout instrumentés
  avec les vraies \`TimeoutException\` du moteur.
- \`.github/workflows/brimaz-v10-ai-hotspot-pilot.yml\` :
  4 parties EDH réelles, 2 pods, siège/rotation2,
  graine 20261009, horloge360s, 2 matchs par pod.
  **Run initial 37999502125** :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999502125.
  Contrôler le statut réel : à la création il était
  \`in_progress\`, ne pas présumer du résultat.
- \`.github/workflows/commander-evidence-and-ai-audit.yml\`
  déclenche aussi les nouveaux tests V10 pour éviter
  une régression silencieuse.

### Travail à faire après cette phase
1. Valider compilation Java V10, tests Python, 4 parties
   naturelles et contrôle de 4 \`Game Outcome\`.
2. Examiner \`AI_EVAL_TIMEOUT_V10\` :
   **quelle carte ? quel joueur ? combien de candidats ?
   quel sous-système exact ?** Un timeout avant que
   la liste de décisions soit consommée peut faire passer
   toute l'IA alors qu'elle aurait eu une bonne réponse.
3. Identifier un calcul redondant avec une preuve
   d'équivalence de comportement ; optimiser sans
   surestimer les menaces, sans désactiver les bloqueurs,
   et sans modifier les règles Magic.
4. Faire un A/B benchmark avec la politique V9 inchangée,
   mesurer temps de décision / fréquence des timeouts,
   temps total, légalité et si possible robustesse de RNG.
5. Documenter tous les correctifs et résultats ici ;
   ne pas prétendre que V10 augmente le winrate : il est
   **instrumentation**, pas encore nouveau moteur tactique.

### Précautions à conserver
Dans le code officiel \`AiController\` :
\`future.get(game.getAITimeout(), TimeUnit.SECONDS)\`
attend jusqu'à 5s, puis tente \`future.cancel(true)\`,
\`t.join(2000)\`, et en dernier recours \`t.stop()\`
(lorsqu'il est disponible). Forcer la terminaison d'un
thread pendant des mutations du jeu est dangereux;
il faut auditer ce phénomène avant de l'« optimiser ».
Ne JAMAIS augmenter artificiellement le winrate par
suppression d'une phase de combat, choix aléatoire de
bloqueurs ou limites de tours arbitraires.


## 15. V10 / V11 — audit quatre IA et budget de réflexion ADAPTATIF

### Cause empirique des timeouts V9
Run postmortem **37999670437 SUCCESS** :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999670437
7 Python unit tests réussis ; 4 vraies parties V9 relues ;
7 \`java.util.concurrent.TimeoutException\` classées :
- 6 dans \`ComputerUtilCombat\` / \`AiBlockController\` ou
  \`predictNextCombatsRemainingLife\` (calculs complexes de
  menaces / bloquants);
- 1 dans \`ReplacementHandler\` (énumération d'effets
  de remplacement).
Ces exceptions proviennent du thread de réflexion de l'IA
et **pas nécessairement du moteur de règles Magic**.
Une exception pendant une réflexion ne prouve pas que toute
la partie était illégale; elle dégrade cependant la qualité
de pilotage et parfois la reproductibilité.

### V10 = instrumentation PURE de la politique V9
\`scripts/patch_forge_brimaz_v10.py\` : conserve les choix
stratégiques V9, la même limite de 5s et toutes les règles.
\`AiController.chooseSpellAbilityToPlayFromList\` :
- \`AI_EVAL_TIMEOUT_V10\` : joueur, tour, phase,
  millisecondes, limite réelle, nombre de capacités
  listées / considérées, dernière carte en cours
  d'évaluation ;
- \`AI_EVAL_SLOW_V10\` : décision terminée mais lente >=1s;
- \`AI_OPENING_V10\` : chaque joueur, nombre de terrains
  initiaux, sorts de faible coût, frais de mulligan ;
  chaque joueur reçoit seulement les informations dont
  Forge dispose normalement; le journal de diagnostic ne
  fournit pas les mains adverses aux IA.

\`scripts/audit_ai_eval_hotspots.py\` :
classification des stacks et des événements par siège;
\`tests/test_ai_eval_hotspots.py\` : 7 tests.
Workflow :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999502125
**Recontrôler son statut** avant de parler de fin ou de victoire.

### V11 = expérimentation de coût CPU global (PAS gain prouvé)
\`scripts/patch_forge_brimaz_v11.py\` : superpose
à V10 une adaptation du \`Game.AI_TIMEOUT\` partagé
par la table : **5s -> 10s** après la première exception,
**10s -> 15s** après la deuxième, puis pas d'autre hausse.
La limite s'applique identiquement aux quatre joueurs.
Aucune carte / deck / PV / règle Magic n'est modifié.
Attention : le timeout déjà échu reste abandonné, le
\`Thread.stop()\` historique reste inchangé et
le CPU / temps d'exécution peut augmenter.
Ne jamais affirmer que V11 améliore la tactique
simplement parce qu'il augmente le budget.

\`scripts/audit_adaptive_ai_budget.py\` et
\`tests/test_adaptive_ai_budget.py\` : 7 tests qui
interdisent les régressions du budget, les hausses
sans TimeoutException et le dépassement de 15s.
Workflow :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999839503
**Recontrôler son statut et ses résultats**, particulièrement
les phases d'audit des vraies parties.

### Critères de comparaison V9/V10/V11
- Toujours même ensemble de decks légaux et adversaires
  Forge ; quatre vrais joueurs dans chaque partie.
- Comparer : \`status\` naturel / censuré, nombre
  d'exceptions AI, temps de CPU, nombre de cartes
  examinées lors des délais, déclarations d'attaque
  invalidées et déploiement de Brimaz.
- Une graine identique ne donne PAS une trajectoire
  identique dans Forge : comparer les distributions
  et rappeler l'incertitude statistique.
- Une V10 « observation pure » ne doit pas prétendre
  rendre les IA meilleures; une V11 « délai adaptatif »
  ne doit pas être promue sans preuve de diminution
  des décisions abandonnées ET surcoût acceptable.
- Les timeouts de combat doivent conduire à une
  optimisation mesurée du moteur d'évaluation, PAS à la
  suppression de bloqueurs ou de menaces pour aller vite.

### Reprise depuis un nouveau chat
\`GET /repos/Toko177/brimaz-forge-lab/actions/runs?per_page=20\`,
puis pour chaque run V10/V11 appeler
\`fetch_workflow_run_jobs\` et
\`fetch_workflow_job_logs\` via GitHub connector.
Suivre les artefacts \`brimaz-v10-...\` et
\`brimaz-v11-...\`; extraire \`results/v10\`,
\`results/v11\` et les journaux Forge bruts.
Poursuivre ensuite sur les véritables goulets
d'étranglement les plus coûteux, sans handicaper
les autres joueurs et sans gonfler le winrate.


## 16. V10 : résultat COMPLET, vraie victoire Brimaz et faux rejet corrigé

**Run V10 observation** 37999502125 : 4 parties Forge
jouées (4 sièges, Deck V3 officiel, IA V9 inchangée
sauf instrumentation V10).
- le premier audit de ce run a rapporté
  \`accepted_natural_games=3\`, \`accepted_brimaz_wins=0\`
  et un match \`aristo/20281010\` rejeté : le parseur
  \`_OUTCOME\` acceptait \`has lost because\` mais
  oubliait \`has lost trying to draw cards from empty
  library\`.
- **BUG DU CERTIFICATEUR**, pas échec du moteur :
  le transcript original contient bien exactement quatre
  \`Game Outcome\`, un vainqueur Brimaz et trois vaincus.
  À la graine \`20281010\`, sièges rotation2 :
  - \`Ai(1)\` Dungeon Party Time : perdu, points de vie 0;
  - \`Ai(2)\` Zimone and Dina : perdu en tentant une
    pioche dans une bibliothèque vide;
  - \`Ai(3)\` Brimaz : gagné, tous adversaires éliminés;
  - \`Ai(4)\` Radha : perdu, points de vie 0.
  \`Game Result\` vainqueur Brimaz, durée moteur
  **164 227ms**, bien avant horloge360s.
  **Ce compte rendu ne prouve pas que Brimaz a
  personnellement infligé les deux dégâts létaux ni
  provoqué le deck-out** : il est juste survivant
  après trois éliminations.
- \`scripts/forge_result_evidence.py\` reconnaît
  maintenant seulement les grammaires explicites
  \`won because\`, \`lost because\`, \`lost trying to\`,
  en exigeant toujours quatre sièges distincts,
  un seul vainqueur et trois vaincus. Régression
  \`tests/test_forge_evidence.py\` inclut deckout
  accepté et sortie inconnue rejetée.
- **Run de re-certification 38000153841 SUCCESS** :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/38000153841
  **4/4 parties naturelles validées, 1/4 Brimaz victorieux,
  zéro exclue**.
- Attention : le match victorieux a **4 TimeoutException**
  dans le thread IA Brimaz et 1 attaque invalide
  automatiquement corrigée par Forge. Il faut conserver
  cette information de qualité IA, ne pas compter ce
  \`1/4\` comme une estimation de winrate réel, et
  ne pas créditer l'instrumentation V10 d'un bonus
  tactique qu'elle n'apporte pas.
- Plusieurs runs sur même seed sont déjà divergents :
  pas de reproductibilité démontrée de cette victoire.

### Diagnostic de V10 maintenant précis par joueur/carte
Le premier rapport a trouvé **6 TimeoutException** au
total : 4 dans une même partie Brimaz (\`Ai(3)\`)
au tour global Forge47, **la carte candidate
\`Vault of the Archangel\` à toutes les phases
UPKEEP, DRAW, MAIN1, COMBAT_BEGIN** ; 2 chez
Zimone and Dina (\`Ai(2)\`) devant les cartes
\`Shore Up\` et \`Octopus Form\`.
Les **6 échantillons de stack** se situent dans
les calculs profonds de combat et de blockers,
sans prouver une erreur de règle liée à ces cartes.
Le rapport V10 observe aussi **8 décisions lentes
terminées entre ~1 et ~4 secondes** et
**20 évaluations de mains initiales des 4 sièges**.
Aucune modification stratégique n'a été appliquée
aux trois adversaires.

### Audit amélioré des conditions de victoire
\`scripts/forge_result_evidence.py\` possède désormais
\`describe_outcome_modes\` : modes \`life_total_zero\`,
\`library_depletion\`, \`poison\`, \`survivor_won\`
ou \`other_reported_elimination\`.
Le certificat \`scripts/certify_commander_games.py\`
ajoute \`outcome_modes\` et la valeur explicite
\`victory_causality_verified=false\`.
Ne pas confondre victoire en étant dernier survivant
et causalité démontrée d'un kill piloté par Brimaz.

### État V11 à vérifier
La campagne https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999839503
était en cours (groupe artifact terminé, groupe aristo
pas encore) au moment de cette addition. Examiner
les journaux et l'audit de son budget adaptatif partagé
et les risques de CPU avant de promouvoir V11.


## 17. V11 certifiée + V12 nouveau gestionnaire \`Incubate\`

### Résultat V11 complet
Run **37999839503 SUCCESS** :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37999839503
Quatre parties réelles, **4/4 certifiées naturellement**, 0/4
victoire Brimaz. **2 TimeoutException** au total (contre 6
dans V10 à mêmes pods/seeds mais exécutions non
déterministes), 1 attaque invalide corrigée,
10 décisions terminées mais lentes. Deux épisodes ont
élevé le budget de 5s à 10s pour toute la table;
aucun épisode à 15s. Les deux cartes en cours de
réflexion au timeout étaient \`Octopus Form\` pour
Ai(2) et \`Vault of the Archangel\` pour Ai(3).
Conserver cette politique comme **expérimentation** ;
aucune preuve de gain en qualité tactique ou de winrate.
L'effet de l'augmentation du budget sur le CPU doit
être encore mesuré sur davantage de parties.

### V12 : lacune de couverture IA Incubate
Forge 2.0.15 \`forge-ai/.../SpellApiToAi.java\` ne
contient **pas** \`.put(ApiType.Incubate,...)\`.
Le code \`SpellApiToAi.Converter.get\` log
\`No AI assigned for API: Incubate\` et substitue
\`CannotPlayAi.class\`, ce qui peut empêcher la
sélection volontaire d'une action Incubate.
**Ce n'est pas une erreur du moteur de règles
IncubateEffect** : les jetons continuent d'être créés
par \`forge-game/.../effects/IncubateEffect.java\`.
Cela concerne le support de décision AI.

Patch \`scripts/patch_forge_brimaz_v12.py\` : part
du **V10 observer + choix stratégiques V9**,
PAS de V11 budget adaptatif. Ajoute une seule
entrée de dispatch \`ApiType.Incubate ->
IncubateAi.class\` dans \`SpellApiToAi.java\`
et une classe
\`forge.ai.ability.IncubateAi extends SpellAbilityAi\`.
Son \`checkApiLogic\` approuve l'idée de lancer Incubate;
les **contrôles génériques de timing, restrictions,
conditions et paiement de coûts** du moteur AI/règles
restent en place. Le patch s'applique à **toutes
les quatre IA**, pas uniquement à Brimaz.
Aucune création de jeton manuelle, aucun changement
de règle ou de cartes.
La V12 est une modification d'IA fonctionnelle :
la juger selon nombre d'Incubate légaux exercés,
la présence/absence d'avertissement, leur coût
et le résultat de 4/4 parties certifiées,
**pas seulement** un nouveau winrate.

Test Java réel sur JAR :
\`tests/java/forge/ai/BrimazV12IncubateChecks.java\`,
qui affirme \`SpellApiToAi.Converter.get(ApiType.Incubate)\`
une instance de \`IncubateAi\` et NON \`CannotPlayAi\`.
Workflow pilote :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38000469712
**RECONTRÔLER son statut avant de rapporter un résultat !**

### Référentiel de rigueur
- Toutes les parties sont distribuées en JVM distinctes,
  réelles et sans changement des quatre decks canoniques;
  conserver toutes les censures/exception.
- Un résultat \`winner_deck=Brimaz_V3\` n'est pas
  un exploit si l'IA a triché, une sortie de log est
  incomplète ou le résultat est fabriqué.
- Le run V10 avec 1 vraie victoire a été recertifié
  en exigant les quatre \`Game Outcome\` et la
  reconnaissance d'une défaite par bibliothèque vide,
  et contient des anomalies de qualité IA :
  **4 timeouts + 1 attaque corrigée**.
- Ne pas supposer les sorties 4/4 de V12 avant
  résultats des jobs.


## 18. Nouvelle double certification : issue naturelle ≠ IA sans avertissements

Le certificat \`scripts/certify_commander_games.py\` comprend
désormais \`ai_warning_free\` calculé séparément à partir
des \`evaluation_timeouts\`, \`invalid_attack_fallbacks\`,
\`incubate_handler_warnings\` et
\`decision_thread_timeout_samples\`.
Il publie :
- \`accepted_natural_games\` :
  seulement les jeux à issue cohérente 4 joueurs ;
- \`accepted_brimaz_wins\` :
  vraies issues naturelles Brimaz ;
- \`accepted_warning_free_natural_games\` :
  parties naturelles sans ces avertissements IA ;
- \`accepted_warning_free_brimaz_wins\` :
  Brimaz victorieux et aucune anomalie IA surveillée.
  Même une partie sans avertissement ne prouve PAS
  que les quatre IA jouent au niveau humain.

**V10 re-certifié selon ces deux niveaux** :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38000704526
\`\`\`json
{
  "checked_games": 4,
  "accepted_natural_games": 4,
  "accepted_brimaz_wins": 1,
  "accepted_warning_free_natural_games": 1,
  "accepted_warning_free_brimaz_wins": 0,
  "total_ai_eval_timeouts": 6,
  "excluded_games": 0
}
\`\`\`
Donc la première victoire V10 EST une vraie issue
Forge complète, mais **PAS** une victoire du sous-échantillon
sans avertissements. Ne pas afficher \`1/4=25%\`
comme compétence Brimaz démontrée.

### V12 côté artefacts
Le pilote Forge V12 a compilé, réussi le test Java
\`V12_INCUBATE_TESTS_OK\`, joué au moins 2 jeux
\`artifact\` avec Amalia gagnante dans les deux.
Leurs logs affichent **0 avertissement**
\`No AI assigned for API: Incubate\`.
Le pod \`aristo\` et l'audit indépendant doivent
encore être vérifiés : ne pas confondre absence
d'avertissement et preuve d'activation stratégique
pertinente.


## 19. Dernier contrôle automatisé du 10/10/2026

- **56 tests Python réussis**, CI commune
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/38000864386
  (\`scripts/forge_result_evidence.py\`,
  \`scripts/audit_ai_eval_hotspots.py\`,
  \`scripts/audit_adaptive_ai_budget.py\`,
  \`scripts/audit_incubate_support.py\`, etc.).
- \`scripts/audit_incubate_support.py\` et
  \`tests/test_incubate_support.py\` (4 nouveaux tests)
  auditent séparément :
  avertissement \`No AI assigned for API: Incubate\`,
  véritables résolutions de capacité contenant Incubate,
  activations de transformation \`Incubator Token\` sur la
  pile et mouvements du jeton en zone. Une mention
  "create an Incubator" dans un rappel de texte
  N'EST PAS une preuve de création supplémentaire.
- V12 \`artifact\` (dans run 38000469712) :
  2 jeux terminés, Amalia victorieuse dans chacun,
  **aucun avertissement d'IA Incubate** ;
  l'une des parties inclut de vraies résolutions
  Incubate et des transformations d'Incubateur,
  l'autre ne montre aucune résolution Incubate.
  **Ne pas annoncer 4 jeux V12 certifiés avant le job audit**.
- Le README et la PR #1 rappellent désormais que
  la victoire V10 a été acceptée sur le plan
  sortie naturelle mais pas au niveau "IA sans
  avertissements". Ne pas annoncer une
  amélioration du winrate avant davantage de jeux.


## 20. Campagne V12 élargie sur 16 jobs et audit indépendant

**Constat nouveau vérifié** : le run V12
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38000469712
est définitivement **SUCCESS**, 4/4 parties réelles naturellement
certifiées, 0 victoire Brimaz, 2 \`TimeoutException\` dans
1 partie, 1 partie avec repli d'attaque invalide,
**0 avertissement \`No AI assigned for API: Incubate\`**.
Deux victoires Amalia côté artefacts et deux victoires
Zimone et Dina côté aristocrates. Cette campagne
n'établit aucune amélioration statistique du winrate.
L'IA Incubate est bien mappée, mais il faut distinguer
les déclenchements obligatoires de choix volontaires.

### Nouvelle expérience déclarée AVANT d'observer les résultats
Workflow **\`.github/workflows/brimaz-v12-balanced-32-games.yml\`** :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38001534517

- 16 shards sur machines GitHub Actions indépendantes ;
  \`max-parallel: 12\`. **32 parties Commander véritables**
  (2 JVM indépendantes par shard), 4 joueurs/partie,
  100 cartes et mêmes 7 decks canoniques vérifiés.
- 2 pods (\`aristo\`, \`artifact\`) x 4 rotations des sièges
  x 2 cohortes de graines **fixées à l'avance**
  x 2 parties par rotation/cohorte.
- Bases des graines (ajouter 10000 fois rotation et
  0 ou 1 pour la répétition) :
  aristo : \`20310000\`, \`20410000\` ;
  artifact : \`20510000\`, \`20610000\`.
  La plage de 32 graines est distincte. Ne pas
  sélectionner après coup les graines qui font gagner Brimaz.
- \`clock=360s\`, \`timeout process=445s\`,
  même budget AI 5s, même V12 code de 4 IA.
  Une partie censurée doit rester au dénominateur
  **des parties prévues**, mais ne constitue pas un
  résultat naturel dans le calcul du taux de victoire
  conditionnel. Toujours publier les deux effectifs.
- Certifier depuis \`scripts/certify_commander_games.py\`
  avec logs brut et empreinte SHA256, puis agréger
  avec \`scripts/audit_balanced_commander_campaign.py\`.
  Chaque matchup, rotation, graine et deck est contrôlé
  et le taux Brimaz est accompagné de l'intervalle de
  Wilson à 95 %, des censures et avertissements IA.
  Regrouper également par pod et siège.
  **Ne pas affirmer de seuil >=20%** à partir d'un
  seul petit échantillon.
- L'analyseur est testé dans
  \`tests/test_balanced_commander_campaign.py\` :
  équilibre 2x4, seeds uniques, résolutions naturelles,
  rejets, censures, contrôle des gagnants, intervalles,
  qualités IA. Suite permanente
  \`.github/workflows/commander-evidence-and-ai-audit.yml\`.
- Chaque shard conserve ses traces brutes dans un
  artefact nommé
  \`brimaz-v12-32-<pod>-r<rotation>-s<seed_base>\`.
  L'artefact final \`brimaz-v12-32-certified-campaign\`
  contient \`balanced-campaign.json\`,
  \`certification/certificate.json\`,
  \`ai-evaluation-hotspots.json\`,
  \`per-seat-pacing.json\`, \`incubate-real-actions.json\`.

### Double déclenchement à connaître (ne pas compter deux fois)
La première version du workflow, run
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38001496914 ,
était déjà en file lorsqu'une assertion de contrôle
s'est révélée incorrecte (\`len(logs)==4\` malgré la
nouvelle matrice de 32). Elle a déclenché elle aussi
32 jeux ; **ce vieux job d'audit devrait échouer après
les parties sur ce contrôle**, même si les traces
Forge sont utilisables.
La correction \`len(logs)==32\` est dans le run
**38001534517**, qui doit être la source privilégiée
de l'estimation V12. Les deux runs portent les
MÊMES graines, donc **NE PAS** mélanger leurs 64
issues pour un intervalle de Wilson indépendant :
les deux traces sont des réplications / essais
non déterministes, pas 64 graines indépendantes.
Un éventuel audit futur de l'instabilité RNG
peut comparer leurs parties à graines identiques.

Au moment de cette rédaction, les deux runs
étaient en cours/queue sur GitHub, et la nouvelle
suite CI était en attente. **RECONTRÔLER leur état**,
ne pas inventer des résultats. Les workflows
exécuteront de nombreuses parties même si un
job échoue; lire tous les logs, les artefacts,
la correction du décompte, et distinguer
\`winner_deck\` du certificat indépendant.


## 21. Correctifs tests et post-traitement des 32 vrais matchs

### État vérifié de la CI au 10 octobre 2026

- [CI de régression **73/73 tests SUCCESS**](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38001973864).
  56 tests de la période précédente + 10 tests
  \`test_balanced_commander_campaign.py\` + 7 tests
  \`test_same_seed_campaign.py\`.
- Les précédentes CI 38001591893 et 38001804497
  ont échoué à cause des **fixtures de test synthétiques** :
  les tests à 8 jeux utilisaient par erreur la valeur
  par défaut \`games_per_rotation=4\` (=32 requis),
  et un adversaire était parfois simulé comme
  vainqueur alors que la case était celle de Brimaz.
  Correctif \`tests/test_balanced_commander_campaign.py\`
  commit \`06e79f290fd3f0c2e5da8910730675798237d228\`.
  La CI 38001973864 (nouveau commit) est VERTE.
  Il ne s'agit **pas** de corrections apportées au
  déroulement des parties réelles.
- \`scripts/batch.py\` explicite maintenant que
  \`-s <seed>\` fixe une graine Forge mais ne garantit
  PAS le déterminisme des décisions (commit
  \`845e704eed288d8384861d9e6ac7081f05048f57\`).
  Les premiers shards 32 ont été déclenchés avant
  ce changement cosmétique ; leurs résumés
  \`method\` peuvent donc encore indiquer à tort
  \`deterministic -s seeds\`. Référer à la passation
  et aux vraies expériences de relecture de graines.

### Post-traitement SANS rejouer les jeux

La campagne V12/32 **38001534517** a été
déclenchée alors que les nouvelles fixtures n'étaient
pas encore corrigées. Son job final peut donc
échouer aux tests, même si les **16 shards de
parties et leurs journaux bruts sont authentiques**.
Un job séparé a été ajouté, qui attend la fin de ce
run et réutilise ses artefacts :

[Workflow \`brimaz-v12-32-postprocess.yml\`](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002112497)
- attend le statut terminal du run 38001534517 ;
- récupère les **16 artefacts et 32 \`games.json\`** ;
- vérifie les **73 tests** ;
- recertifie les **32 journaux Forge** avec
  \`certify_commander_games.py\` et manifeste
  légal Scryfall original ;
- \`audit_balanced_commander_campaign.py\` contrôle
  le SHA256 de chaque transcription, l'unicité
  des 32 seeds, la matrice 2 pods x4 sièges
  et les comptes; rapporte victoire, Wilson 95%,
  jeux censurés, temps de réflexion IA et
  victoires sans avertissement de pilotage ;
- analyse les tours personnels, le mulligan et
  la couverture Incubate ;
- stocke \`v12-32-independent-certification-and-stats\`.
Le premier run de post-traitement 38002068419
a échoué en raison d'une erreur de variable d'env
\`GH_TOKEN\` ; le correctif est dans le run
**38002112497**. Ne pas rapporter de statistiques
32/32 avant sa fin et celle des shards.

### Réplications techniques (ne PAS doubler la taille d'échantillon)
\`scripts/audit_same_seed_campaign.py\` compare les
deux runs 38001496914 et 38001534517 sur leurs
32 graines identiques, sans attribuer automatiquement
les divergences aux timeouts. Les tests correspondants
\`tests/test_same_seed_campaign.py\` passent en CI.
Le fait de re-jouer les MÊMES 32 graines n'autorise
**pas** à annoncer un intervalle de confiance calculé
sur 64 réalisations indépendantes.


## 22. Test empirique des doubles campagnes (vraies 32 graines rejouées)

Le comparateur \`scripts/audit_same_seed_campaign.py\` est
maintenant associé au workflow
[\`brimaz-v12-32-same-seed-audit.yml\`](https://github.com/Toko177/brimaz-forge-lab/actions/runs?query=workflow%3A%22Audit+32+identical-seed+Forge+game+replays%22).

Ce job attend les statuts terminaux des deux
vrais runs **38001496914** et **38001534517**,
télécharge les 16 artefacts de chaque côté et
compare les **32 mêmes seed/pod/rotation/repeat** :
- état naturel / censuré pour chacun ;
- même gagnant ou gagnant différent (seulement si
  les deux parties sont naturelles) ;
- même séquence d'événements sélectionnés par
  \`audit_matched_replay.py\`
  (pile, terrain, vie, mana, blessures) ou divergence ;
- première divergence observée et son tour global,
  nombre de \`TimeoutException\` dans chaque run ;
- empreintes SHA256 des deux traces Forge complètes.

Le comparateur refuse la moindre différence de
decks, profiles, pod, sièges, seed et horloge, ainsi
que les matrices incomplètes. Il publie distinctement
accord sur le vainqueur et concordance des séquences
d'événements. Les séquences comparées sont un
**sous-ensemble choisi d'événements**, pas la
trajectoire complète de tous les objets Forge;
un hash de transcript mesure la concordance
exacte du texte brut.

**Aucune donnée de ce double run ne doit être
additionnée à l'estimation indépendante 32 jeux
comme si on avait testé 64 graines différentes.**
La divergence de Forge doit être étudiée comme
un défaut potentiel de reproductibilité / qualité
du simulateur, sans attribuer automatiquement
la cause au seul \`AI_TIMEOUT\`.

Le workflow et sa publication d'artefacts
sont indépendants de l'audit principal de résultats
32 jeux. Lire ses logs GitHub et vérifier
le statut complet avant d'en rapporter les chiffres.


## 23. Résultat définitif V12 sur 32 vrais matchs et V13 créée

### V12 : certification RECONSTRUITE sur les transcriptions réelles

**Source de vérité finale** (remplace le premier
rapport 28/32, qui contenait 3 faux rejets) :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002649987

- **32 matchs V12** réellement exécutés sur 16 shards
  avec 2 pods ×4 positions ×4 parties/pod-siège ;
- **31 parties naturelles certifiées**, **1 vraie
  \`clock_censored\`** à 360 s, 0 autre rejet ;
- **1 victoire Brimaz / 31 naturelles = 3,23 %** ;
  Wilson 95 % **[0,57 % ; 16,19 %]** ;
- 21/31 parties naturelles **sans aucun avertissement
  des quatre signatures IA actuellement surveillées** ;
  cette unique victoire Brimaz est également
  sans avertissement IA ;
- Pod aristo : 15 certifiées, 0 Brimaz,
  23 timeouts IA, 3 repli(s) d'attaque ; podium :
  Tazri (Dungeon) 10, Zimone&Dina 3, Radha 2 ;
- Pod artifact : 16 certifiées, 1 Brimaz,
  10 timeouts IA, 0 repli attaque ;
  Amalia 8, Urza 4, Lathril 3, Brimaz 1 ;
- Nombre total de \`java.util.concurrent.TimeoutException\`
  **33** (10 parties touchées) ;
  281 décisions terminées mais lentes >1000 ms.
  **32/33** échantillons de stack attribués au
  calcul profond des combats/bloqueurs,
  1 au recalcul de capacités statiques ;
- 4 usages du mulligan gratuit spécifique V9 ;
  Brimaz a été joué **dans 31/31 jeux naturels**,
  médiane de premier cast tour personnel **4**,
  seulement deux casts après tour personnel 6 ;
- 118 textes d'effets Incubate **résolus**
  (principalement triggers), 123 activations
  de transformation d'Incubateurs ; **0 warning
  \`No AI assigned for API: Incubate\`** ;
  aucun lien de causalité de winrate attribuable
  à la simple disparition du warning ;
- médiane de 12 tours personnels du joueur
  le plus actif, source humaine médiane ~9
  rotations : les unités ne sont PAS égales
  après élimination / tours supplémentaires.

### Faux rejets par blessures de commandant — corrigés

En relisant les 4 anciens « rejets » du premier
rapport, on a trouvé que 3 avaient **quatre**
\`Game Outcome\` Forge parfaitement légales :
les perdants étaient notés
\`has lost due to accumulation of 21 damage from generals\`.
\`scripts/forge_result_evidence.py\` accepte
maintenant **strictement cette formulation précise**
et refuse toute cause \`due to\` inconnue.
\`describe_outcome_modes\` distingue désormais
\`commander_damage_21\` des \`life_total_zero\`,
\`library_depletion\`, \`poison\`.
5 pertes par blessures de commandant dans les
31 jeux certifiés. La seule partie véritablement
exclue est \`aristo/seed 20310001\` : arrêt
à 360 s avec vainqueurs contradictoires.
**Ne jamais attribuer de victoire à une partie
arrêtée artificiellement.**

81 tests Python réussis :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002628580

### Victoire Brimaz « propre » V12, mais pas une preuve de 20 %

Graine \`20610001\`, pod artifact, rotation0,
siège Brimaz1, durée 139570ms :
- Brimaz \`Ai(1)\` gagnant naturel ;
- Lathril, Urza, Amalia perdent tous à 0 PV
  selon Forge ;
- **0 TimeoutException, 0 déclaration d'attaque
  invalide, 0 avertissement Incubate,
  aucune signature fatale surveillée** ;
- nombreuses attaques de créatures Phyrexian
  en fin de match, incubes transformés,
  attaques Brimaz et autres tokens. Ne PAS
  affirmer qu'il a causé directement chacune
  des 3 morts sans attribution détaillée.
- Source : artefact
  \`brimaz-v12-32-artifact-r0-s20610000\`
  du run 38001534517. La certification finale
  accepte explicitement cette victoire,
  y compris dans \`warning_free_wins\`.

### Répétabilité du moteur (mêmes graines 32 fois rejouées)

Rapport https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002258622 :
- 32 paires pod/graines/sièges identiques,
  30 paires de matchs naturels dans les deux runs ;
- 25/32 **mêmes séquences d'événements sélectionnés**,
  7/32 divergences d'actions ;
- parmi les 30 paires doublement naturelles :
  **29 mêmes vainqueurs, 1 vainqueur différent**.
C'est un progrès de mesure, **PAS 64 graines
indépendantes**, ni une preuve de déterminisme
complet. Les événements retenus sont pile,
terrains, vie, mana, dégâts. Les logs bruts
restent disponibles pour analyses détaillées.

### Prochaine direction technique : V13 fair adaptive timeout

Puisque Brimaz est maintenant joué dans
31/31 sorties naturelles et que les timeouts
se concentrent sur le combat, l'expérience
V13 superpose à V12 (Incubate AI + V9
mulligan et déploiement) la gestion de délai
**commune aux 4 IA** déjà pilote V11 :
\`Game.AI_TIMEOUT=5\` par décision au départ,
puis 10s après premier vrai timeout, 15s
après le second, toujours global pour tous
les sièges. Pas de règles Magic ou de cartes
modifiées ; une décision déjà expirée
reste abandonnée, et le CPU peut augmenter.
Le code est dans
\`scripts/patch_forge_brimaz_v13.py\`,
trace \`AI_ADAPTIVE_BUDGET_V13\`.
\`scripts/audit_adaptive_ai_budget.py\` reconnaît
maintenant V11 et V13, avec vérification
anti-régression et anti-mélange de versions.

**Pilote V13** :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002838904
8 jobs GitHub simultanés (2 pods ×4 rotations),
2 matchs par job = **16 jeux**,
bases aristo \`20710000\`, artifact
\`20810000\`, graine +=10000*rotation+repeat,
horloge 360s, délai process 445s,
résultats toujours contrôlés via les vrais logs.
Il était \`in_progress\` au dernier contrôle.
V13 peut réduire les interruptions,
mais **ne doit PAS être déclarée supérieure**
avant audit des décisions, règles et coûts CPU.
Test Java IncubateV12 + V9 Mulligan et tests
Python de budget adaptatif.


## 24. Couverture d'APIs Forge vérifiée et CI portée à 88 tests

Rapport [\`V12/32 missing AI handlers\`](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38003057234)
**SUCCESS** :
- 32 vrais transcrits vérifiés, **0 warning**
  \`No AI assigned for API: ...\` ;
- dictionnaire \`missing_api_counts={}\` pour les 7
  decks utilisés en V12.
  Attention : **ne prouve PAS** qu'il n'existe
  aucun autre gestionnaire manquant pour
  l'ensemble des cartes Magic, seulement
  qu'aucun n'a été rencontré dans ces 32 parties.
- Scripts \`scripts/audit_missing_ai_handlers.py\`
  et \`tests/test_missing_ai_handlers.py\` (5 cas),
  aucune modification du moteur de règles.

La [suite permanente de CI](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38003081740)
passe maintenant **88 tests Python** et les
4 parties de régression V6 sont encore
certifiées, conformément au niveau
d'exigence sur les résultats et les pertes
par 21 blessures de commandant.

Détail supplémentaire du rapport V12/32 :
- la couverture des sorties initiales n'est plus
  le premier point faible : Brimaz lancé 31/31,
  première invocation médiane au quatrième tour
  personnel ; 4 mulligans gratuits V9 déclenchés ;
- les cartes en cours d'évaluation lors des
  dépassements fréquents incluent
  \`Soul of New Phyrexia\` (6),
  \`Basilisk Gate\` (5),
  \`Elvish Warmaster\` (5),
  \`Ezuri, Renegade Leader\` (5),
  \`Magic Damper\` (3), etc. ;
- ces cartes sont les dernières candidates
  examinées par Forge au timeout, **pas
  nécessairement des cartes dont la
  résolution est illégale**, ni une preuve
  que la carte est la cause algorithmique
  complète du délai ;
- la prochaine optimisation devrait s'appuyer
  sur une **mesure de coût de simulation de
  combat** et un contrôle de non-régression
  tactique contre tous les adversaires.

Le V13 16-jeux
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38002838904
est la prochaine expérience de mitigation :
allocation 5 -> 10 -> 15s équitable pour tous.
Ne pas conclure avant le job de certification
indépendant et le rapport CPU/timeout. Un
changement de vainqueur avec la même seed
peut venir de la non-détermination du moteur.


## 25. Vérification indépendante de V13, sans relancer les 16 parties

Workflow
[brimaz-v13-16-independent-certification.yml](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38003422030)
déclenché avec le code consolidé et les **88 tests
de régression Python** existants. Il attend
le statut terminal des **16 jeux** V13 du run
**38002838904**, puis télécharge les artefacts
des **8 jobs déjà exécutés**, sans rejouer.
La matrice de 16 parties est
aristo seeds \`20710000 + 10000*rotation + repeat\`
et artifact seeds \`20810000 + 10000*rotation + repeat\`,
4 rotations par pod, 2 repeats, horloge 360s.

Il utilise les 16 vrais journaux Forge et :
- \`certify_commander_games.py\` : états 4 joueurs
  distincts, Scryfall, vainqueur, partie naturelle,
  délais, motifs de pertes y compris 21 blessures
  de commandant ;
- \`audit_balanced_commander_campaign.py\` :
  SHA256 réel du log égale certificat, 8 groupes,
  16 graines distinctes et 4 positions Brimaz
  équilibrées, Wilson 95%, listes de censures,
  résultats par pod/siège, victoire « sans
  avertissement IA » séparée du résultat naturel ;
- \`audit_adaptive_ai_budget.py\` : confirme
  chaque passage global 5→10→15 seconds
  déclenché UNIQUEMENT par un timeout, pour les
  quatre sièges ;
- \`audit_ai_eval_hotspots.py\` et
  \`audit_missing_ai_handlers.py\` :
  cartes candidates, coût AI, API non supportées ;
- \`audit_brimaz_combat.py\` : comptabilise
  uniquement les déclarations et dégâts
  directement attribuables aux attaquants
  sur le même tour (jamais des kills inférés).

Artefact à relire :
\`brimaz-v13-independent-16-game-certification\`
(\`balanced-games.json\`, \`adaptive-decisions.json\`,
\`ai-hotspots.json\`, \`missing-ai-apis.json\`,
\`brimaz-combat.json\`, \`certification/certificate.json\`).
**À la rédaction, le travail V13 était encore
en cours (6/8 shards terminés), pas de verdict
final enregistré**. Toute victoire vue dans
\`FINISH\` doit être recertifiée avant annonce.
La comparaison V12/V13 sur les mêmes graines
n'a pas encore eu lieu : des jeux à graine
identique peuvent diverger spontanément, et
V12/32 seed cohort précédent est distinct
de celui utilisé en V13/16.


## 26. CHANGEMENT D'ARCHITECTURE — deckbuilding rapide A/B générique (10 octobre)

### Motivation : ARRÊTER les dizaines de versions Forge

L'utilisateur souhaite avant tout **deckbuilder rapidement ses propres decks**.
Il ne veut pas que chaque remplacement de carte déclenche une
suite interminable de V14, V15, etc. Le nouveau chemin principal est
**un moteur de benchmark A/B stable et paramétrable**, conservant
Forge 2.0.15 + le correctif Charm et la politique IA V13
actuelle pour les quatre joueurs. Les correctifs moteur doivent
dorénavant être motivés par des bugs factuels,
pas par un incrément de numéro pour son propre intérêt.

**Mode d'emploi canonique** :
[docs/DECKBUILDING_QUICKSTART.md](DECKBUILDING_QUICKSTART.md).

### Implémentation effectuée dans la PR draft #1

- \`decks/Challenger.txt\` : clone initial strictement identique
  au \`decks/Brimaz_V3.txt\` canonique; **c'est le fichier
  à modifier** sur la branche
  \`improve/realism-and-ai-diagnostics\` pour tester un
  remplacement. Un commit de ce seul fichier déclenche
  le workflow même avant le merge (via \`on.push.paths\`).
  Ne JAMAIS interpréter un A/A initial comme une
  amélioration de deck. Ne pas écraser la source canonique.
- \`scripts/deckbuild_prepare.py\` : accepte liste complète
  (Moxfield \`1 Card\` / Forge \`.dck\`) pour référence et
  candidate avec commandant explicite, produit
  \`Deck_Reference.dck\` et \`Deck_Candidate.dck\`, contrôles
  100 cartes, SHA256, différence carte par carte et
  \`candidate-manifest.json\`.
- \`scripts/deckbuild_swaps.py\` : substitutions en une
  seule ligne \`1 Out -> 1 In; 2 Other -> 2 Another\`,
  total strictement conservé, commandant protégé.
  Le workflow \`workflow_dispatch\` permet l'option
  \`swaps\` et des fichiers alternatifs, lorsque la
  fonctionnalité Run workflow devient disponible.
  Attention : les actions manuelles d'un **nouveau
  workflow GitHub Actions** requièrent généralement
  que la définition soit sur la branche **par défaut**.
  Ne PAS fusionner la PR draft de force ; utiliser
  le chemin push/Challenger en attendant.
- \`scripts/deckbuild_run.py\` : pilote **générique**
  de quatre vraies IA Forge, 2 pods fixes, 4 sièges,
  2 bras A/B et graines appariées. Toute partie garde
  son transcript original, son statut et ses timeouts.
  Le launcher ne déclare pas qu'un win manifest =
  win certifié.
- \`scripts/deckbuild_certify.py\` : **nouveau
  certificateur** sans hypothèse sur le commandant
  (contrairement à des scripts anciens hardcodés
  sur \`Brimaz_V3\`). Accepte les pertes à 0 PV,
  deck-out et 21 commandant; exige quatre issues,
  Scryfall pour les 8 labels de decks et SHA256
  du log et du candidat, horloge naturelle.
- \`scripts/deckbuild_compare.py\` :
  résultats par bras, pod, siège et graine;
  Wilson 95%, bornes incluant les censures,
  avertissements IA, paires comparées sans
  prétendre que la RNG identique prouve une
  causalité A/B. \`comparison.json\` et
  \`certificate.json\`.
- \`.github/workflows/deckbuild-ab.yml\` :
  **un seul workflow de référence**.
  Job préparation : hash vérifier 7 decks canoniques
  existants, générer A/B, appel LIVE à Scryfall
  **pour les 2 candidats uniquement**, fail closed
  si carte illégale, identité couleur interdite
  ou Game Changer (Bracket 3 sans GC);
  réutilise audit légal historique des six adversaires.
  Ensuite **16 runners GitHub Actions parallèles**
  (2 bras x 2 pods x 4 positions), chacun joue
  \`repeats\` vraies parties JVM Forge.
  Réglage 1/2/4/6 répétitions : **16/32/64/96
  parties**. Une étape finale publie les métriques
  et téléverse un rapport certifié.
- \`.github/workflows/deckbuild-regression.yml\`,
  \`tests/test_deckbuild_pipeline.py\`,
  \`tests/test_deckbuild_swaps.py\` : vérif. hors-ligne
  des quantités, commanders, sièges, empreintes,
  vrais résultats et gestion honnête des censures.
- Pour les références Magic dont une carte
  est représentée comme une double-face
  \`Card A // Card B\`, vérifier la compatibilité
  avec la sérialisation Forge (le moteur peut
  ne connaître que la première face). La
  normalisation est déjà résolue dans les anciens
  scripts \`normalize_forge_decks.py\`.

### Première campagne de contrôle A/A (identiques)

Le workflow
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38004900250
a été lancé **automatiquement** lors de la création
initiale du workflow (quand sa définition incluait
un trigger push). Il utilise \`decks/Brimaz_V3.txt\`
dans les DEUX bras (mêmes 100 cartes), 16 parties
au total, 16 jobs en parallèle. Il s'agit d'un
**test de bout en bout de l'architecture**, pas
d'une amélioration de deck. Préparation,
SHA des 7 decks, et validation LIVE Scryfall
des deux candidats ont réussi. Les parties
étaient en cours au dernier contrôle.
**Il faut lire le job final \`report\` et
\`commander-deckbuild-certified-comparison\`
pour confirmer les certificats**. Attention :
les deux bras ont des identités de fichier et
noms de joueur différents, et le moteur Forge
n'est pas parfaitement déterministe; même
une différence de winrate A/A ne démontre
pas de changement de puissance.
Le workflow a ensuite été ajusté pour :
- réagir au **push de \`decks/Challenger.txt\`**,
  donc utilisable sur la branche draft actuelle ;
- accepter via \`workflow_dispatch\` un chemin
  candidat, un commander et des substitutions
  de cartes sans reconstruire une liste à la main
  (disponibilité UI conditionnée par GitHub).
Il ne se relance plus à chaque modification
du fichier YML.

### Résultat le plus récent de V13 (avant le comparateur)

[Run indépendant V13 38003422030 SUCCESS](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38003422030)
- 16 parties programmées, **14 naturellement
  certifiées**, **2 censurées**, 1 victoire Brimaz,
  **1 victoire sans avertissement IA**.
- Winrate observé **1/14 = 7,14 %**, Wilson 95 %
  **[1,27 % ; 31,47 %]** ; l'échantillon est
  trop petit pour donner un classement précis.
- **9 AI TimeoutException**, 0 attaque invalide,
  5 parties utilisant un budget adaptatif;
  5 hausses globales à 10 secondes, dont
  3 ont atteint 15 secondes. Ce résultat
  n'établit pas que V13 est plus intelligente que
  V12; les deux cohortes de graines sont différentes.
- Ne jamais fusionner les V12 31 parties et V13
  14 parties comme si toutes étaient soumises
  à une seule politique IA inchangée.

### Points de vigilance immédiats pour le prochain chat

1. Récupérer le run A/A \`38004900250\` et
   corriger toute faille révélée par le vrai
   workflow (artefacts, statut, noms, certificats),
   puis mettre à jour ce document.
2. Lancer une **vraie variante non identique**
   quand un changement de carte a été défini
   par l'utilisateur : modifier \`decks/Challenger.txt\`
   sur la branche; Scryfall gate obligatoire.
   Ne pas inventer la variante juste pour
   afficher une amélioration.
3. Prioriser les mécanismes qui font avancer
   la qualité du moteur pour **TOUS** les joueurs,
   surtout les calculs profonds de combat,
   avant des campagnes de centaines de parties.
4. Le nombre de parties prévu peut être augmenté
   via \`repeats\` et 16 runners ; tenir compte du
   coût GitHub Actions, de la censure et de la
   précision Wilson.
5. Le gain rapide à terme sera un cache de
   références réutilisable sur de multiples
   échanges de cartes UNIQUEMENT lorsque decks,
   Forge version, patch SHA, pods, profils,
   sièges, horloge et cohorte de graines
   ont tous des empreintes compatibles.
   Ne pas encore déclarer ce cache implémenté.


## 27. Contrôle final de bout en bout du nouveau deckbuilder : SUCCESS

Workflow A/B réel
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38004900250
**SUCCESS**, les 16 jobs Forge et le job
final \`report\` ont tous été exécutés (plus
le job \`prepare\` avec Scryfall et SHA256).
Ce premier run est un contrôle A/A :
\`reference_file=decks/Brimaz_V3.txt\`
et \`candidate_file=decks/Brimaz_V3.txt\` :
les **deux listes sont identiques**, seules
leurs identités de fichier Forge diffèrent.

Résultat \`DECKBUILD_CERTIFIED_RESULTS\` :
- **16 parties programmées, 16 naturelles
  indépendamment certifiées, 0 exclue/censurée**.
- **8 reference et 8 candidate certifiées**
  dans 2 pods et 4 sièges par bras.
- **0 victoire du deck dans chaque bras** :
  taux A = 0/8 = 0 %, taux B = 0/8 = 0 %,
  delta=0 ; intervalle Wilson 95% pour chaque
  taux [0 ; 32,44 %].
- **14/16 parties sans avertissement IA** ;
  **0 evaluation \`TimeoutException\`**, **2 replis
  d'attaque invalide** (1 par bras),
  **0 warning Incubate**, 0 threads bloqués.
- Même distribution de gagnants dans
  les deux bras : Dungeon/Tazri 3,
  Zimone&Dina 1, Urza 2, Lathril 2.
  C'est **une campagne de validation technique,
  pas une preuve que Brimaz ne peut pas gagner**
  ni qu'une variante est meilleure.
- Les huit couples pod/siège/graine sont tous
  présents et naturellement terminés,
  avec SHA256 de transcript accepté.
- La somme des durées *wall* par bras ≈
  1016 s et 1008 s (huit JVM parallélisées
  sur huit runners par bras); le temps utilisateur
  réel dépend du plus lent shard, ici les pods
  aristocrates ont pris plusieurs minutes.
  **Le coût Forge combat est toujours le
  goulot**, pas le calcul d'intervalles Wilson.
- GitHub Actions artifact à conserver :
  \`commander-deckbuild-certified-comparison\`
  (\`certificate.json\` et \`comparison.json\`).
- Tous les tests « courts » continuent à passer,
  dont run
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/38005338370 :
  **14 tests A/B +6 tests swaps +22 tests de
  certification historique**.
- La PR #1 reste volontairement en brouillon.
  Pas de merge automatique sur \`main\`.

### Principes à garder après la réussite A/A

1. Le comparateur générique est maintenant
   **fonctionnel de bout en bout** sur de vraies
   parties Forge EDH; ne pas re-développer
   le simulateur à chaque échange de carte.
2. Pour un vrai deckbuilding, modifier
   \`decks/Challenger.txt\` sur la branche ;
   cela déclenche immédiatement une campagne
   A/B à 16 parties. La fonction input
   \`swaps\` en workflow_dispatch permettra
   les échanges ponctuels dès que GitHub
   autorisera le run manuel sur la branche
   par défaut.
3. La campagne initiale clone identique
   a été effectuée sur un SHA antérieur
   à l'ajout de l'option de swaps et au
   refus explicite des partenaires non
   vérifiés ; les unit tests couvrent
   désormais ces deux aspects, mais
   ils nécessiteront une vraie nouvelle
   campagne seulement lorsqu'un candidat
   légal différent sera testé.
4. L'IA V13 corrige les avertissements
   Incubate et évite certains timeouts,
   mais n'est pas une IA experte.
   Pour accélérer davantage, rechercher
   des optimisations **prouvées
   équivalentes tactiquement** du
   \`ComputerUtilCombat\` / bloqueurs,
   puis vérifier des situations tactiques
   des quatre joueurs et le débit CPU.
5. Pour évaluer un effet limité de carte,
   16 parties ne suffisent généralement pas.
   Les options de campagne 32/64/96
   sont déjà en place, sans changement
   de version du moteur.


## 28. ACCÉLÉRATION STRUCTURELLE DU DECKBUILDING : CACHE VÉRIFIÉ + TOURNOI DE VARIANTES

**Objectif prioritaire demandé le 10 octobre 2026 :**
ne plus consacrer des dizaines de versions du moteur à de
simples changements de cartes. Accélérer le cycle
« modifier -> jouer de vraies parties -> certifier ->
comparer -> classer quelques bons candidats ».

### A. Cache de parties de référence vérifiables

Fichiers :
- \`scripts/deckbuild_cache.py\`,
  \`tests/test_deckbuild_cache.py\` (9 tests),
  \`.github/workflows/deckbuild-ab.yml\`.
- \`forge_decks/reference-cache-key.json\` est généré
  **après** la vérification Scryfall des deux candidats.

L'identité de référence prend **SHA256** sur :
- source et .dck Forge du deck de référence ;
- chaque deck des six adversaires dans les deux pods ;
- scripts \`patch_forge_charm_context.py\`,
  \`patch_forge_brimaz_v13.py\`,
  \`deckbuild_run.py\`, \`forge_result_evidence.py\` ;
- installeur officiel Forge 2.0.15 fixé par SHA256 ;
- profils, règle de délai, politique IA, horloge et
  limites de processus, pod, seat, rotation,
  TOUTES les graines déclarées, nombre de repeats.

Le workflow recherche **automatiquement** une exécution
antérieure **conclue SUCCESS**, avec artefact
\`deckbuild-verified-inputs\` et empreinte
\`reference-cache-key.json\`. Une référence sans
attestation, avec un seul paramètre différent
ou un log malformé est refusée.

- Cache absent : **16 runners, 16 vraies JVM** pour
  les répétitions=1 (8 référence+8 candidate).
- Cache exact : **8 runners, 8 nouvelles JVM**
  pour le nouveau candidat. Téléchargement des
  **8 journaux Forge originaux** de l'exécution
  antérieure (16 si repeats=2, etc.), vérification
  de chaque SHA256, seed, seat, profil, statut,
  liste de decks et politique IA. 
- IMPORTANT : même après vérification du cache,
  \`scripts/deckbuild_certify.py\` **recertifie tous
  les résultats à partir de leur transcription
  réelle** contre le deck de référence, les autres
  decks et la Scryfall légalité. Aucune issue
  censurée n'est convertie en victoire.
- Le nombre effectif de **JVM nouvelles** est diminué
  de moitié, mais l'effectif statistique
  **n'augmente pas**. Les résultats réutilisés
  sont strictement les mêmes jeux de référence,
  non des nouvelles parties indépendantes.
- Si \`reference_run_id\` est renseigné en lancement
  manuel, le workflow échoue explicitement si
  l'ancienne campagne n'est pas compatible.
- Lors d'un push \`decks/Challenger.txt\`, le workflow
  récupère les exécutions terminées précédentes
  via l'API GitHub, avec permission actions:read.
  Tout artifact sans clé de provenance (les
  anciens contrôles A/A par exemple) est rejeté,
  sans inventer une compatibilité.

### B. Classement de plusieurs modifications de cartes

Fichiers :
- \`scripts/deckbuild_compare.py\` inclut désormais
  \`reference_environment_fingerprint\`, la clé
  de référence complète, ainsi que
  \`reference_transcript_sha256\` et
  \`candidate_transcript_sha256\` pour chaque paire ;
- \`scripts/deckbuild_rank.py\` et
  \`tests/test_deckbuild_rank.py\` (8 tests) ;
- \`.github/workflows/deckbuild-leaderboard.yml\`
  (déclenchement manuel avec plusieurs IDs de runs,
  à utiliser lorsque GitHub expose ce workflow
  depuis la branche par défaut) ;
- Mode d'emploi détaillé :
  [DECKBUILDING_QUICKSTART.md](DECKBUILDING_QUICKSTART.md).

Les comparaisons multi-variantes n'acceptent
**QUE** les candidats partageant **les mêmes
SHA256 des huit vrais journaux de référence**,
le même patch, les mêmes graines, pods, profils,
commandant de référence et tailles de campagne.
Ils refusent un candidat dupliqué ou des traces
incomplètes. Résultat : \`candidates.json\`,
\`candidates.md\`, changement de cartes,
winrate, Wilson 95 %, censures et avertissements
IA. Le rang est un ordre de **présélection**,
jamais une preuve de supériorité statistique :
le tri de nombreux candidats introduit un
biais de sélection qu'il faut réévaluer sur
**de nouvelles graines**.

### C. Tests de régression

[CI PASS 59 tests](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38006243468) :
- 14 tests parsing/prep/certification A/B ;
- 6 tests substitutions une ligne ;
- 9 tests sécurité du cache ;
- 8 tests du classement multi-candidats ;
- 22 tests historiques issues Forge.
Tous les tests tournent sans Scryfall, Forge, ni
action de fond et échouent sur incohérences.

### D. Expérience réelle de qualification du cache

Nouveau A/A (Brimaz vs clone identique,
**aucun changement de carte**) :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38006057124

À la dernière vérification, le job de préparation
a réussi :
- SOURCE Forge, 7 decks canoniques hachés,
  Scryfall vérifié, la clé
  \`REFERENCE_CACHE_CREATED
  f7c8e3d85c430933470a7c9818f503fef47e3c9df41a815ac7e19c3173a71c1d\`
  a été créée ;
- ancienne campagne 38004900250 détectée mais
  refusée à juste titre car sans clé provenance ;
- 16 jobs de simulation réels déclenchés ;
  15/17 jobs complets (prepare + 14 shards),
  les rotations 2 du pod aristo en cours ;
- n'annoncer ni résultats certifiés ni taux
  jusqu'au passage du dernier job \`report\`.

**Action suivante indispensable :** vérifier le
run 38006057124. S'il est SUCCESS et l'artefact
\`deckbuild-verified-inputs\` contient bien
\`reference-cache-key.json\`, faire un second
push (simple commentaire de suivi dans
\`decks/Challenger.txt\`, sans changer les cartes)
et vérifier empiriquement :
\`REFERENCE_CACHE_HIT from run 38006057124\`,
matrice de **8 jobs candidats** (contre 16
au premier run), huit logs d'origine recertifiés,
huit nouvelles JVM candidates, rapport final
\`natural_certified_matches=16\`. 
NE PAS AFFIRMER QUE LA RÉUTILISATION EST
VALIDÉE DE BOUT EN BOUT AVANT CET ESSAI.
Si un autre membre du dépôt modifie un script
de patch Forge ou les decks avant l'essai,
le cache doit refuser et les 16 jeux doivent
être rejoués, ce qui est attendu.

### E. Suites réellement importantes

- Optimiser les simulations de calcul de combat
  de TOUS les adversaires sur situations
  déterministes (sans modifier règles Magic
  ni forcer un résultat), et comparer CPU,
  comportement tactique et qualité de l'IA ;
- réaliser des présélections structurées de
  3 à 10 candidats (même ligne de base),
  puis confirmation sur nouvelles graines ;
- élargir les pods adversaires réalistes et
  les styles de joueurs une fois le moteur
  stable ; ne pas promettre le véritable
  winrate humain de Brimaz basé uniquement
  sur sept decks fixes et les heuristiques Forge.
