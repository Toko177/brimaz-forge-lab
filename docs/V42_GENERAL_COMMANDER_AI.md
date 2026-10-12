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

## Correctif fondé sur les vraies traces — V43 / identité des sièges

La campagne V42 historique
[38175519441](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38175519441)
a fait tourner **16 vrais processus Forge**, 8 paires de parties
(4 artifact + 4 aristocrats). Les deux bras ont fini naturellement
dans **7 paires** (4 artifact + 3 aristocrats). Les deux audits
ont pourtant échoué sur `Unknown V42 seat Ai(4)-EDH Amalia` et
`Ai(4)-EDH Zimone and Dina aristo`. Cette erreur appartient
au *parseur des traces*, pas au moteur de règles. Les résultats ne
démontrent pas une meilleure politique.

La cause est maintenant confirmée : le nom observé est
`Ai(<numéro de siège>)-<Name= du .dck>`, tandis que le banc d'essai
utilise un identifiant de fichier comme `Kaal_22193355`.
`scripts/forge_seat_identity.py` valide strictement les deux
dimensions (siège **et** nom du deck déclaré), en lisant les
métadonnées canoniques originales, y compris les caractères
accentués, sans recherche partielle. Les miroirs utilisent uniquement
leurs six labels exacts, dérivés des clones temporaires.

Le contrôle Java `MultiplayerSacrificeAccessV41.authorized`
reconnaît le vrai préfixe Forge `Ai(1)-` à `Ai(4)-` avant
d'appliquer l'allowlist strictement bornée. Les anciennes campagnes V41
marquant **toutes** les fenêtres `unauthorized_pilot` ne peuvent pas
servir de preuve de la stratégie ; le correctif est vérifié par de
nouveaux tests adversariaux.

Un second défaut de généralisation est corrigé : `Card.getCMC()`
ne représente pas toujours le coût à payer. Le classement ne
rejette plus une action que Forge juge légalement payable sous
prétexte que sa valeur de mana imprimée dépasse une estimation
des sources de mana. La validité réelle reste déterminée par
`sa.canPlay`, `canCastTiming`, `ComputerUtilCost.canPayCost`
et surtout `AiController.canPlayAndPayFor`.

**Protocole de retest à graines inédites** : `20261213` pour
les miroirs V41 et `20261217` pour les paires génériques V42.
Les campagnes précédentes restent conservées et invalides lorsque
l'audit n'a pas pu établir la bonne identité de pilote.
Aucune affirmation de gain de victoire avant de nouveaux résultats
non censurés, comparés sur plusieurs decks, sans contamination.

## V43 — Commander générique : une IA candidate contre trois contrôles

Le premier protocole V42 activait le même pilote sur les quatre sièges.
Il vérifiait l'exécution multi-decks, mais ne mesurait pas la force de
ce pilote *contre* Forge : un gagnant existe dans les deux politiques.

La variante `v43_commander_single_seat` n'active le modèle que pour
le **siège Forge Ai(1)**. Les autres sièges conservent la sélection
originale de Forge sous les mêmes patches de compatibilité. Les
quatre rotations de `batch.py` placent successivement plusieurs decks
différents sur ce siège et évitent de privilégier Brimaz.

L'auditeur V42/V43 vérifie les journaux `Ai(n)-Name=`, l'unique siège
autorisé, les mêmes decks entre les deux bras, les vraies approbations,
les fins naturelles et les victoires du siège expérimental.
Le modèle ne traite pas encore les décisions tactiques et les combos.
Un petit nombre de différences de victoires n'est pas une preuve
de compétence comparable aux joueurs humains.

Commande :

```sh
python3 scripts/run_paired_four_ai.py \
  --jar /path/to/forge-gui-desktop-2.0.15-jar-with-dependencies.jar \
  --reference-policy v37_stock_control \
  --experiment-policy v43_commander_single_seat \
  --pod both --games-per-rotation 1 --parallel 2 \
  --clock 420 --seed-base 20261221 \
  --out results/v43_head_to_head_pairs
```

**Attention :** cette note décrit la nouvelle composition active ;
les mentions d'Amalia plus haut concernent les anciens journaux réels
et restent volontairement conservées comme preuve historique.
