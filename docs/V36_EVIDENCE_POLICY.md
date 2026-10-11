# V36 — Challenger Brimaz fondé sur des preuves locales

## Objectif et constat initial

Après 35 versions, aucune campagne n'a permis de démontrer un gain
statistiquement fiable contre Forge. Les scores abstraits V35, dont
les projections de cartes non piochées, ne prouvaient pas des choix
stratégiques supérieurs.

Le V17 original du projet **forçait déjà Brimaz** en phase principale
1 à chaque occasion payable. Ce comportement masque une erreur :
le test de menace considérait la force maximale d'une seule créature
adverse, pas la somme des créatures chez un adversaire capable de tuer.
Dès lors, prioriser « Brimaz avant un Phyrexian » n'est pas, à lui
seul, un progrès face à V17.

## Politique V36 réellement implémentée

- Classe `patches/java/forge/ai/MultiplayerEvidenceGateV36.java`.
  Trois interventions bornées fondées sur la main et le plateau réellement
  connus, et **vérifiées par `ComputerUtilCost.canPayCost`** avant
  approbation finale de `AiController.canPlayAndPayFor`.
- Lancement de Brimaz avant une créature Phyrexian réellement connue
  et abordable à horizon court ; un coût élevé fictivement ramené à
  3 n'autorise pas cette prévision.
- Lancement d'un Phyrexian alors que Brimaz est déjà effectivement
  présent pour son déclencheur d'incubation.
- Rocher de mana non-créature et immédiatement payable, lorsque le
  mana connu le tour prochain déverrouille le coût imprimé de
  Brimaz. Les producteurs souffrant du mal d'invocation comme Gold
  Myr ne sont pas pris pour des accélérateurs immédiatement sûrs.
- Jetons Incubateur non transformés **exclus** du nombre de créatures
  disponibles pour sacrifice.
- Sous forte pression adverse, la V36 s'abstient, et un second garde
  empêche le vieux `BrimazTurnPlanner.planDevelopment` de forcer
  un sort économique malgré un risque de dégâts cumulés.
  Le moteur reste libre de choisir une défense réelle et légale.

**Limite fondamentale :** lorsqu'elle s'abstient, V36 revient au
contrôleur **V17 Brimaz-aware**, lui-même modifié par nos correctifs,
et *non* à l'IA originale du JAR Forge inchangé. Les trois adversaires
du benchmark mixte utilisent strictement la même V17 dans les deux
bras. Seul le siège Brimaz possède le commutateur V36.

## Expérience et preuves

La politique `v36_brimaz_challenger` est opt-in avec
`brimaz.v35StrategicSearch=true`,
`brimaz.v35BrimazOnly=true`,
`brimaz.v36EvidenceGate=true`.

Java 21 compile les classes contre le vrai JAR Forge 2.0.15 ; les
tests synthétiques vérifient les sorties sur scénarios antagonistes.
Ils ne remplacent pas les résultats de véritables parties.

[Workflow de vraies parties](../.github/workflows/strategic-real-4ai-ab.yml) :
deux pods, rotations des quatre sièges, trois adversaires V17
constants, sept decks originaux vérifiés SHA256, nouvelles graines
`20270217`. Les erreurs et censures ne sont jamais des défaites.
Les résultats doivent être attribués à la bonne SHA avant toute
déclaration d'amélioration.

**Critère de validation non atteint à la création :** démontrer sur
des configurations indépendantes un avantage significatif et
reproductible, pas une hausse des propositions, ni un simple
changement de vainqueur. La PR reste DRAFT.

## V37 — test contrôlé face à l'IA Forge, et non la V17 héritée

La précédente politique V36 se repliait sur **V17** et l'effet réel
pouvait provenir des patches historiques Brimaz. Deux nouveaux bras
`v37_stock_control` et `v37_brimaz_challenger` utilisent donc
**les mêmes classes compilées et le même correctif moteur commun**.
Ils désactivent, de façon symétrique, les mulligans personnalisés,
les priorités automatiques de cast, la transformation forcée des
Incubateurs et les choix de sacrifice historiques. Les quatre sièges
partagent une même base Forge avec prise en charge commune des
incubations (ceci reste **une base compatible modifiée**, pas le JAR
strictement inchangé).

