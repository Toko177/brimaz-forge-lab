# Audit des 32 parties canoniques, première victoire et correction des exceptions
Date : 2026-10-09.

## Résultats observés, sans extrapolation

- 32 parties Forge 2.0.15 sur 7 listes **100 cartes entièrement reconnues**, avec positions tournantes et graines sauvegardées.
- 29 parties terminées avec un vainqueur naturel selon Forge et sans exception Java détectée ; 3 parties censurées par `-c 360`.
- **0 victoire de Brimaz parmi les 29 parties valides de la campagne initiale.**
- Les métriques du programme initial surestimaient la qualité des conditions de certaines parties historiques (recto-verso non reconnus) ; les listes canoniques ont été créées séparément.
- L'agrégation GitHub a échoué car sa clé de match n'incluait pas `policy` : collision sur les graines `stock` et `V4`. Correctif appliqué dans `scripts/aggregate_batch.py`; analyse ultérieure réussie.
- Les tâches individuelles GitHub sortaient avec un code non zéro dès qu'une partie dépassait l'horloge. Le nouveau `scripts/batch.py` conserve ce résultat comme `clock_censored` sans échouer le job pour cette seule raison ; les exceptions et les parties sans résultat restent des erreurs bloquantes.
- Le batch ne réécrit plus le fichier Brimaz validé lorsque `--require-canonical-decks` est utilisé.

## Défaut racine des trois parties bloquées

Les trois transcriptions contiennent une longue série de :
```
java.lang.NullPointerException:
SpellAbility.getActivatingPlayer() is null
TargetRestrictions.getAllCandidates
CharmEffect.makePossibleOptions
CharmEffect.makeFormatedDescription
Card.getAbilityText
ComputerUtilCost.checkDiscardCost
```
`CharmEffect.makeFormatedDescription` exécutait `makePossibleOptions` avant l'initialisation tardive du joueur activant. Les capacités modales exigeant une liste de cibles invoquaient le calcul sans joueur valide.

Correctif minimal `scripts/patch_forge_charm_context.py` : définir, si nécessaire, le joueur activant d'une capacité modale à partir de l'aptitude parente ou du contrôleur de la carte, avant de compter les cibles légales.

**Reproduction empirique :** les 3 graines précédemment problématiques n'ont plus présenté de `NullPointerException` avec le correctif. Deux sont restées censurées après 360 secondes ; une a terminé naturellement avec Brimaz vainqueur.

## Première victoire de Brimaz vérifiée séparément

Run : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744

- Série : correctif du seul bug Charm + IA Forge `Default` (ni politique V4 ni V5).
- Pod : `Brimaz / Radha / Tazri / Zimone & Dina`, sièges tournés (Brimaz siège 2).
- Graine `20291010`, partie terminée à **356 476 ms** du moteur, sous la limite de 360 000 ms ; tour 24.
- `Game Outcome` confirme : Zimone/Dina, Radha et Tazri ont tous perdu en atteignant **0 PV** ; Brimaz gagne parce que tous ses adversaires sont éliminés.
- Aucun crash Java identifié ; les quatre decks proviennent des listes canoniques Scryfall-legal, reconnues entièrement par Forge.
- Journal SHA-256 : `a3655fbb2e30ab53f581d96c3e6bb688296ef1842a6d2f8210e266e9aab85c1d`.
- **Attention** : ce match reprend volontairement une graine précédemment bloquée ; il ne doit pas être ajouté au 0/29 initial comme un trente-et-unième tirage aléatoire indépendant ni être utilisé comme estimation directe d'un taux de victoire après correction.

## Causes probables de la faiblesse de l'IA

- Sur la série initiale : **4/32 matchs sans lancement de Brimaz**, en moyenne 1,06 lancement par partie ; **26/32 sans déclenchement de prolifération au début d'une étape de fin détecté**. Cela ne quantifie pas les opportunités réellement légales et bénéfiques.
- Audit direct de la base Forge : **9 cartes de Brimaz marquées `AI:RemoveDeck:All`** : Phyrexian Delver, Orzhov Signet, Krark-Clan Ironworks, Spawning Pit, Phyrexian Reclamation, Tortured Existence, Diabolic Intent, Fetid Heath, Phyrexian Tower.
- Forge les filtre de sa liste habituelle d'actions (`AiController.getSpellAbilityToPlay`). Les capacités de mana peuvent être traitées par un autre mécanisme ; l'étiquette n'implique pas nécessairement une impossibilité de produire du mana.
- Ces exclusions portent sur des **outils centraux du deck**, en particulier tutorat, récursion et sacrifices. Elles peuvent expliquer la sous-performance par rapport au pilotage humain.
- Amalia gagne 12 des 16 parties de son pod cumulé (`stock` + `V4`), et possède deux Game Changers, alors que Brimaz n'en a aucun. Les pods ne sont pas tous strictement équivalents en restrictions de construction.

## Modifications d'IA

- V5 : Brimaz prioritaire lorsque légal/abordable en première phase principale et transformations d'Incubateurs valables. 8/8 parties certifiées, zéro victoire, 11 décisions prioritaires de lancer le commandant, 12 lancements ; 0 activation du planificateur de sacrifice et 0 priorité de transformation observées dans ce court test.
- V6 : accès **conditionnel** à Orzhov Signet, Spawning Pit et Krark-Clan Ironworks depuis la main ; moteur de sacrifice pour KCI sous contrôle de la politique d'état. Aucun coût, effet Magic, joueur adverse ou deck n'est modifié.
- **Ces modifications ne sont pas encore reconnues comme meilleures qu'un pilote humain.** Les adversaires utilisent leurs propres heuristiques Forge et peuvent être eux aussi affectés par leurs exclusions AI.

## Tests reproductibles

- Postmortem des 32 : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37968248090
- Exclusions réelles IA : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969381954
- Première victoire certifiée : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744
- Reproduction des 3 erreurs avec correctif : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37968565113
- Tests V5 : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969072177

## Limites permanentes

Une partie jouée dans Forge et sans erreur Java détectée n'est pas une preuve formelle que toutes les interactions MTG Oracle sont parfaites. Une victoire réelle sans bug détecté est **plus crédible** qu'un simple état `success` de GitHub Actions, mais seule une inspection exhaustive ou des tests de règles pertinents peuvent confirmer chaque interaction. Ne jamais sélectionner les graines pour maximiser artificiellement les victoires.
