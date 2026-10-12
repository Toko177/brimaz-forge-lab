# Brimaz V4 Bracket 3 — board et attaques, audit des 78 cartes « considering »

**Date : 12 octobre 2026. Statut : candidat de deckbuilding, non prouvé meilleur que V3 par des parties.** 100 cartes, WB, pas de plan poison, zéro Game Changer souhaité. Le projet vise avant tout une liste compétitive et synergique contre un playgroup Bracket 3, et non une nouvelle IA V44.

## Plan de victoire

1. Jouer Brimaz dès que le mana et la situation le permettent ; lancer des créatures **Phyrexian** ou **artefact** pour incub(er) selon leur valeur de mana.
2. Conserver des Incubateurs sous forme **d'artefacts non-créatures** pendant le développement et les renforcer par prolifération ; ne pas payer {2} pour tous sans raison.
3. Sacrifier, au bon moment, une **créature Phyrexian** si nécessaire AVANT le début d'une étape de fin pour déclencher Brimaz ; ne pas confondre mort d'un jeton incubateur non transformé et mort d'un Phyrexian.
4. Transformer les bons Incubateurs en créatures, leur donner le vol (Abzan Falconer), les renforcer (Patchwork Banner, **Banner of Kinship**, Grafted Butcher), accroître leur force (Mirror Entity) et achever la table au combat (Akroma's Will).
5. Préserver le board et le commandant via Restoration Magic, Flare of Fortitude, Clever Concealment ; garder des moyens de récursion quand les wraths passent. Les pertes de vie accessoires d'Elas il-Kor/Meathook ne sont pas le plan A.

**Attention à Banner of Kinship** : elle compte uniquement les créatures de type choisi présentes lorsqu'elle entre, donc pas les artefacts Incubateur non transformés. Les marqueurs fellowship déjà placés sont proliférables, et les Phyrexians transformés ultérieurement bénéficient du bonus tribal existant.

## 13 différences entre la V3 figée et la V4 actuelle

| Retrait V3 | Ajout V4 | Gain visé / risque |
|---|---|---|
| Darksteel Splicer | Abzan Falconer | Vol pour toute créature à marqueurs ; perte de 3 Golems indestructibles à 7 mana |
| Chronomancer | Myr Sire | Petit artefact incubeur au tour 2 et second corps à la mort ; perte de récursion haute courbe |
| Phyrexian Delver | **Gix, Yawgmoth Praetor** | Phyrexian incubeur + pioche sur blessures de combat ; peut donner des cartes aux autres joueurs |
| Tortured Existence | **Solemn Simulacrum** | Incubation 4 + terrain + pioche à la mort ; recul de la récursion en main |
| Inspiring Statuary | Idol of Oblivion | Pioche avec création de jetons ; mana virtuel perdu |
| Norn's Wellspring | Patchwork Banner | Mana coloré + +1/+1 aux Phyrexians ; perte de pioche via prolifération |
| Etchings of the Chosen | Rite of Oblivion | Exil de permanent non-terrain réutilisable via flashback ; perte de protection tribale |
| Vault of the Archangel | War Room | Source de pioche terrain ; perte de lifelink/deathtouch global activable |
| Marionette Master | Mirror Entity | Changeling : incube au lancement et boost de l'armée pour X |
| Mirkwood Bats | Akroma's Will | Protection/vol/double initiative pour attaque décisive ; moins de dégâts indirects |
| Vraan, Executioner Thane | Norn's Choirmaster | Prolifération lors d'ETB/attaque du commandant et créature volante |
| Marionette Apprentice | **Esper Sentinel** | Incubeur à {W} + draw/taxe multijoueur ; baisse du drain sur artefacts morts |
| Scheming Aspirant | **Banner of Kinship** | Prolifération devenue buff tribal de masse au lieu de perte de vie |

**Les quatre décisions de cette dernière passe** sont marquées en gras (Gix, Simulacrum, Esper Sentinel et Banner). Les arbitrages individuels sur **les 78 cartes soumises** figurent dans [BRIMAZ_CONSIDERING_AUDIT_2026-10-12.md](BRIMAZ_CONSIDERING_AUDIT_2026-10-12.md).

## Autres cartes à réexaminer selon les parties réelles

- **Resourceful Defense** : les permanents qui quittent le champ transmettent leurs marqueurs, même un Incubateur non transformé.
- **The Ozolith** : transmet les marqueurs des **créatures** qui quittent le champ, pas des Incubateurs non transformés ; bonne synergie avec Ravager et les créatures transformées.
- **Weatherlight Compleated** : devient 5/5 vol après quatre marqueurs phyresis ; le moteur de sacrifice et la prolifération aident à atteindre le seuil de pioche.
- **Swiftfoot Boots** : si Brimaz meurt beaucoup, trois manas entre équipement et pose peuvent éviter de payer à répétition la taxe de commandant.
- **Phyrexian Awakening** : incube 4 et donne la vigilance à nos Phyrexians ; outil de combat défensif fiable, mais ne remplace pas un véritable finisher.
- **Darksteel Splicer / Elesh Norn, Grand Cenobite** : gros payoffs de board à 7 manas ; à privilégier si les parties du playgroup sont assez longues.
- **Metallic Mimic** : déclenche Brimaz au lancement car artefact-créature, mais un Incubateur ne gagne pas de marqueur Mimic en se transformant.
- **Skrelv, Defector Mite / Gixian Infiltrator / Aron, Benalia's Ruin** : candidats à bas coût plus axés protection/combat/marqueurs, sous réserve de ne pas faire du poison l'objectif.

## Tests : n'affirmer que ce qu'ils prouvent

- L'algorithme [audit_brimaz_v4.py](../scripts/audit_brimaz_v4.py) **vérifie les 100 cartes et les 13 échanges** et calcule des probabilités hypergéométriques **de voir** des catégories de cartes parmi les premiers tirages. Il ne modélise pas le mana, les mulligans, les capacités réellement lancées, les réponses, le combat ni les victoires.
- Le workflow `commander-legality.yml` consulte les données Scryfall de manière **live**, contrôle la légalité Commander et rejette tout Game Changer déclaré dans les cartes. Légale en Commander ne signifie pas optimale en B3.
- Le banc Forge pourra observer de vraies parties A/B, mais ses IA n'activent pas nécessairement correctement les synergies nouvelles ; un mauvais résultat ne démontre pas nécessairement qu'une carte ne fonctionne pas contre des humains.
- Test humain souhaité : nombre d'Incubateurs créés/transformés, marqueurs et force cumulée, tour de première grosse attaque, dégâts de combat, dégâts de drain, cartes non jouées, wraths, sources de pioche et victoires. **Le critère principal est le taux de victoires obtenues par présence et combat**, pas le nombre de triggers drain.

La V3 et les **sept decks Forge canoniques** restent inchangés. La V4 est dans `decks/Brimaz_V4_B3.txt` pour Moxfield/Archidekt et `deck_candidates/Brimaz_V4_B3.dck` pour Forge. Ne pas remplacer le DCK original témoin.

### Textes Oracle utiles

[Brimaz](https://mtg.wtf/card/moc/2/Brimaz-Blight-of-Oreskos) · [Banner](https://mtg.wtf/card/fdn/127/Banner-of-Kinship) · [Gix](https://mtg.wtf/card/tdc/181/Gix-Yawgmoth-Praetor) · [Esper Sentinel](https://mtg.wtf/card/mh2/328/Esper-Sentinel) · [Solemn Simulacrum](https://mtg.wtf/card/m21/239/Solemn-Simulacrum) · [Wizards Brackets](https://magic.wizards.com/en/formats/commander)
