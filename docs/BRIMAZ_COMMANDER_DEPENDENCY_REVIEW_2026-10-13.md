# Brimaz V4 : traiter la dépendance au commandant sans changer la win condition

**13 octobre 2026 — audit stratégique et révision appliquée.**
La V4 reste une liste Commander **100 cartes**, Bracket 3, **sans Game Changer**,
qui veut **gagner par le board et les blessures de combat** avec Incubateurs
transformés et Phyrexians. Pas de poison/infect comme win condition,
pas de drain comme plan principal et pas d'auto-includes génériques chers
ajoutés simplement pour leur puissance.

## Diagnostic des parties vécues

**Brimaz, Blight of Oreskos coûte {2}{W}{B}, MV4, et n'a aucune capacité
d'arrivée sur le champ de bataille.** Le premier déclenchement ne se produit
que lorsqu'on lance un **autre** sort de créature Phyrexian ou
d'artefact-créature **alors que Brimaz est déjà sur le champ**.
Il ne déclenche pas sa propre capacité lorsqu'on le lance, et son
arrivée ne fait pas incuber. Lorsqu'il meurt avant le tour suivant,
payer **6** puis **8** manas de zone de commandement expose le
deck au problème « dépenser un tour entier sans gain de board ».

Par conséquence, il ne faut pas essayer de toujours forcer
Brimaz T4. La bonne configuration doit :
1. exécuter un début de partie utile T1–T3 avec ramp, pioche,
   première incubation et protection ;
2. avoir plusieurs cartes créant/grossissant le board
   **indépendamment** du commandant ;
3. mettre la protection en place AVANT de le lancer, ou garder une
   réponse instantanée pour prévenir sa première mort ;
4. pouvoir finir avec l'armée, même si le chat retourne plusieurs
   fois en zone de commandement ;
5. utiliser une solution occasionnelle de récupération du commandant
   contre la taxe si celui-ci est trop ciblé, sans surestimer cette
   solution (commander tax ≠ seul problème).

## Cinq échanges de la V4 en réponse directe

| Sortie V4 précédente | Entrée V4 actuelle | Problème corrigé et véritable compromis |
|---|---|---|
| **Norn's Choirmaster** ({3}{W}{W}) | **Sculpted Perfection** ({2}{W}{B}) | L'enchantement **incube 2 à l'arrivée** et donne **+1/+1 à tous nos Phyrexians** même sans Brimaz : une créature et un buff de board qui persistent si le commandant meurt. Coût : perte d'un Phyrexian volant/initiative et de ses proliférations quand notre commandant **arrive ou attaque**. |
| **Gixian Infiltrator** ({1}{B}) | **Phyrexian Rager** ({2}{B}) | Créature Phyrexian 2/2 ; **pioche une carte et perd 1 PV à son entrée**. Fonctionne seule au T3, et au T5, si Brimaz est présent, le sort déclenche **Incubation 3** avant son ETB. Coût : un mana de plus et perte d'un payoff de sacrifice à marqueurs. |
| **Elas il-Kor, Sadistic Pilgrim** ({W}{B}) | **Selfless Spirit** ({1}{W}) | La 2/1 volante peut arriver avant Brimaz. En la sacrifiant à vitesse d'éphémère, **toutes nos créatures gagnent indestructible jusqu'à la fin du tour** : protection contre destroy et blessures, même si Brimaz arrive plus tard. Coût : ne protège pas contre l'exil, bounce ou réduction de l'endurance à zéro ; la créature est non Phyrexian/non artefact et ne déclenche pas Brimaz au lancement. Aucun poison. |
| **Resourceful Defense** ({2}{W}) | **Lightning Greaves** ({2}, équipement {0}) | Posées T2, les bottes permettent de donner **shroud** à Brimaz dès son arrivée sans mana supplémentaire, ainsi qu'à une menace clé. Coût : suppression de la conservation/transmission des marqueurs ; **shroud empêche aussi nos propres sorts ciblés, comme Malakir Rebirth, de cibler Brimaz équipé ; Selfless Spirit ne cible PAS et peut le protéger même sous les bottes**. Il faut déplacer les bottes sur une autre créature lors d'une phase principale pour pouvoir ensuite le cibler. L'équipement utilise la pile : un adversaire peut répondre avant qu'il ne s'attache. |
| **Vault of the Archangel** (terrain donnant {C}) | **Command Beacon** (terrain donnant {C}) | Sacrifier ce terrain met Brimaz depuis la **zone de commandement vers notre main**, ce qui permet de le relancer pour **{2}{W}{B}** sans taxe de zone de commandement. La valeur est surtout en cas de **deuxième/troisième relance**, pas lors du premier lancement. Coût : dépense d'un terrain (perte de mana permanent), maintien d'une source incolore, perte du contact mortel/lien de vie défensif de Vault, pas une solution à une destruction immédiate au T4. |

