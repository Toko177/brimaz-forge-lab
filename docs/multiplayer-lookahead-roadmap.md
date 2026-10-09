# Architecture cible : décisions Forge IA EDH à quatre joueurs

## Observations confirmées dans Forge 2.0.15

- `AiController.chooseSpellAbilityToPlay` possède deux voies : heuristiques habituelles et mode `USE_FULL_SIMULATION` (via `SpellAbilityPicker`).
- `GameSimulator` copie l'état de la partie, mais son traitement des réponses adverses appelle `getWeakestOpponent()` et contient un TODO explicite pour prendre en charge plusieurs adversaires. La gestion des contrôleurs des autres joueurs est également marquée TODO.
- `GameStateEvaluator` n'évalue pas correctement toutes les réponses possibles en même temps dans cette version : un chemin avance jusqu'aux dégâts de combat en résolvant la pile avec le plus faible adversaire.
- Activer `USE_FULL_SIMULATION` sur les quatre IA sans modifier cette logique serait **une expérimentation**, pas une amélioration multijoueur validée.

Sources dans Card-Forge/forge, tag `forge-2.0.15`:
- `forge-ai/src/main/java/forge/ai/AiController.java`
- `forge-ai/src/main/java/forge/ai/simulation/GameSimulator.java`
- `forge-ai/src/main/java/forge/ai/simulation/GameCopier.java`
- `forge-ai/src/main/java/forge/ai/simulation/GameStateEvaluator.java`
- `forge-ai/src/main/java/forge/ai/simulation/SpellAbilityPicker.java`

## Conception recommandée, non implémentée à ce stade

**1. Conservation du moteur de règles Forge**

Chaque séquence candidate est jouée sur une **copie réelle de l'état Magic**. Aucune simulation de tirage simplifiée ne remplace les règles de pile, combat, priorité, simultanéité ou effet de remplacement.

**2. Agents identifiables séparément pour les quatre joueurs**

Pour chaque état cloné, installer trois contrôleurs adverses distincts. Respecter l'ordre APNAP et la priorité/les passes. Ne pas réduire artificiellement les trois adversaires à `getWeakestOpponent()`.

**3. Recherche à budget fixe**

Au lieu d'explorer tous les coups légaux :
- présélectionner les coups par heuristiques de valeur, coût et létalité ;
- explorer profondeur 1 à 2, avec une seule réponse adverse ou quelques réponses critiques ;
- échantillonner les réactions adverses sous plusieurs politiques ;
- borner strictement le temps CPU et les nœuds explorés par décision ;
- retomber sur l'IA heuristique si budget épuisé, erreur de clone ou état ambigu.

**4. Évaluation adaptée à EDH quatre joueurs**

Fonction de valeur comportant au minimum :
- probabilité de survie aux trois adversaires et danger de létalité ;
- menaces majeures par joueur et risque d'élimination immédiate ;
- avancement des moteurs du commandant ;
- mana disponible sur le cycle complet, non uniquement le tour actif ;
- valeur des permanents, tokens, cartes et contre-mesures ;
- tempo et capacité d'interaction ;
- probabilité d'arriver aux prochains trois end steps ;
- pénalités explicites sur les actions irréversibles sans gain mesurable.

Pour Brimaz, mesurer particulièrement :
- statut `died this turn` pour chaque joueur actif ;
- compte de permanents alliés à marqueurs améliorables ;
- valeur d'un sacrifice Phyrexian avec et sans un end step supplémentaire ;
- potentiel de transformation et d'attaque des Incubateurs ;
- apport de cartes à marqueurs et moteurs de sacrifice ;
- risque de perdre un bloqueur pendant le tour adverse.

**5. Audit de correction / test anti-régression**

Enregistrer pour chaque décision : identifiant du tour, joueur actif, états visibles, candidats légaux, scores des options, action choisie, résolutions, changements de ressources et première cause d'échec.

Tester d'abord des états déterministes ciblés (un Phyrexian sacrifiable et un moteur disponible, puis états négatifs) et des parties réelles. Aucun gain de puissance ne sera affirmé avant une comparaison appariée sur des dizaines à centaines de parties complètes.

**6. Exécution parallèle**

Un processus Forge isolé par partie, un **job GitHub Actions par lot**. Chaque job exécute quelques matchs séquentiellement pour ne pas dépasser la RAM, avec huit jobs ou plus en parallèle selon quotas. Paramètres reproductibles : SHA moteur, SHA patches et decks, position, graine, profils, horloge et logs.

### Statut actuel

- Pilote V1 : patch fonctionnel avec trois propositions de sacrifice sur 16 parties, **0 victoire** ; pas d'amélioration démontrée.
- V2 : patch Java plus large incluant Throne of Geth et Spawning Pit et valorisation des permanents à marqueurs ; compilation et première partie réelle validées.
- L'architecture de lookahead multijoueur décrite ici est un **plan de développement**, pas un moteur prétendument opérationnel.
