# Protocole de fiabilité — simulations Brimaz EDH à 4 IA

Dernière révision : 9 octobre 2026. Objectif : obtenir des **victoires réelles et vérifiables**, jamais des victoires obtenues en désactivant les règles, en modifiant secrètement les adversaires, ou en sélectionnant les graines favorables.

## 1. Légalité des decks (validée)

Les sept decks du laboratoire ont été vérifiés avec l'API Scryfall : 100 cartes commandant compris, identité couleur, règle de singleton et légalité Commander. La V3 Brimaz ne contient **aucun Game Changer** dans les données Scryfall consultées. Les decks de Lathril et Amalia contiennent respectivement 1 et 2 Game Changers, donc les résultats ne doivent pas être présentés comme s'ils avaient exactement les mêmes restrictions de construction.

Run : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37965067128

## 2. Chargement fidèle dans Forge (validé)

**Problème découvert :** les exports Archidekt de certaines cartes à deux faces utilisent des noms composites tels que `Selfless Glyphweaver // Deadly Vanity`. Forge 2.0.15 conserve le nom de la face principale pour l'entrée de la carte ; le nom composite pouvait être rejeté, entraînant des cartes manquantes et des `NullPointerException` liées à l'IA.

Pour chaque deck :
- conserver l'original archivé **sans suppression ni remplacement de cartes** ;
- traduire seulement le nom composite en nom de la face principale ;
- enregistrer les mappages et les hachages SHA-256 ;
- charger chaque carte dans la véritable base interne de Forge avec `StaticData.instance().getCommonCards().getCard` ;
- échouer si une seule des 100 cartes d'un deck manque.

**Résultat vérifié : 7/7 decks, 700/700 cartes (avec copies de terrains de base), 610 lignes individuelles.**

Run : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37966009166

## 3. Victoire naturelle et audit des exceptions (opérationnel)

Chaque processus doit être une partie réelle de Forge à quatre IA utilisant un deck Commander complet par siège. Le validateur exige :
- quatre sièges IA identifiables ;
- exactement un résultat de victoire dans le transcript brut, concordant avec le fichier résultat ;
- au moins un tour numéroté et le format Commander ;
- partie terminée naturellement, **sans** arrêt de l'horloge ou exception Java fatale ;
- code de sortie Forge égal à zéro ;
- hachage du transcript pour audit ;
- Scryfall validation présente pour tous les participants.

Les parties incomplètes, celles touchées par des exceptions et celles ayant un résultat non cohérent sont **exclues**, jamais transformées en victoires arbitraires. Les victoires ne sont ni inventées ni corrigées après coup.

Audit historique V3 : 13 parties admissibles / 16; trois rejetées (dont deux avec exceptions), toutes utilisant encore les anciennes identités de cartes Archidekt. Ne **pas** citer ces campagnes comme tests de compétitivité fiables.

Run : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37965442687

## 4. Expérience contrôlée sur les decks canoniques

Workflow : [canonical-benchmark.yml](../.github/workflows/canonical-benchmark.yml)

- Deux tables fixes de decks réels du playgroup.
- Quatre rotations de siège pour Brimaz, deux graines prédéfinies par siège.
- Forge 2.0.15 identique et authentifié ; modèle `stock` contre IA Brimaz V4 **qui ne modifie que la prise de décision**, pas les règles Magic.
- 16 parties par politique, 32 parties au total, sur 16 tâches GitHub Actions dont 8 en parallèle.
- Chaque tâche vérifie les 7 hachages de decks normalisés avant lancement ; agrégation et certification automatique à la fin.
- Toutes les parties doivent rester dans le rapport, y compris les défaites et les parties censurées ; **aucune sélection opportuniste de seed**.

## 5. Ce que ces certificats NE prouvent PAS

- Forge n'est pas une implémentation formellement vérifiée de toutes les interactions Oracle Magic. Une carte reconnue n'est pas la garantie que chacune de ses capacités est correctement pilotée par l'IA.
- Scryfall garantit la légalité des cartes, pas le niveau réel d'un deck Bracket 3 ; la présence de Game Changers est signalée séparément.
- La partie « conforme aux règles du moteur Forge » ne constitue pas un arbitrage humain de toutes les décisions.
- Aucune IA de Forge utilisée dans ce laboratoire n'a été démontrée équivalente à un joueur Commander expert.
- Des graines identiques n'assurent pas des tirages identiques si les comportements des IA divergent à cause de décisions différentes.
- 0 victoire dans un échantillon est une mesure du **couple deck + IA** et de son panel d'opposition, pas une preuve que la liste est incapable de gagner lorsqu'elle est pilotée correctement.

## 6. Correction du bonus poison

Brimaz peut proliférer un marqueur poison déjà présent, mais **aucune carte de Brimaz V3 n'a pour plan de produire du poison**. Le bonus poison artificiel des heuristiques V3 est retiré de la V4. Elle évalue davantage les synergies pertinentes : +1/+1, charges, mort de jetons, pertes de points de vie provoquées par Marionette Apprentice / Mirkwood Bats / Elas il-Kor et Scheming Aspirant.

La V4 est une politique expérimentale ; même si elle remporte une partie, cette victoire doit d'abord passer tous les contrôles ci-dessus.

## 7. Conditions d'acceptation à long terme

Rechercher une IA mieux pilotée avec des tests de situations précises, journalisation des options légales, score de l'action, résolution réelle de la capacité, puis comparaisons sans favoritisme. Les tours adverses, le combat et la capacité d'Incubation méritent une attention particulière. Un remplacement global d'`Incubate` par un mécanisme AlwaysPlay n'est pas validé comme une bonne IA.

Le vrai objectif n'est **pas d'obtenir une victoire à tout prix** ; c'est de mesurer correctement la puissance du deck dans des parties équitables.
