# Commander empirique : normalisation des tours et vrai diagnostic Brimaz

Date d'analyse : 10 octobre 2026. Source du code moteur : Forge 2.0.15,
`forge-game/src/main/java/forge/game/phase/PhaseHandler.java`.

## 1. Distinction indispensable : tour global et tour d'un joueur

Forge incremente `PhaseHandler.turn` une fois par tour **de joueur**, et non
par rotation de quatre joueurs. `Turn: Turn 40` represente environ dix
rotations au debut d'une partie a quatre, mais ne peut pas etre divise
arbitrairement par quatre quand des joueurs meurent ou obtiennent des tours
supplementaires. L'analyseur `scripts/audit_edh_pacing.py` compte les tours
reels de chaque siege a partir des evenements `Turn: Turn N (Ai(seat)-...)`.

## 2. Referentiel humain mesure et limites

- https://playgroup.gg/about : **720 000+ parties Commander** enregistrees
  (papier+Live) au 9 octobre 2026. Ce sont des parties, pas des listes.
- https://playgroup.gg/commander/how-to-play : **547 279 parties
  multijoueurs**, mediane **9 rotations**, duree mediane **58 minutes**.
  Les parties du top 10% durent 112+ minutes en temps reel.
- https://playgroup.gg/commanders/2396-brimaz-blight-of-oreskos :
  **2466 parties Brimaz**, taux de victoire publie **19%**, tour de
  victoire moyen environ **10** (toutes listes et puissances confondues).
  Parmi les conditions de victoire declarees pour ce commandant :
  **66,89% combat**, **14,86% poison**, **7,77% blessures non-combat**.
  Le Brimaz V3 canonique n'est PAS un deck producteur de poison :
  ne jamais injecter de bonus poison artificiel dans sa politique.
- https://playgroup.gg/playgroup-live/how-sparring-works :
  sous-ensemble de **6 934 vraies parties Live** avec **21 480 interactions** :
  58% retrait cible, 19% contres, 13% wraths, 7% bounce, 3% edicts.
  Les wraths sont observees environ 2,5 fois plus souvent face a >=3
  creatures que face a 0-1 (correlation, non regle Magic).
- Ces sources sont des **agregats publics**, pas un export de millions de
  trajectories integrales contenant toutes les actions de joueurs. La
  source Live detaillee est un sous-ensemble. Ne pas pretendre disposer
  de traces individuelles privees ou de donnees d'entrainement exhaustives.

## 3. Mesures de 4 parties V8 reelles

Workflow CI : https://github.com/Toko177/brimaz-forge-lab/actions/runs/37997796527

| Pod et seed | Dernier compteur global | Maximum de tours d'un joueur | Tours joues par Brimaz | Brimaz 1ere invocation | Terrains joues au 8e tour personnel |
|---|---:|---:|---:|---:|---:|
| artifact 20281009 | 31 | 10 | 7 | Jamais | 3 |
| artifact 20281010 | 42 | 12 | 8 | Tour personnel 4 | 7 |
| aristo 20281009 | 59 | 16 | 15 | Tour personnel 9 | 3 |
| aristo 20281010 | 51 | 14 | 13 | Tour personnel 4 | 7 |

Toutes les parties V8 sont terminees naturellement; **0 victoire Brimaz**.
La mediane des maxima de tours personnels est **13**, comparee aux
**9 rotations** de la source humaine. Quatre parties contre des pods
precis ne representent PAS un echantillon robuste du format.

Observations : les deux parties ou Brimaz joue tres tard (ou jamais)
correspondent a seulement **3 terrains joues au huitieme tour**. Dans
ces quatre parties, Forge rapporte que Brimaz a conserve une main
de **7 cartes**, sans mulligan. Cela ne prouve pas une mauvaise decision
de mulligan : la probabilite de pioches ulterieures et la couleur des
sources doivent etre examinees. Ne pas fabriquer un bonus de mana.

## 4. Ce que les humains font : trajectoire d'apprentissage pertinente

Les statistiques observees peuvent servir de distribution de reference
pour le controle qualite des politiques, **jamais** de modification
artificielle des regles ni de delai d'arret obligatoire. Tester :
1. Ouvrants : qualite des mains conservees, couleurs des sources,
   terrains joues et ramp disponible aux tours personnels 1-4.
2. Developpement : etudier tour de premiere invocation de Brimaz,
   re-lancement avec commander tax, cartes phyrexianes jouees avant/apres.
3. Interaction : choix d'anti-betes au bon moment, conservation
   des reponses contre les menaces reelles, comportement devant une
   table large / une wrath.
4. Combat et conclusion : degats utiles, attaques non-suicidaires,
   elimination des adversaires faibles, capacite a convertir l'avance
   en victoire; verifier l'absence de faux bonus poison.
5. Robustesse : repro de la graine, depassements AI_TIMEOUT,
   declarations d'attaques invalidees, actions Forge ignorees.

## 5. Limites statistiques pour l'objectif 20%

Le chiffre empirique 19% de Brimaz toutes listes confondues est un
point de comparaison, **pas** la probabilite de victoire de la V3
contre nos six decks fixes. Pour mesurer le winrate V3 de maniere
serieuse, il faut d'abord de nombreuses parties de 4 IA representant
des comportements legaux, une bonne couverture de toutes les places,
la conservation des censures, et des intervalles de confiance.
Il est trompeur de declarer qu'une partie est anormalement longue
parce que le log mentionne un tour global 40; les anomalies doivent
se mesurer sur les tours personnels, le mana, les interactions et
la dynamique des menaces.
