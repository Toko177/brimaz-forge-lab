# Commander Deckbuilder — passer d'une idée de cartes à des parties Forge réelles

## But et périmètre

La voie d'usage courante du laboratoire est désormais le **comparateur A/B de listes**
et **non** une série V14, V15, V16, etc. Un changement de cartes ne requiert
plus de modifier le Java Forge ni de créer un nouveau workflow.

- **Deux listes Commander complètes de 100 cartes**, avec **un seul commandant
  explicite par liste**. Les deux commandants peuvent différer,
  mais la stratégie du bot n'est pas automatiquement experte pour chacun.
  Les paires `Partner`, `Choose a Background` et assimilées
  sont **refusées pour l'instant** : la simple présence de deux cartes
  en zone de commandement ne suffit pas à vérifier leur légalité.
- **2 pods fixes** : aristo (Radha, Dungeon/Tazri, Zimone et Dina) et artifact
  (Lathril, Urza, Amalia).
- **Quatre sièges équilibrés** pour chaque liste : Brimaz ou le nouveau
  commandant occupe tour à tour les quatre places.
- Le vrai moteur **Forge 2.0.15** applique les règles du jeu, avec le
  correctif Charm et l'IA **V13 (Incubate + budget adaptatif partagé
  aux quatre adversaires)**. Les choix sont de vraies heuristiques Forge,
  pas encore une IA experte.
- Les résultats sont indépendamment **certifiés** : les quatre issues,
  le vrai vainqueur, le chrono, les pertes par 21 blessures de commandant,
  les logs hachés et les validations Scryfall.
- Les résultats **censurés ne deviennent jamais des victoires**.

## Utilisation immédiate sur la branche expérimentale

Tant que la PR #1 est en **brouillon** et que ce workflow n'est
pas présent sur la branche par défaut, la manière la plus sûre de
le déclencher est :