Seul le challenger autorise son siège Brimaz à proposer les lignes
connues de V36 et à utiliser un sacrifice de jeton Phyrexian de valeur
locale strictement positive avant l'étape de fin, vérifié par
`AiController.canPlayAndPayFor`. Les trois adversaires ne reçoivent
aucune politique nouvelle. L'auditeur vérifie SHA des decks,
égalité des patches, absence de flags globaux et siège unique.

Les nouvelles graines de la campagne sont `20270319`, différentes
des anciennes. Sans statistiques favorables sur un échantillon large,
la supériorité n'est toujours pas une conclusion autorisée.

## V37 — duel direct dans la même partie, à decks identiques

Le problème expérimental des campagnes précédentes était qu'un deck
Brimaz différent en qualité de ses adversaires pouvait ne quasiment
jamais gagner. Il fallait un bras de référence beaucoup plus proche.

`scripts/run_v37_mirror.py` crée, **dans un dossier temporaire**,
deux copies byte-identiques des 99 cartes et du commandant du deck
Brimaz canonique, avec seulement un champ `Name=` distinct.
Les deux sièges jouent dans **le même processus JVM Forge**, contre
les mêmes deux adversaires Kaal. Leurs positions sont tournées sur
les quatre sièges et sur deux pods. Les sept decks originaux du repo
sont relus et contrôlés SHA256 avant chaque campagne ; aucune
modification persistante n'est autorisée.

`brimaz.v37MirrorDuel=true` active la logique V37 **uniquement**
pour `Brimaz Challenger`. `Brimaz Reference` conserve les choix
Forge d'origine dans le même JAR ayant les correctifs communs ;
les anciens automatismes V17 sont désactivés symétriquement.
Les deux Kaal utilisent également la politique d'origine de
ce JAR compatible. Les journalisations de cast, de sacrifice et
de fin de partie sont conservées dans des logs Forge bruts.

Les résultats sont : victoires du challenger, victoires de la
référence, victoires des Kaal, parties censurées/invalides, puis
test binomial bilatéral conditionnel *uniquement* sur les duels
où l'un des deux Brimaz gagne. **Un petit échantillon,
un avantage de 1 victoire ou un test synthétique ne prouve pas
la supériorité générale d'une IA.** Les résultats des vraies
parties ne peuvent être annoncés qu'après exécution réussie.

### Benchmark miroir renforcé : quatre Brimaz identiques (2 V37 vs 2 Forge)

Le mode `--mode all-brimaz` lance quatre copies identiques du même
deck Brimaz — **deux challengers V37 et deux références Forge**, dans
une même partie réelle à quatre joueurs, avec rotation équilibrée des
sièges. Contrairement aux parties à deux Brimaz + deux Kaal, chaque
victoire naturelle revient nécessairement à l'une de ces deux
politiques. L'auditeur vérifie explicitement cet invariant et sépare
les parties censurées.

Ce test mesure **l'avantage relatif des deux politiques sur le deck
Brimaz en miroir**, et non une supériorité générale contre tous les
archétypes Commander. Le format à deux Kaal est donc maintenu comme
validation externe. Les deux expériences sont exécutées dans le
workflow existant (aucune nouvelle automation ni deck canonique
modifié). Le verdict d'efficacité reste conditionné aux nombres
réels de victoires, pas aux nombres de propositions IA.

#### Contrôle de reproductibilité et durée CI

Les jobs du miroir sont répartis en quatre lots indépendants de huit
parties : `all-brimaz / aristo`, `all-brimaz / artifact`,
`kaal-mirror / aristo` et `kaal-mirror / artifact`. Le protocole
préserve les mêmes sièges et les mêmes graines, tout en évitant qu'un
job unique de seize parties dépasse le timeout GitHub.

L'extracteur refuse désormais une victoire supposée du Challenger
ou de la Référence quand **le nom du gagnant annoncé dans le journal
Forge** n'est pas exactement celui du joueur attendu à ce siège.
Dans ce cas la partie est marquée `name_mismatch` : **ni victoire
ni défaite artificielle**. En mode quatre Brimaz, il vérifie que
chaque victoire naturelle est bien obtenue par une politique Brimaz.

