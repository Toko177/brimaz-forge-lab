# Brimaz : recherche complète des cartes Commander légales Orzhov / incolores

**Audit lancé le 12 octobre 2026, sur le catalogue Oracle live Scryfall.**
[Exécution effective sur GitHub](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38311544321),
job `Enumerate the full live Commander-legal Orzhov and colorless Oracle pool` :
**SUCCESS**. L'archive `brimaz-current-full-oracle-pool` contient
`all-eligible-WB-colorless-index.csv` (tous les noms admissibles),
`orzhov-legal-full-pool.json` (rôles + Oracle + candidats) et
`orzhov-legal-shortlist.csv`.

## Taille et limites de l'inventaire

| Étape | Nombre |
|---|---:|
| Enregistrements Oracle disponibles examinés | **38 751** |
| Cartes Commander légales, identité incluse dans W/B/incolore, sans `game_changer:true` | **12 763** |
| Cartes classées pertinentes par mots-clefs/typologie, après filtres | **7 216** |

Parmi les 12 763 cartes admissibles, le moteur repère :
22 références contenant l'Incubation, 31 la prolifération,
934 des profils possibles d'interaction ciblée, 250 des profils
de gestion de masse, 396 des profils de défense, et 1 188 des
expressions potentielles d'avantage de cartes. **Ce sont des
étiquettes lexicales** : elles sont approximatives et parfois
redondantes ; 934 ne signifie **pas** 934 bons removals.
Les cartes hors de ces catégories restent indexées, non exclues
silencieusement. Les cartes infect/toxic/poison reçoivent une
pénalité de recommandation : elles ne sont pas présentées comme
illégales. Les Game Changers déclarés sont exclus de l'index
principal **pour respecter la préférence utilisateur**, pas
parce que Bracket 3 les interdirait tous.

Le scan utilise `scripts/scan_commander_oracle_pool.py`, une
classification de candidats qui n'analyse **pas** les combinaisons
de deux cartes, le déroulement des coûts, les réponses adverses,
les dégâts réels ni les prix de toutes les éditions européennes.
**12 763 cartes considérées pour la découverte n'est PAS la
preuve mathématique d'une liste optimale.**

## Diagnostic de la V4 existante

Objectif utilisateur : **gagner d'abord au combat** avec des
Incubateurs transformés et des Phyrexians, sans staples
universels hors de prix et sans poison.

Les moteurs principaux sont déjà nombreux :
**Brimaz, Norn's Inquisitor, Progenitor Exarch,
Elesh Norn // The Argent Etchings, Mondrak, Roaming Throne,
Abzan Falconer, Mirror Entity, Norn's Choirmaster,
Grafted Butcher, Patchwork Banner, Banner of Kinship, Aron**.
C'est le noyau à préserver.

Le point insuffisamment traité était la **gestion et la survie
du board** : peu de réponses universelles à une menace et
quelques cartes de sacrifice redondantes malgré le plan combat.
Il fallait améliorer **les slots déjà disponibles** sans
diminuer gratuitement les casts Phyrexians ou le mana coloré.

## 3 changements supplémentaires, issus de la recherche élargie

| Sortie V4 antérieure | Entrée V4 actuelle | Gain stratégique et vrai coût |
|---|---|---|
| **Krark-Clan Ironworks** | **Sunder the Gateway** | À {1}{W}, rituel retirant un **artefact non-jeton/enchantement adverse** et incubant 2 ; mode alternatif : incube 2 puis transforme un jeton gratuitement. Deux fonctions cohérentes, plutôt qu'une énième machine à sacrifier tous les artefacts. Coût : perte d'une source de mana incolore obtenue en sacrifiant les Incubateurs non transformés. |
| **Spawning Pit** | **Stroke of Midnight** | Un éphémère {2}{W} répond à **tout permanent non-terrain** destructible, même un enchantement, planeswalker ou artefact. Contrepartie 1/1 Humain à son contrôleur, peu problématique si notre armée vole. Coût : perte d'un exutoire de sacrifice libre et stock de marqueurs charge proliférables. |
| **Living Death** | **Phyrexian Scriptures** | La Saga {2}{B}{B} offre une destruction des **créatures non-artefacts** (chapitre II) et exil de tous les cimetières adverses (chapitre III). Chapitre I peut donner à Brimaz le type artefact pour lui éviter ce nettoyage. Les Incubateurs transformés sont des créatures-artefacts donc survivent. Coût : **nettoyage retardé et annoncé** ; inefficace contre une armée adverse d'artefacts ; perte de la capacité de réanimation massive de Living Death. **Sunfall** reste un exil de masse rapide contre les decks artefacts. |