1. Ouvrir [decks/Challenger.txt](../decks/Challenger.txt) sur
   la branche \`improve/realism-and-ai-diagnostics\`.
2. Modifier uniquement les quantités et noms des cartes de cette
   liste. Pour commencer, remplacer **une carte par une autre**,
   en conservant les 100 cartes et \`1 Brimaz, Blight of Oreskos\`.
3. **Commiter le fichier sur cette branche**. Le workflow
   [Fast Commander deckbuilding A/B](../.github/workflows/deckbuild-ab.yml)
   est déclenché par cet événement, en utilisant la liste
   \`decks/Brimaz_V3.txt\` comme référence et \`decks/Challenger.txt\`
   comme variante.
4. Consulter le job \`report\` et télécharger
   l'artefact \`commander-deckbuild-certified-comparison\`,
   qui contient \`certificate.json\` et \`comparison.json\`.

**Attention :** un commit créant uniquement un nouveau fichier,
par exemple \`decks/candidates/another.txt\`, ne déclenche pas
automatiquement ce chemin de démarrage rapide. Il faut modifier
\`decks/Challenger.txt\` ou utiliser le déclenchement manuel
dès qu'il est disponible sur la branche par défaut.

## Lancement manuel avec des échanges de cartes (après activation sur la branche par défaut)

Depuis GitHub → Actions → **Fast Commander deckbuilding A/B** →
Run workflow, renseigner :

- \`reference_file\` : \`decks/Brimaz_V3.txt\`.
- \`candidate_file\` : chemin d'une autre liste, si déjà présente dans
  le dépôt.
- \`swaps\` : facultatif, par exemple
  \`1 Plains -> 1 Swamp; 1 Sol Ring -> 1 Arcane Signet\`.
  Lorsque renseigné, ce champ prend le dessus sur \`candidate_file\`.
  Il autorise les quantités \`2 Card Out -> 2 Card In\`, conserve
  le commandant et les 100 cartes ; la légalité complète est ensuite
  contrôlée via Scryfall **avant** de faire tourner Forge.
  L'exemple est purement syntaxique, **pas une recommandation**
  de remplacer Sol Ring.
- \`reference_commander\` et \`candidate_commander\` :
  obligatoires lorsque les listes ne contiennent pas de section
  \`[Commander]\` ; pour le workflow, Brimaz est leur valeur par défaut.
- \`repeats\` : \`1\`, \`2\`, \`4\` ou \`6\`.
- \`seed_base\` : cohorte RNG déclarée à l'avance ; les deux variantes
  utilisent les mêmes valeurs, sans que cela garantisse des décisions
  déterministes ni une causalité statistique.

La disponibilité de **Run workflow** pour une nouvelle définition
GitHub Actions dépend notamment de sa présence sur la branche
par défaut. **Ne pas fusionner automatiquement la PR #1 pour
contourner cette limitation** tant que les contrôles de qualité
et la revue du code ne sont pas satisfaits.

## Tailles et coûts de calcul

| Réglage | Groupes | Joueurs | Parties réelles | Runners parallèles maximum |
|---|---:|---:|---:|---:|
| 1 répétition | 2 | 4 | 16 (8 référence + 8 variante) | 16 |
| 2 répétitions | 2 | 4 | 32 | 16 |
| 4 répétitions | 2 | 4 | 64 | 16 |
| 6 répétitions | 2 | 4 | 96 | 16 |

Pour écarter rapidement une variante très faible, commencer à
16. Pour une décision de deckbuilding moins incertaine, passer
à 32–96. Ce n'est **pas une garantie de précision statistique**,
notamment si la différence réelle est faible, les matchups
peu représentatifs ou les parties non certifiables nombreuses.
Éviter de choisir après coup la graine qui fait gagner son deck.

Chaque job conserve ses logs bruts. Le coût le plus important
est la simulation de Forge, pas le calcul de l'intervalle de
confiance ; un lancement à 96 parties consomme réellement
plus de calcul GitHub.

## Ce que le rapport prouve — et ne prouve pas

\`comparison.json\` fournit :
- les decks de référence et candidat (SHA256 de la source et de
  la liste Forge, et **détail des cartes ajoutées / retirées**) ;
- parties programmées, **naturelles certifiées** et censurées,
  victoires / taux / Wilson 95 % pour chaque bras ;
- **bornes conservatrices** de taux rapportées aux parties
  programmées, si des parties sont censurées ;
- distribution des adversaires gagnants, résultat par pod et
  par siège, décisions IA interrompues, attaques invalides ;
- paires par pod, siège et graine, à interpréter de manière
  **descriptive** : l'IA Forge peut diverger même à graine
  identique.

L'absence d'avertissements IA n'est pas la preuve de décisions
parfaites. Un \`1/4\` ou \`1/16\` ne suffit pas à classer des decks
sur un format multijoueur aussi variable. Et **un taux de
victoire plus élevé ne doit jamais provenir d'un bonus caché,
d'un handicap adversaire ni de règles simplifiées**.

## Architecture technique (pour reprendre ce chantier)

- \`scripts/deckbuild_swaps.py\` : échanges écrits sur une seule ligne,
  protection du commandant, contrôle de quantité.
- \`scripts/deckbuild_prepare.py\` : parseurs de listes,
  sérialisation Forge, SHA256 et diff carte par carte.
- \`scripts/deckbuild_run.py\` : runner générique en JVM indépendantes,
  profils et adversaires constants, matrice à quatre sièges.
- \`scripts/deckbuild_certify.py\` : auditeur indépendant
  Forge/Scryfall, vrai résultat 4 joueurs, empreinte du log,
  type de victoire, censures et avertissements IA séparés.
- \`scripts/deckbuild_compare.py\` : rapport A/B avec
  appariement descriptif, Wilson 95 %, répartition par siège,
  qualité IA et proportion de parties non certifiables.
- \`.github/workflows/deckbuild-ab.yml\` : préparation et légalité
  une seule fois, puis **16 jobs parallèles** référence/variante/pod/siège.
- \`.github/workflows/deckbuild-regression.yml\` : tests Python très
  rapides pour tous les contrôles précédents.
- \`tests/test_deckbuild_pipeline.py\` et
  \`tests/test_deckbuild_swaps.py\` : garde-fous locaux sans téléchargement
  de Forge ni Scryfall.

La vérification de bout en bout sur une **copie strictement
identique** de la liste de Brimaz est un **test d'infrastructure** :
une différence de vainqueur dans ce contrôle doit inciter à
étudier la non-reproductibilité ; elle ne constitue évidemment
pas une amélioration de deck.

## Étapes structurantes suivantes, sans accumulation de versions

1. Stabiliser le comparateur sur une campagne témoin A/A.
2. Rendre le moteur IA assez efficace pour réduire les coûteuses
   simulations de bloqueurs, avec tests de non-régression
   **des quatre IA**, sans changement des règles.
3. Ajouter des bancs de tests tactiques (mulligan, première rampe,
   blocage, interaction, Incubate/sacrifice) pour filtrer en quelques
   secondes les décisions défectueuses avant un benchmark massif.
4. Conserver des résultats référence réutilisables **seulement
   si les hashes des decks, le code Forge, le profil des IA,
   les pods, l'horloge et la cohorte de graines correspondent** ;
   toute divergence doit invalider le cache et interdire
   les comparaisons trompeuses.
5. À terme, tester et comparer des variantes proposées depuis
   les cartes légales via une **présélection** fondée sur le
   rôle des cartes et le budget/puissance souhaités, puis
   réserver les vraies parties Forge aux candidates prometteuses.

Pour l'état courant des campagnes Forge et la passation du chat :
[PASSATION ACTIVE](PASSATION_ACTIVE_2026-10-10.md).


## Accélération majeure : les parties de référence sont réutilisables

Après une première campagne complète, les **8 parties de référence**
(2 groupes x 4 sièges x une répétition) peuvent être réemployées
lorsqu'on modifie seulement la variante. Le workflow parcourt
automatiquement les anciennes campagnes GitHub Actions *terminées
avec succès* et sélectionne une référence admissible.

La réutilisation n'est **pas** une fiction statistique ni une
simulation simplifiée : ce sont de vraies parties Forge
déjà jouées, dont chaque transcription d'origine est conservée
puis **recertifiée par le certificateur de la nouvelle campagne**.

L'empreinte de compatibilité couvre :
- le SHA256 du deck de référence, son contenu source et son commandant ;
- le SHA256 de chacun des six vrais decks adversaires ;
- la version officielle Forge 2.0.15 et le SHA256 de l'installeur ;
- les SHA256 des scripts de patch Java, du runner et des contrôles
  du moteur de résultats ;
- la version de politique IA, le profil des quatre sièges,
  l'horloge de jeu, le délai d'exécution ;
- tous les pods, rotations de sièges, graines et répétitions.

Le contrôle final exige aussi **les huit journaux complets SHA256**
(et, pour 2/4/6 répétitions, respectivement 16/32/48 journaux)
avant de réutiliser quoi que ce soit. Les anciennes
campagnes sans provenance vérifiable **ne sont pas admises**.

| Nombre de répétitions | Première campagne | Variantes suivantes avec cache compatible |
|---|---:|---:|
| 1 | 16 vraies parties | **8 nouvelles parties** |
| 2 | 32 | **16 nouvelles** |
| 4 | 64 | **32 nouvelles** |
| 6 | 96 | **48 nouvelles** |

Les jeux d'origine ne sont pas ajoutés plusieurs fois au
dénominateur : il s'agit des **mêmes références** réexaminées
contre chacune des variantes. Comparer deux variantes utilisant
des références différentes n'est pas autorisé pour un classement
commun.

Le workflow propose aussi le champ \`reference_run_id\` si
l'on veut **forcer** la référence d'une campagne précise.
Si celle-ci ne correspond pas exactement à l'empreinte actuelle,
le workflow **échoue plutôt que d'utiliser un faux cache**.
Quand ce champ reste vide, il recherche de manière automatique
une campagne compatible ; en cas d'absence il rejoue la référence.

**Limite importante :** un changement dans un fichier de patch Forge,
dans le deck de référence, le niveau de répétitions, les graines,
un des adversaires ou les profils invalide la réutilisation.
Une évolution de l'IA reste nécessaire lorsqu'une nouvelle
capacité est mal gérée ; elle impose alors de régénérer des références.

## Classement exploratoire de plusieurs variantes

Lorsqu'on dispose de plusieurs fichiers \`comparison.json\`
issus de campagnes différentes, le script
\`scripts/deckbuild_rank.py\` sait les réunir :

\`\`\`bash
python3 scripts/deckbuild_rank.py \
  --reports result_variant_A/comparison.json result_variant_B/comparison.json \
  --output results/deckbuild-ranking.json \
  --markdown results/deckbuild-ranking.md
\`\`\`

Il vérifie **l'égalité de l'empreinte complète et de chacun
des journaux originaux de référence**, la couverture des
graines et les identifiants différents des variantes. En cas
de désaccord, il refuse le classement.

Le rapport rassemble les changements de cartes, les victoires,
les parties non certifiables, les anomalies IA et l'intervalle
de Wilson de chaque variante. L'ordre sert uniquement à
**sélectionner les modifications à retester** : avoir examiné
beaucoup de candidats crée un biais de sélection. Un résultat
prometteur doit être confirmé sur un **nouveau groupe de graines**.

Les fichiers et tests correspondants sont
\`scripts/deckbuild_cache.py\`,
\`scripts/deckbuild_rank.py\`,
\`tests/test_deckbuild_cache.py\` et
\`tests/test_deckbuild_rank.py\`.


## Mesures disponibles sans attendre les parties

Chaque campagne effectue désormais **avant toute JVM Forge**
un rapport \`preflight.json\` basé sur l'API Scryfall :
terrains première face, cartes MDFC dont l'autre
face est un terrain jouable, courbe de valeur de
mana et différences de structure entre A et B.

**Mesure vérifiée sur le Brimaz V3 canonique** :
35 terrains première face +3 terrains sur
des versos modal DFC, soit 38 cartes ayant
une possibilité de terrain ; courbe moyenne
des 65 cartes non-terrain en première face
2,892 mana. Voir le [test Scryfall live
SUCCESS](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38006620330).
Le fait qu'une MDFC puisse être jouée comme
terrain ne garantit pas un land drop ;
aucun avantage de winrate n'est attribué
à ces chiffres isolés.

La sortie est intégrée aux artefacts certifiés
de chaque benchmark A/B. Pour détecter
une anomalie de courbe de mana évidente,
**ce préflight ne coûte aucune partie Forge**.

## Classement dans GitHub Actions (quand Run workflow est disponible)

Le workflow
[Rank multiple Commander deck variants](../.github/workflows/deckbuild-leaderboard.yml)
accepte \`comparison_run_ids\` avec deux à vingt
identifiants de campagnes A/B terminées,
séparés par virgules. Il télécharge leurs
rapports, contrôle les empreintes de
tous les vrais matchs de référence, puis
publie \`candidates.json\` et
\`candidates.md\` dans l'artefact
\`commander-candidate-ranking-provenance-checked\`.

Seules des variantes réellement différentes
et basées sur le même environnement et les
mêmes logs de référence peuvent être
comparées. Il ne s'agit pas d'une preuve
de supériorité : confirmer la variante
prometteuse avec un nouveau lot de graines.