## V38 — anomalie de ressources physiques diagnostiquée

Le premier véritable miroir `V37` avec deux Brimaz et deux
adversaires Kaal a terminé **14 parties naturellement sur 16** :
**0 victoire challenger, 2 victoires référence, 12 victoires Kaal**,
2 parties censurées/défectueuses. La mesure binomiale bilatérale
conditionnelle vaut `p=0.5` : ce n'est pas une preuve de régression.
En revanche **aucune action V37 de sacrifice n'a été approuvée**.

Une cause structurelle plausible est que la V37 attend une
créature Phyrexian sacrifiable, tandis que les permanents `Incubator
Token` créés par la capacité du commandant sont **des artefacts
non-créatures** tant qu'ils ne sont pas transformés. L'ancienne
transformation automatique V17 était explicitement désactivée
pour conserver le duel expérimental propre. Le challenger V38
ajoute un convertisseur endogène et prudent :

- `MultiplayerIncubatorTempoV38.choose` examine seulement les
  capacités `SetState/Transform` **réellement présentes** dans le
  moteur Forge sur des jetons `Incubator Token` contrôlés par le
  challenger et encore non-créatures ;
- le seuil `shouldTransform` dépend de la taille X, de la vie,
  des bloqueurs prêts et de la force agrégée du plus dangereux
  adversaire, en phase `MAIN2` et pile vide ;
- les coûts et contraintes de timing sont vérifiés avec
  `ComputerUtilCost.canPayCost`, `canPlay`,
  `canCastTiming`, puis **`AiController.canPlayAndPayFor`** ;
- chaque activation proposée et approuvée est journalisée sous
  `FOUR_AI_V38_TRANSFORM_PROPOSAL` et
  `FOUR_AI_V38_TRANSFORM_STOCK_APPROVED` ; **une seule**
  transformation proposée par tour ;
- aucune carte adverse cachée n'est consultée, et le bras de contrôle
  garde exactement les mêmes patches, sans le flag
  `v38IncubatorTempo`.

Le protocole Forge 2.0.15 + Java 21 avec **nouvelles graines
`20270903`**, quatre sièges, deux pods, quatre decks identiques
en 2v2 et un format de validation contre Kaal distingue maintenant
les transformations effectivement approuvées des victoires
naturelles. Cette hypothèse reste à confirmer par les parties ;
une classe Java compilable et des tests synthétiques ne démontrent
jamais à eux seuls une meilleure qualité stratégique.

## V39 — transformer un Incubateur **pour une raison mesurable**

[V38 — preuves réelles CI](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38152203947) :

| Expérience | Naturelles | Challenger | Référence | Kaal |
|---|---:|---:|---:|---:|
| 4 Brimaz identiques, première famille de graines | 8/8 | 6 | 2 | — |
| 4 Brimaz identiques, deuxième famille de graines | 8/8 | 2 | 6 | — |
| 2 Brimaz + 2 Kaal, Artifact | 7/8 | 3 | 0 | 4 |
| 2 Brimaz + 2 Kaal, Aristo | 8/8 | 1 | 0 | 7 |

**Attention :** les deux expériences « 4 Brimaz » ont exactement
**les mêmes quatre listes de cartes** : leur seule différence liée au
`pod` est un décalage de la graine aléatoire. Les résultats 6–2
puis 2–6 constituent une fluctuation sur petit échantillon,
**pas une différence entre les archétypes opposés**.
Le bilan **8–8** en miroir ne démontre aucun gain.

En revanche, le test contre Kaal montre quatre victoires pour V38
contre zéro pour la référence en 15 parties naturelles. La valeur
bilatérale conditionnelle de 4 succès sur 4 duels décisifs
est `p = 0,125`. Ce signal est encourageant mais faible :
les onze victoires de Kaal ne sont pas attribuées à l'une des deux IA.

