# Brimaz V4 Bracket 3 — révision **victoire par le board**

**Date : 12 octobre 2026. Statut : candidat 100 cartes, légal à recontrôler en direct, pas une puissance ou un taux de victoire prouvé.**

## Objectif confirmé par le joueur

Gagner **surtout en attaquant avec les Phyrexians et les Incubateurs transformés**,
pas en faisant perdre 30 à 40 PV par une accumulation automatique de
déclenchements de drain. L'axe sacrifice/prolifération subsiste car il
**fait grandir les marqueurs +1/+1** et permet de reconstruire.
Le drain reste une issue secondaire si le plateau est verrouillé.

Cycle tactique recherché :
1. accélérateur puis Brimaz ; lancer des Phyrexians/créatures-artefacts pour incuber ;
2. générer des Incubateurs, les garder comme artefacts non-créatures pendant le développement ;
3. sacrifier si nécessaire un **Phyrexian déjà créature** avant les étapes de fin pour déclencher la prolifération de Brimaz ; choisir les Incubateurs avec leurs marqueurs ;
4. payer {2} pour transformer les Incubateurs pertinents, et pas tous aveuglément ;
5. leur donner **vol**, **+1/+1 tribal**, un pompage global ou double initiative afin de gagner avec de vrais dégâts de combat ;
6. protéger l'armée contre wraths/exils et conserver du mana pour réanimer/rejouer si elle est détruite.

## Cinq corrections de la première ébauche V4

| Retirée de V4 initiale | Remplaçante | Ce que cela change vraiment |
|---|---|---|
| Nadier's Nightblade | **Abzan Falconer** | Le Fauconnier donne le vol aux créatures avec marqueur +1/+1, ce qui inclut les Incubateurs **transformés**. Gagne par blessures de combat plutôt que par jetons quittant le champ. Non phyrexian, donc ne déclenche pas Brimaz au lancement. |
| Marionette Master | **Mirror Entity** | Mirror Entity est **changeling**, donc Phyrexian lorsqu'elle est lancée : déclenche Brimaz. Pour {X}, toutes tes créatures ont la F/E **de base** X/X et gardent leurs marqueurs. Offre un mana sink d'attaque de masse ; attention, X=0 peut tuer nos créatures sans marqueurs. |
| Mirkwood Bats | **Akroma's Will** | Véritable finisher de combat. Si on contrôle **un commandant** au lancement, les deux modes donnent vol, vigilance, double initiative, lien de vie, indestructible et protection contre les couleurs à **nos créatures déjà en jeu**. Ne crée aucune armée à lui seul. |
| Vraan, Executioner Thane | **Norn's Choirmaster** | Phyrexian volant, initiative ; son lancement déclenche Brimaz et il prolifère lorsque le commandant **arrive ou attaque**, renforçant les marqueurs des Incubateurs. Coût {3}{W}{W}, plus haut de courbe ; demande une base blanche disponible. |
| Ichor Wellspring | **Patchwork Banner** | Fixe une couleur de mana et donne +1/+1 aux créatures du type choisi **Phyrexian**, y compris aux Incubateurs transformés, mais pas aux Incubateurs artefacts non-créatures. Perd deux sources de pioche ponctuelle potentielles de Wellspring. |

La **première V4 orientée drain n'était encore qu'une hypothèse** et n'a
jamais démontré un meilleur taux de victoire. La présente révision garde
le même fichier candidat V4 dans la branche expérimentale ; le commit
précédent dans Git permet de retrouver la première proposition.
Aucune modification du témoin V3 ni des sept `.dck` canoniques.

## Comparaison V3 → V4 **actuelle** : 11 échanges

