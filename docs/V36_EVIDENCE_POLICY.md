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