**Nouvelle modification de gameplay V39 :** en plus de la V38,
`MultiplayerIncubatorEngineV39.minimumVisibleNetEngineValue`
évalue la rentabilité minimale d'une séquence future impliquant
un Incubateur transformé puis sacrifié : seul un petit Incubateur
de taille 2 à 4, un **vrai exutoire de sacrifice déjà sur table**,
Brimaz réellement présent et au moins assez d'autres permanents
déjà porteurs de compteurs pour un bénéfice net positif
justifient de privilégier cette transformation. Ce calcul
**n'assume pas** l'existence d'une future activation valide :
le véritable Forge valide séparément la transformation et, le cas
échéant, le sacrifice.

V39 refuse également d'interrompre un sort de ramp connu
et **actuellement payable** (Sol Ring, Arcane Signet, etc.)
pour transformer un artefact non urgent ; le garde ne s'applique
pas sous danger défensif sérieux. Les décisions enregistrent
`source=KNOWN_COUNTER_ENGINE` ou `DEFENSIVE_TEMPO`,
la marge de valeur observée, la présence de l'exutoire et
l'existence d'un ramp payable.

Le protocole V39 utilise des graines **indépendantes `20271119`**,
3 répétitions par rotation/pod (12 parties par shard,
48 parties miroirs) et 16 processus JVM appariés séparés.
Les quatre shards du miroir tournent dans le même workflow existant,
sans créer de branche, workflow ou deck canonique supplémentaire.
Les tests Java V39 ne simulent ni victoire ni capacité résolue.

## V39 : campagne terminée, résultat défavorable — correction V40

[Campagne V39, 64 processus réels](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38154331237), 6 jobs réussis :

- 4 decks Brimaz strictement identiques, famille de graines `artifact` :
  **9/12** parties naturelles ; V39 4 victoires, référence 5.
- Même miroir, famille de graines `aristo` : **11/12**
  naturelles ; V39 4 victoires, référence 7.
- Donc **8 victoires V39 contre 12 référence** dans
  les vingt miroirs réellement terminés.
- 2 Brimaz + 2 Kaal : **21/24 naturelles**, V39 2 victoires,
  référence 1, Kaal 18.
- 16 autres JVM appariées : 6/8 paires naturellement terminées,
  V39 0 victoire, référence 2.
- Les transformations sont effectivement approuvées dans Forge,
  mais les sacrifices positifs restent rares (une seule approbation
  sur les 48 parties miroir).

### Défaut de V38/V39 identifié dans le vrai code

`MultiplayerIncubatorTempoV38` conservait un **unique entier
`latestTurn` statique**, partagé par **tous les joueurs du même
processus JVM**. En miroir avec deux challengers, la proposition de
transformation du premier pouvait bloquer celle du second jusqu'au
tour suivant. Le verrou était en outre consommé dès la proposition,
même si Forge refusait l'activation. Le compteur de diagnostics de
sacrifice souffrait d'un problème analogue (observation du seul
premier joueur par numéro de tour).

### Correction V40, isolée et falsifiable

- Remplace ce verrou, lorsque `v40SeatScopedActions=true`, par un
  registre faiblement référencé **par identité du joueur et par tour**,
  résistant au cas « deux Brimaz challengers dans une partie ».
- Une tentative refusée **ne consomme plus** l'activation prévue :
  l'état est enregistré uniquement après `AiController.canPlayAndPayFor
  == WillPlay`, avant la remise de la capacité au moteur. Cela ne
  présume **pas** que la capacité s'est résolue.
- Les fenêtres de diagnostic de sacrifice sont également enregistrées
  par joueur et par tour de ce joueur ; elles ne se bloquent plus entre
  IA. La planification de sacrifice V40 ignore les phases principales
  adverses, car le but est le déclenchement de Brimaz à notre fin de tour.
- Les 10 nouveaux scénarios de test couvrent deux joueurs simultanés,
  une approbation par joueur, une nouvelle disponibilité au tour
  suivant et l'absence de verrou lors d'un rejet.
- La V39 reste activable sans ce changement, pour conserver la
  reproductibilité historique ; **la V40 seule** active le garde.

Un nouveau benchmark exploite les graines inédites `20280117`,
les mêmes 7 decks originaux vérifiés SHA256, les 4 sièges,
les deux formats miroir, et les campagnes appariées. Ce correctif
résout un biais dans le logiciel ; son **gain de victoires n'est
pas encore démontré**.