| Retrait par rapport à V3 | Ajout V4 actuelle | Fonction |
|---|---|---|
| Darksteel Splicer | Abzan Falconer | Evasion pour les Incubateurs à marqueurs, contre perte de Golems indestructibles (gros payoff à 7 manas) |
| Chronomancer | Myr Sire | Créature-artefact à deux manas lançable tôt et double corps au sacrifice |
| Phyrexian Delver | Morbid Opportunist | Pioche sur une mort de créature au maximum **une fois par tour** |
| Tortured Existence | Braids, Arisen Nightmare | Valeur de sacrifice/pioche à **notre seule étape de fin** ; abandon du recast depuis le cimetière |
| Inspiring Statuary | Idol of Oblivion | Pioche de jetons contre accélération des non-artefacts |
| Norn's Wellspring | Patchwork Banner | Anthems Phyrexians + mana contre pioche/prolifération |
| Etchings of the Chosen | Rite of Oblivion | Exil de permanent non-terrain avec sacrifice d'artefact/créature ; perte de protection/anthem tribal |
| Vault of the Archangel | War Room | Pioche récurrente terrain contre puissance défensive/combat lifelink-deathtouch |
| Marionette Master | Mirror Entity | Pompage de board + sort Phyrexian contre drain ciblé |
| Mirkwood Bats | Akroma's Will | Finisher/protection de combat contre drain de jetons |
| Vraan, Executioner Thane | Norn's Choirmaster | Vol + prolifération par attaques du commandant contre drain de morts par tour |

## Cartes de soutien délibérément conservées

- **Anointed Procession / Mondrak** : plus d'Incubateurs = plus de créatures transformables. Chaque transformation coûte normalement {2}, donc la quantité seule ne suffit pas à gagner.
- **Grafted Butcher** : bonus aux Phyrexians ; la capacité de récursion est un filet de sécurité.
- **Elesh Norn // The Argent Etchings** : transforme en masse des Incubateurs et favorise l'armée phyrexiane, utile lorsque {2} par jeton deviendrait trop coûteux.
- **Roaming Throne** : double les triggers de type choisi (Phyrexian) pertinents, notamment l'Incubation et la prolifération de Brimaz, mais pas les effets qui ne sont pas déclenchés par un Phyrexian.
- **Vulpine Harvester / Myr Retriever / Lurrus / Phyrexian Reclamation** : permettent de reconstruire et de relancer des permanents, afin de recréer le board.
- **Ashnod's Altar / Phyrexian Altar / Krark-Clan Ironworks / Bartolomé / Ravager / Yawgmoth** : outils de tempo et de conversion des ressources ; sacrifier l'armée entière sans autre raison est désormais un contresens tactique. On privilégie les moteurs de reprise et une mort de Phyrexian par tour utile à Brimaz.
- **Scheming Aspirant, Marionette Apprentice, Elas il-Kor, The Meathook Massacre** : drain/valeur **secondaires** (et Meathook pour un wipe). Ce n'est plus l'axe principal de victoire.

## Règles et points de vigilance

- Un Incubateur non transformé est **artefact non-créature** ; il a des marqueurs +1/+1 mais ne peut ni attaquer ni bénéficier des bonus réservés aux **créatures**. Sa transformation n'est pas une nouvelle arrivée sur le champ et ne déclenche pas les ETB.
- Un Incubateur **transformé** est un **jeton créature-artefact Phyrexian**. Ses marqueurs restent, ce qui rend Abzan Falconer, Patchwork Banner et la prolifération particulièrement cohérents.
- Mirror Entity ne transforme pas les artefacts non-créatures : son activation ne concerne que les créatures que nous contrôlons. La valeur X fixe la force/endurance de base, puis les marqueurs s'ajoutent.
- **Akroma's Will** est un sort non-créature : ne déclenche pas Brimaz. Avec Brimaz sur le plateau lorsqu'on annonce le lancement, les deux modes sont accessibles. La protection contre les couleurs ne bloque pas nécessairement des créatures-artefacts incolores.
- **Norn's Choirmaster** prolifère au déclenchement d'ETB/attaque d'un commandant que nous contrôlons ; les attaques de simples Incubateurs ne suffisent pas.
- La capacité de Brimaz se déclenche au début de chaque étape de fin si un Phyrexian sous notre contrôle **est mort durant ce tour**. Sacrifier le premier Phyrexian seulement à la résolution de Braids **pendant** notre étape de fin arrive trop tard.
- Akroma's Will et les synergies board sont plus sensibles aux wraths et à l'exil : conservation de Clever Concealment, Flare of Fortitude et Restoration Magic, et nécessité d'observer les removals du playgroup.