**Détail important :** **Selfless Spirit n'a ni toxic, ni infect et ne cible aucune créature**. Sa capacité protège donc aussi Brimaz équipé de Lightning Greaves, puisque *shroud* n'empêche que le ciblage. Elle n'empêche pas les wipes d'exil comme Sunfall. Loran's Escape est une alternative ciblée à un mana pour un autre type de protection.

**Bilan net V3→V4 : 23 sorties et 23 entrées**, puisque
**Norn's Choirmaster, Gixian Infiltrator et Resourceful Defense**
n'étaient que des ajouts des révisions V4 précédentes.
**Vault of the Archangel et Elas il-Kor étaient en V3**, d'où
deux nouvelles différences effectives. La V3 et les sept fichiers
de decks adverses canoniques restent totalement inchangés.

## Comment piloter sans se faire punir par la taxe

### Séquence A : Brimaz protégé

- **T1 :** développer le mana ou garder une main avec une action utile au T2.
- **T2 :** Norn's Inquisitor, qui **incube 2 sans Brimaz** ; OU
  Lightning Greaves ; OU **Selfless Spirit** pour une protection préposée.
- **T3 :** Phyrexian Awakening, qui **incube 4 sans Brimaz** ;
  OU Phyrexian Rager qui pioche immédiatement ; OU un rock suivi
  d'un autre effet.
- **T4 :** Brimaz seulement si l'on peut effectivement l'exploiter
  ensuite et/ou s'il est couvert par Selfless Spirit ou Greaves. Sinon,
  préparer les créatures/ressources sans lui.
- **T5 :** sort de Phyrexian/artefact-créature
  pour incuber selon sa MV, puis ne transformer que les Incubateurs
  utiles pour attaquer avec évasion/bonus.

### Séquence B : le chat se fait tuer avant sa première valeur

- **Pas de rage-recast à six manas par défaut.** Jouer les
  producteurs autonomes : Sculpted Perfection, Norn's Inquisitor,
  Phyrexian Awakening, Essence of Orthodoxy et Progenitor Exarch
  (si X>=1), ou un mode d'Incubation de Sunder the Gateway ;
  Sunfall lorsqu'un reset est utile.
- Maintenir le développement du mana, de la pioche et des marqueurs
  (Steel Overseer, Gix, Idol of Oblivion, Caretaker's Talent, War
  Room). Transformer les Incubateurs qui peuvent **déjà** faire
  des dégâts au combat.
- Brimaz revient **après** stabilisation/protection,
  idéalement via Command Beacon pour esquiver la taxe lors d'une
  nouvelle relance depuis la main ; ou quand nous avons le mana
  de le lancer et un autre sort compatible en même temps.
- La carte en main via Command Beacon **n'est plus lancée de la zone
  de commandement** : elle ne subit donc pas la taxe et ne
  l'augmente pas, mais Beacon a dû être sacrifié.

## Mesures de deck à vérifier (ne pas confondre avec des parties réelles)

Le script `scripts/audit_brimaz_v4.py` mesure :
- 100 cartes physiques / 94 noms ;
- **23 échanges nets** V3 → V4 ;
- densité des sorts déclenchant Brimaz au lancement ;
- sources de mana et interactions/protections ;
- nombre de cartes pouvant incuber **sans commandant** avec
  réserve sur les conditions de lancement et d'effet ;
- outils pouvant être posés **avant Brimaz** pour le couvrir ;
- terrain permettant d'éviter ponctuellement la taxe ;
- probabilités exactes hypergéométriques **de voir** ces cartes,
  pas des probabilités de les lancer ni des winrates.

Ce rapport ne mesure toujours pas les mulligans, les couleurs
de mana, la cible des removals, le timing de l'adversaire,
la véritable survivabilité de Brimaz, ni une série de
parties quatre joueurs. Pour valider cette passe,
journaliser la **première destruction** de Brimaz,
**combien de tours sans lui**, le nombre de permanents
productifs sans lui, la **pioche produite**, et le **tour
où l'armée menace une attaque gagnante**.

## Oracle / références de règles

- [Brimaz](https://mtg.wtf/card/moc/2/Brimaz-Blight-of-Oreskos)
- [Sculpted Perfection](https://mtg.wtf/card/mom/253/Sculpted-Perfection)
- [Selfless Spirit](https://mtg.wtf/card/emn/40/Selfless-Spirit)
- [Lightning Greaves](https://mtg.wtf/card/afc/331/Lightning-Greaves)
- [Command Beacon](https://mtg.wtf/card/tdc/352/Command-Beacon)
- [Loran's Escape, alternative](https://mtg.wtf/card/bro/14/Lorans-Escape)
- [Norn's Inquisitor, capacités de transformation et incubation](https://magic.wizards.com/en/news/feature/march-of-the-machine-release-notes)

**La priorité n'est pas d'atteindre Brimaz au tour 3 à n'importe
quel prix, mais de ne pas perdre la partie si Brimaz n'est
jamais résolu ou meurt deux fois.**
