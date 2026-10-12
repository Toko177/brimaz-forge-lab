# Benchmark de construction EDH : KaalDeagle vs Brimaz V4

**Consultation publique : 12 octobre 2026.** L'utilisateur décrit KaalDeagle comme le meilleur joueur de son groupe et souligne la qualité de ses decks **budget**. C'est une référence sociale et stratégique du playgroup, pas un score Elo ni une preuve que ces decks gagnent statistiquement plus.

**Attention :** les prix sont les estimations affichées par Archidekt au moment de la consultation, pas une estimation Cardmarket exacte des versions physiques achetées. Les catégories sont **déclarées manuellement par le constructeur** et peuvent se chevaucher ; elles ne sont donc **pas directement comparables** aux rôles de `scripts/audit_brimaz_v4.py`.

## Six listes publiques, lecture actuelle

| Deck public | Coût Archidekt | Bracket UI | Catégories saillantes | Usage comme référence |
|---|---:|---|---|---|
| [Quintorius](https://archidekt.com/decks/22106142/edh_quintorius) | **115,90 €** | Core (2), estimé | Land 37 ; Ramp 14 ; Draw 8 ; Interaction 9 ; Mass disruption 3 ; Protection 5 ; Finisher 5 ; « Out Yard » 26 ; payoff sortie cimetière 8 | Une boucle cohérente : cartes quittent le cimetière -> création d'Esprits -> pioche et payoff -> finisher |
| [Zimone and Dina aristo](https://archidekt.com/decks/21930525/edh_zimone_and_dina_aristo) | **139,41 €** | Core (2), estimé | Land 45 ; Ramp 15 ; Draw 8 ; Interaction 6 ; Protection 3 ; Wrath 1 ; Tokens 17 ; Sac Outlet 4 ; Drain 7 | Terrain/pioche/sacrifice intégrés au commandant ; 45 terrains s'expliquent par landfall et ramp, à ne pas copier vers Brimaz |
| [Dungeon Party Time](https://archidekt.com/decks/10347090/edh_dungeon_party_time) | **77,48 €** | **Upgraded (3)**, explicite | Land 35 ; Ramp 20 ; Draw 7 ; Protection 7 ; Spot Removal 6 ; Wrath 3 ; Initiative 17 ; Dungeon 12 | 5 couleurs mais énorme investissement dans l'accès au mana et la résilience ; trois chemins de victoire via dungeons/initiative/party |
| [Abzan Armor Felothar](https://archidekt.com/decks/12576636/edh_abzan_armor_felothar) | **148,60 €** | Core (2), estimé | Land 38 ; Ramp 20 ; Draw 4 ; Removal 7 ; Protection 7 ; Wrath 4 ; Recursion 5 ; Defender 22 ; Evasion 4 ; Finishers 6 | Plan toughness/defender + accélération + interaction ; certaines pièces « low power » seules sont fortes en synergie |
| [Queen Marchesa](https://archidekt.com/decks/9667830/edh_queen_marchesa) | **144,46 €** | Core (2), estimé | Land 35 ; Ramp 12 ; Draw 8 ; Removal 10 ; Wrath 7 ; Anti-wrath 6 ; Protection/Monarchy 14 ; Goad 7 | Deck politique/contrôle : tempo, menace de réponse, monarchie et goad comme ressources, pas combo cher |
| [Xyris buuuuuffs](https://archidekt.com/decks/9214476/edh_xyris_buuuuuffs) | **35,39 €** | Core (2), estimé | Land 36 ; Ramp 12 ; Buff 22 ; Engine 16 ; Removal 12 | Exemple le plus probant pour « budget synergique agressif » : 22 buffs de board, 16 moteurs, 12 cartes de retrait déclarées |

**Avertissement :** Felothar affiche **101 cartes** sur la page publique lors de la consultation, probablement une liste en évolution : ne pas présumer que l'état affiché est directement exportable comme deck Commander légal à 100 cartes. Les brackets **estimés par Archidekt** ne préjugent pas de la perception du groupe ni du winrate réel.

## Leçons de deckbuilding, uniquement là où elles sont transférables

### 1. Préférer la fiabilité d'une séquence à la valeur solitaire d'une carte

Quintorius possède **26** cartes de son sous-système « sorties de cimetière » et **8** payoffs dédiés. Xyris sépare explicitement **22 buffs** et **16 moteurs** : un moteur seul sans payoff, ou un payoff sans matière à multiplier, n'est pas suffisant. Brimaz doit maximiser la séquence :
`sort Phyrexian/artefact au lancement → incubation → mana/temps de transformation → prolifération → évasion/anthem → attaque`.
Évaluer **combien de slots réellement actifs à chaque phase**, et pas seulement la somme des « cartes synergétiques ».

### 2. Plus de mana que de simples cailloux, car transformer coûte {2} par Incubateur

Dungeon Party Time et Felothar indiquent chacun **20** sources annotées Ramp. Brimaz est Orzhov et a une exigence moins forte en couleurs, mais **incuber n'est pas transformer** : il faut payer {2} *en plus* des manas servant à lancer les créatures. Certains boosts tribaux demandent encore 3 à 5 manas.
**Hypothèse à tester** : notre V4 a peut-être un goulot de mana de transformation et de recast. Distinguer :
- vraie accélération T1-T3 (Sol Ring, Arcane Signet, Talisman, Signet, Gold Myr, Ornithopter) ;
- accélération plus tardive/conditionnelle (Patchwork Banner, Solemn Simulacrum, Phyrexian Tower, Ashnod's Altar), sans les traiter comme équivalentes ;
- réduction de coûts (Urza's Incubator), qui ne paie **pas** l'activation de transformation des Incubateurs.
Avant tout remplacement, calculer les sorties colorées et suivre la capacité réelle à transformer en partie.

### 3. Gestion et protection ne sont pas des « slots perdus »

Même Xyris à **35,39 €** porte **12** cartes catégorisées Removal ; Queen Marchesa en affiche **10** et **7 wraths**, tandis que Felothar en affiche **7 removals, 7 protections, 4 wraths**. Il n'y a aucun dogme sur les chiffres exacts, mais la présence de suffisamment de réponses est manifestement voulue dans ces constructions.
Brimaz V4 (comptage manuel distinct) : **6 interactions ciblées, 3 sweeps, 5 protections**. Ne pas rogner sur ces slots uniquement pour insérer davantage de créatures qui incubent ; le gain en menaces n'aide pas contre un combo, un enchantement bloquant ou une wrath létale.

### 4. Reprise après sweeper : le point à surveiller

Le remplacement de **Living Death** par **Phyrexian Scriptures** donne un effet asymétrique cohérent avec des créatures-artefacts, mais supprime une reconstruction massive de board. La V4 garde Lurrus, Phyrexian Reclamation, Agadeem's Awakening, Athreos, Myr Retriever et Vulpine Harvester, mais plusieurs sont lents ou conditionnels.
**Critère test humain** : nombre de tours nécessaires à revenir à trois créatures pertinentes après une wrath adversaire, avec et sans Brimaz sur le champ.

### 5. Budget social : les synergies contextuelles ont souvent plus de valeur

Le Xyris à ~35 € fournit un exemple remarquable de construction bon marché orientée vers le commandant. Cette observation ne démontre pas sa compétitivité à elle seule ; l'utilisateur précise néanmoins que son propriétaire est le joueur le plus fort du groupe. L'évaluation de Brimaz doit donc respecter le même contrat social :
- Eviter les cartes autonomes dominantes ou génériques à ~20–40 € juste pour gagner des points de pourcentage hypothétiques ;
- accepter des exceptions *vraiment reliées au moteur* comme Mondrak et Yawgmoth (que le groupe peut toujours contester) ;
- préférer une carte moins spectaculaire qui active Brimaz et résout un problème du matchup.

## Ce qu'il ne faut PAS importer mécaniquement

- **45 terrains** de Zimone/Dina ne sont pas une nouvelle cible pour Brimaz : son commandant récompense explicitement les terrains supplémentaires.
- **7 wraths** de Queen Marchesa correspondent à une philosophie goad/monarch/contrôle, pas à une stratégie d'armée à protéger.
- **20 ramp** de Dungeon/Felothar reflètent leurs besoins 5/3 couleurs et sous-moteurs ; Brimaz doit mesurer sa propre dépense en mana sur les transformations.
- **Nombre de cartes d'une catégorie** n'est pas le taux de victoire et ne doit pas être automatiquement traduit en 1:1 en raison du chevauchement des tags.
- **Core (2) estimé** est affiché sur plusieurs listes du joueur, même si elles peuvent très bien performer localement ; ne pas prétendre qu'elles sont toutes officiellement Bracket 3.
- La liste Felothar publique affichait **101** cartes, donc il faut vérifier l'export avant de l'utiliser comme témoin technique.

## Hypothèses de tests V4 prioritaires

1. **Séquences réelles** : Brimaz lancé avant T5 ; au moins 2 Incubateurs créés en T5–T7 ; mana encore disponible pour transformation ; Premier gros coup de combat.
2. **Consistance mana/colours** : mains à 2/3/4 lands avec rocks, sorties Aron à {W}{W}{B} ou Norn's Choirmaster à {3}{W}{W}. Mesurer les manas non utilisés vs manque de {2} pour transform.
3. **Capacité à jouer autour d'une interaction** : réponses ciblées Sunder the Gateway, Stroke of Midnight, Swords to Plowshares, Anguished Unmaking, Rite of Oblivion, Witch Enchanter ; timing rituel / instant.
4. **Wipes et protection** : adaptation à une menace de boardwipe, avec Flare of Fortitude, Clever Concealment, Restoration Magic, Phyrexian Scriptures ; après un wipe d'exil, temps de redéploiement.
5. **Matchups du vrai pod** : Kaal Zimone/Dina et Dungeon Party Time sont déjà protégés SHA256 dans `forge_decks/`. Comparer éventuellement contre ces snapshots en Forge, mais **les décisions des IA ne reproduisent pas le joueur humain**.
6. **Budget réel** : mesurer le prix de la V4 **dans une même source et avec mêmes hypothèses** que les decks du groupe, pas additionner des prix de listes Cardmarket/Archidekt mixtes.

## Références

- [KaalDeagle : profil, 106 listes au jour de consultation](https://archidekt.com/u/KaalDeagle)
- [Quintorius](https://archidekt.com/decks/22106142/edh_quintorius)
- [Zimone and Dina](https://archidekt.com/decks/21930525/edh_zimone_and_dina_aristo)
- [Dungeon Party Time](https://archidekt.com/decks/10347090/edh_dungeon_party_time)
- [Felothar](https://archidekt.com/decks/12576636/edh_abzan_armor_felothar)
- [Queen Marchesa](https://archidekt.com/decks/9667830/edh_queen_marchesa)
- [Xyris](https://archidekt.com/decks/9214476/edh_xyris_buuuuuffs)

**Statut** : comparaison de conception à partir des pages Archidekt publiques + V4 et snapshots GitHub. Aucun taux de victoire, aucune preuve que Kaal n'a pas modifié ses listes après consultation. **La V4 n'est pas modifiée dans cette étude** ; la priorité est de tester le manque éventuel de mana et la reconstruction après wrath avant de faire des échanges arbitraires.