## À vérifier, avec méthode et sans statistiques inventées

Les decks ont 100 cartes **vérifiées structurellement** contre la V3
et les sept decklists canoniques restent inchangées. La légalité et
l'absence de Game Changers sont testées en direct par Scryfall dans
`.github/workflows/commander-legality.yml`. Un contrôle réussi atteste
de la légalité **au moment de l'exécution**, pas de la qualité stratégique.

`scripts/audit_brimaz_v4.py` fournit des probabilités hypergéométriques
**exactes de voir** une pièce de soutien au combat parmi les cartes
physiquement piochées et de voir une source de drain. Les étiquettes
sont manuelles, les cartes vues peuvent être injouables et rien
ne simule les combats, les décisions des adversaires ou les victoires.

Une vraie démonstration devra comparer V3/V4 en jeu **humain** à quatre,
contre les archétypes et brackets habituels, en notant : nombre
d'Incubateurs créés/transformés, taille des créatures en attaque,
blessures **de combat** infligées vs pertes de vie par drain,
cartes adverses tuées, nombre de wraths, tours de victoire et morts.
Le but est de gagner davantage **par dégâts de combat**, pas seulement
d'avoir un meilleur taux de victoire global.

### Liens

- `decks/Brimaz_V4_B3.txt` (import de deck).
- `deck_candidates/Brimaz_V4_B3.dck` (Forge).
- `docs/BRIMAZ_V4_B3_CARD_BY_CARD.md` (audit des 100 cartes).
- `scripts/audit_brimaz_v4.py` et `tests/test_audit_brimaz_v4.py` (preuve structurelle, non gameplay).

## Validation factuelle de la révision orientée combat

La campagne **[GitHub Actions santé / structure](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38305895661)**
a terminé avec succès sous Python 3.10 et 3.12. Les 100 cartes,
les 11 changements V3→V4 et les sept DCK canoniques non modifiés
sont confirmés par des contrôles reproductibles.
La campagne **[légalité Scryfall live](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38305895743)**
a aussi terminé avec succès : 100 cartes, 94 noms, commandant Brimaz,
identité blanc/noir, **zéro erreur, zéro avertissement et zéro
Game Changer détecté**, avec `--require-no-game-changers`.

L'audit hypergéométrique repose sur des **catégories de cartes
annotées**, ne tient pas compte du mana, de la table ou des adversaires
et ne doit jamais être présenté comme un taux de victoire :

| Mesure structurelle ou cartes vues | V3 | V4 board |
|---|---:|---:|
| Cartes de soutien/finisher de combat identifiées | 3 | 6 |
| ≥1 de ces cartes vues dans les 13 premières cartes | 34,45 % | 57,64 % |
| Principaux moteurs de drain identifiés | 7 | 4 |
| Sources potentielles de pioche répétable identifiées | 5 | 8 |
| ≥1 moteur de pioche vu dans les 10 premières cartes | 41,62 % | 58,34 % |
| Sorts pouvant déclencher Brimaz au lancement | 26 | 25 |
| ≥2 de ces sorts vus parmi les 13 premières cartes | 90,50 % | 89,03 % |
| ≥1 exutoire + ≥1 payoff de sacrifice vus dans 13 cartes | 51,89 % | 37,27 % |
| Cartes jouables comme terrain, dont MDFC | 38 | 38 |

**Trade-off volontaire** : moins d'accès aux moteurs de drain
(et un sort incubant de moins) pour davantage de combat.
La capacité à **transformer suffisamment d'Incubateurs** et à
faire passer les dégâts **reste non mesurée**. Ces chiffres ne
permettent aucune prédiction de winrate humain.

Aucune partie réelle V3/V4 n'a été certifiée dans ce changement :
la réussite du workflow de légalité n'est pas une preuve de supériorité
stratégique.
