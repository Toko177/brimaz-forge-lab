# V42 — Premier contrôleur générique Commander à quatre IA

## But et limites

Remplacer les exceptions Brimaz par une **politique opt-in indépendante des
noms de cartes**, commune aux quatre sièges. Cette version met en place le
contrat logiciel générique, **pas** encore une IA Commander comparable à un
joueur confirmé. Les calculs restent un classement *partiel* d'actions
existantes : aucune simulation de la pile, des mains adverses ou des cartes
piochées, aucun calcul fiable de combos ni réponse adversaire anticipée.

## Interfaces

- `CommanderGenericModelV42.java` : état public immuable, candidats décrits
  par types, taille, valeur de mana et présence d'une vraie capacité de mana
  Forge; aucune liste de cartes, aucun commandant forcé ni bonus Brimaz.
- `CommanderGenericSequencerV42.java` : lit uniquement les permanents
  publics et **notre propre main**, la zone commandant, et les capacités de
  lancement déjà présentes dans la liste proposée par Forge.
- `AiController` : chaque proposition est encore rejetable par
  `canPlayAndPayFor`. Si le modèle hésite, détecte une menace grave,
  ou s'il ne voit pas au moins deux permanents candidats non ciblés,
  **l'IA Forge originale continue**. Les contre-sorts, removals ciblés,
  réponses sur pile, attaques et blocs restent principalement Forge.
- L'ancien pilote Brimaz et les règles V17–V41 sont désactivés par les
  drapeaux contrôlés ; le même JAR patché est commun aux deux bras.

## Exécution

Politique : `v42_commander_general`. Référence :
`v37_stock_control` (Forge avec mêmes correctifs de compatibilité,
**pas** le JAR original byte-identique). Les 7 decks
`forge_decks/*.dck` restent fixés par SHA256.

```sh
python3 scripts/run_paired_four_ai.py \
  --jar /path/to/forge-gui-desktop-2.0.15-jar-with-dependencies.jar \
  --reference-policy v37_stock_control \
  --experiment-policy v42_commander_general \
  --pod both --games-per-rotation 1 --parallel 2 --clock 420 \
  --seed-base 20261129 --out results/v42_generic_pairs
```

Après les parties, analyser le `comparison.json` réellement écrit :

```sh
python3 scripts/audit_v42_generic_commander.py \
  --input results/v42_generic_pairs/<run-id>/comparison.json \
  --output results/v42_generic_pairs/v42_audit.json
```

L'audit vérifie que la référence ne contient **aucune** décision V42,
que les mêmes sièges, patches et decks ont joué les deux bras, et que
plusieurs decks distincts ont réellement été pris en charge. Propositions,
approbations natives, jeux terminés naturellement, et censures sont
distingués. Une approbation n'est pas une résolution.

## Ce que V42 ne sait pas encore faire

1. Classer la valeur réelle des textes Oracle, des triggers, combos,
   tuteurs, sacrifices, stack interactions, taxes et ressources adverses.
2. Rechercher des lignes multi-actions légales en tenant compte des
   adversaires qui réagissent en politique imparfaite information.
3. Apprendre/caler les décisions à partir de séquences humaines évaluées.
4. Offrir un deckbuilding crédible sur *win-rate* avant suffisamment de
   vraies parties contre plusieurs archétypes, forces et rotations.

**Porte de sortie :** la V42 ne peut être considérée meilleure que Forge
qu'après des changements de décisions approuvés, résultats A/B naturels
à graines inédites, plusieurs stratégies adverses, et une analyse
statistique qui ne traite pas un tirage de petite taille comme preuve.
