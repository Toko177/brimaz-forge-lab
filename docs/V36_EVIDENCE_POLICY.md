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