Prix tendance indicatifs Cardmarket le 12/10/2026 :
[Sunder the Gateway ≈ 0,11 €](https://www.cardmarket.com/en/Magic/Cards/Sunder-the-Gateway),
[Stroke of Midnight ≈ 0,32 €](https://www.cardmarket.com/en/Magic/Cards/Stroke-of-Midnight),
[Phyrexian Scriptures ≈ 0,71 €](https://www.cardmarket.com/en/Magic/Cards/Phyrexian-Scriptures).
Ce sont des prix ponctuels selon édition, **pas des achats exécutés**.

**Différence nette V3→V4 : 19 sorties et 19 entrées**.
Les 100 cartes V4 sont toujours strictement validées ; les
sept originaux restent inchangés.

## Autres cartes examinées dans l'ensemble du pool, non sélectionnées

- **Sculpted Perfection** : enchantement {2}{W}{B}, Incubation 2
  et +1/+1 aux Phyrexians ; excellente synergie directe, mais
  concurrence plusieurs anthems déjà en V4. Challenger naturel
  si `Banner of Kinship` arrive trop tard ou si la table
  retire les artefacts.
- **Unbreakable Formation** : {2}{W}, instant indestructible ;
  en phase principale, marqueur +1/+1 sur chaque créature et
  vigilance. Excellent hybride attaque/défense, mais la V4
  possède déjà Clever Concealment, Flare of Fortitude,
  Restoration Magic et Akroma's Will. **Ne protège pas les
  Incubateurs non transformés**, qui ne sont pas des créatures,
  et son indestructible ne protège pas de l'exil.
- **Fracture** : {W}{B}, instant détruisant artefact,
  enchantement ou planeswalker ; flexible et bon marché,
  mais ne retire pas une créature problématique.
- **Excise the Imperfect** : {1}{W}{W}, instant exilant un
  permanent non-terrain mais **son contrôleur incube selon
  sa valeur de mana**, donc l'adversaire reçoit un Incubateur
  potentiellement gros ; prix politique et de board non nul.
- **Merciless Repurposing** : exile une créature et incube 3
  à **six manas**, trop lent comme interaction tactique.
  Un score lexical élevé ne suffit pas à justifier l'inclusion.
- **Unbounded Potential** : instant {1}{W}, proliférer
  ou poser des marqueurs sur deux créatures ; synergie bonne,
  mais une protection/gestion supplémentaire vaut souvent
  davantage dans une partie à quatre.
- **Phyrexian Rager** : caste Phyrexian à 3 manas qui
  pioche à l'entrée et fait perdre 1 PV ; pertinent pour
  améliorer la densité de casts et la pioche sans staple,
  mais peut remplacer une pièce de late game seulement
  après analyse de la courbe.
- **Bone Shredder** : Phyrexian à 3 manas avec ETB anti-créature,
  mais cible **non-artefact non-noire** et coûte l'écho :
  mauvais contre plusieurs menaces Orzhov/artefacts.
- **Surge of Salvation** : protection {W} de nous et nos
  permanents par hexproof ; très rentable contre ciblages,
  mais ne donne pas indestructible et ne répond pas à une
  wrath d'exil non ciblée.

## Critères d'équilibre à mesurer en vraies parties à quatre

| Fonction | Ordre de grandeur initial, pas une règle légale |
|---|---|
| Sources de terrain (35 cartes frontales + 3 MDFC chez nous) | **36–39** sources possibles |
| Accélérateurs réels et réduction de coûts | **8–11** |
| Sources de pioche, dont certaines répétables | **8–11** |
| Réponses ciblées aux menaces, à différentes vitesses | **5–8** |
| Contrôles de table (y compris asymétriques) | **2–3** |
| Protections/évasions contre les removals et wipes | **3–5** |
| Sorts compatibles avec l'Incubation de Brimaz | garder une densité élevée, autour de **25–30** |
| Finisseurs d'armée et évasion | **4–7**, dont les capacités complémentaires |

Les catégories **se chevauchent** (ex. `Witch Enchanter` =
MDFC terrain/removal, `Sunder the Gateway` =
Incubation/removal, `Akroma's Will` = protection/finisher).
Ne pas additionner les lignes comme si elles occupaient des slots
indépendants.

### Attention à la précision des tests

L'audit hypergéométrique de `scripts/audit_brimaz_v4.py`
mesure uniquement les chances de **voir** certaines catégories
de cartes, sans pouvoir de mana, cast, défense adverses,
règles moteur ou combat. Même un winrate Forge élevé
resterait à confronter à de vraies parties humaines.

La sélection 19 swaps est une **proposition stratégique
cohérente et légalement vérifiable**, pas « la meilleure
mathématiquement prouvée parmi les 12 763 cartes ».

## Dernières vérifications réalisées pour cette V4 (19 échanges)

- [CI structure et tests Python 3.10/3.12](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38312050886) : **SUCCESS**, 100 cartes, 19 changements nets, contrôle des sept decks canoniques, et test offline de l'énumération Oracle.
- [CI Scryfall live, légalité et catalogue complet](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38312050893) : **SUCCESS** pour les deux jobs. La V4 compte 100 cartes physiques, 94 noms différents, identité W/B, **0 erreur, 0 avertissement et aucun Game Changer détecté**.
- Selon les étiquettes manuelles et les tirages aveugles du script d'audit, la V3 avait **3 réponses ciblées** et la V4 **6** ; chacune contient trois cartes/suites capables de faire office de nettoyages selon le contexte, et la V4 possède cinq cartes de protection identifiées. Ces comptages ne mesurent pas les capacités de résolution ou l'efficacité tactique.
- Les 19 modifications et les trois cartes de gestion sont documentées carte par carte. **Aucune simulation de victoire V3 contre V4 ni partie humaine n'a été exécutée dans ce changement**.


## Mise à jour ciblée depuis l'inventaire global

La V4 actuelle a **21 changements nets** relativement à la V3 figée, après ajustement au niveau de jeu décrit pour KaalDeagle : Anointed Procession → Everflowing Chalice, Aron → Steel Overseer, Activated Sleeper → Scrap Trawler. **La validation globale de 38 751 cartes et 12 763 admissibles demeure valable comme inventaire de découverte**, mais les statistiques de la V4 actuelle et ses tests sont dans `docs/BRIMAZ_V4_B3_DECISIONS.md` ; la CI du run 38312050886 citée plus haut concerne la **version antérieure à 19 changements** et demeure volontairement historisée.
