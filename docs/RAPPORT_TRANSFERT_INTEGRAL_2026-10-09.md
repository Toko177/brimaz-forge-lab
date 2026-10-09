# Rapport de transmission intégral — Brimaz Forge Lab

**Établi le 9 octobre 2026 (Europe/Paris).**  
**Dépôt privé :** https://github.com/Toko177/brimaz-forge-lab  
**Objet :** conception, exécution et audit d'un moteur de parties Magic: The Gathering Commander (EDH), avec quatre IA, pour mesurer et améliorer le deck **Brimaz, Blight of Oreskos**, puis comprendre les différences avec son pilotage humain.

> **Consigne centrale à reprendre :** obtenir des parties **réelles et légalement jouées** via le moteur de règles Forge ; une victoire ne vaut rien si un adversaire n'a pas ses 100 cartes, si le moteur a planté, si la partie a été arrêtée à la limite de temps ou si l'IA a reçu un avantage artificiel. Ne jamais inventer de parties, de statistiques ou de capacité de l'IA.

## A. État exécutif vérifié

1. **Architecture réelle opérationnelle :** Forge 2.0.15, Java 21, Forge CLI `sim`, quatre sièges IA, exécutée en environnement Linux via GitHub Actions. Moteur officiel de règles et effets des cartes, pas une simulation simpliste de pioches ou une estimation probabiliste.
2. **Parallélisation implémentée :** matrice de 16 tâches GitHub Actions avec au plus huit jobs simultanés ; deux parties successives par tâche dans la campagne type, soit **32 parties**. Chaque tâche conserve les graines, journaux et résultats ; les processus Forge sont isolés par JVM.
3. **Sources vérifiées :** Brimaz V3 à 100 cartes, six adversaires publics d'un membre du playgroup (compte Archidekt `KaalDeagle`), validés par Scryfall (légalité Commander, couleurs, quantités) et par **la vraie base de données de Forge : sept decks, 700 cartes au total** (comptant les copies de terrains de base).
4. **Campagne canonique initiale :** 32 parties, **29 parties avec victoire naturelle certifiée**, 3 parties censurées ; **Brimaz 0/29**. Il s'agit du couple « liste + décisions de l'IA Forge », pas d'une preuve de faiblesse intrinsèque de la liste entre les mains d'un humain.
5. **Bug moteur découvert :** dans Forge 2.0.15, évaluation de capacités modales (`CharmEffect.makeFormatedDescription / makePossibleOptions`) sans `activatingPlayer` ; `TargetRestrictions.getAllCandidates` lançait des `NullPointerException`. Un patch minimal de `CharmEffect` a été compilé et testé.
6. **Première victoire réelle de Brimaz depuis ce correctif :** IA Forge `Default`, pod Radha/Tazri/Zimone-Dina, Brimaz siège 2, graine **20291010**, tour 24, **356 476 ms** pour une limite de **360 000 ms**, adversaires tous éliminés à **0 PV**. Certificat automatique individuel sans erreur Java détectée : [run 37969492744](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744). Important : graine choisie pour reproduire un échec antérieur et victoire très proche de la limite ; **ce n'est pas une victoire d'un nouvel échantillon indépendant ni un taux de victoire représentatif**.
7. **IA custom expérimentales V1–V6 :** correctifs Java compilés sur les classes de Forge et injectés dans une copie du JAR ; amélioration de certaines capacités spécifiques de Brimaz et accès contrôlé à quelques cartes exclues de l'IA standard. Les campagnes testées ne démontrent **pas encore** d'augmentation robuste du taux de victoire.
8. **Dernières Actions inspectées :** tous les workflows répertoriés jusqu'au run **37970476445** sont terminés, le plus récent s'étant achevé le 9 octobre 2026 à 18:02 UTC (20:02 heure de Paris). Les séries V5/V6 sont des **pilotes**, pas une nouvelle campagne de centaines de parties.

## B. Objectif initial et motivation

L'utilisateur cherche à améliorer son deck Commander **Brimaz, Blight of Oreskos**, typé Orzhov (blanc/noir), Incubateurs/Phyrexians, marqueurs +1/+1, sacrifices, prolifération, drains de vie et récursion. Objectif de puissance : environnement de playgroup réel, préférablement **Bracket 3**, avec **aucun Game Changer dans Brimaz V3**. L'utilisateur gagne parfois avec ce deck en partie humaine : le taux de 0 victoire obtenu par Forge est donc un **signal fort d'un pilotage IA déficient, de déséquilibres du panel ou de bugs**, pas une conclusion définitive sur le deck.

Avant le laboratoire, des audits sur **144 cartes candidates initiales**, puis une sélection V3 Moxfield, avaient été effectués. Des fichiers historiques de la bibliothèque ChatGPT existent, notamment :

- `Brimaz_audit_144_cartes_initiales.csv`
- `Brimaz_audit_complet.md`
- `Brimaz_V3_rapport_tests_et_limites.md`
- `Brimaz_V3_sans_Game_Changers_Moxfield.txt`

L'**état de référence effectivement simulé** est figé dans le dépôt : [decks/Brimaz_V3.txt](../decks/Brimaz_V3.txt), 100 cartes exactement ; commandant `Brimaz, Blight of Oreskos`. Une modification future de liste doit créer une **nouvelle version explicite** (V4-deck, etc.), sans écraser la baseline utilisée dans les comparaisons.

L'utilisateur veut **que l'assistant fasse lui-même les expériences**, via GitHub Actions et le dépôt connecté, sans devoir exécuter manuellement un logiciel sur son PC à chaque étape.

## C. Accès au dépôt et architecture technique

### Connexion
- Compte/dépôt : https://github.com/Toko177/brimaz-forge-lab
- Dépôt privé, accès d'écriture accordé par la connexion de l'app/plugin GitHub dans ChatGPT.
- Dans une nouvelle conversation, **réutiliser cette URL et vérifier la présence des outils GitHub connectés**. Si la connexion n'est plus active, demander de la reconnecter ; ne pas redemander l'URL déjà connue.
- Les GitHub Actions tournent dans le cloud GitHub ; l'assistant peut lire les journaux et modifier le dépôt via la connexion GitHub.

### Forge
- Projet amont : https://github.com/Card-Forge/forge
- Version de référence : tag **`forge-2.0.15`**.
- Distribution officielle : `forge-installer-2.0.15.tar.bz2`, téléchargement possible depuis les **releases GitHub** ; le user avait également importé une archive de 297 Mo en bibliothèque.
- Hash SHA-256 de la distribution vérifié dans les workflows :
  `4468f182b60f6ca62d89697baa208981085af744f116781af751c611826db600`.
- Environnement GitHub `ubuntu-latest`, Temurin Java **21**, JAR exécutable `forge-gui-desktop-*-jar-with-dependencies.jar`.
- Les correctifs locaux recompilent des classes Java à partir des sources du **tag exact**, puis les injectent dans une **copie** du JAR avec `jar uf`. Garder une baseline Forge originale pour comparaison.

### CLI utilisé
Représentation générale :

    java -Xmx4g -jar /chemin/forge-gui-desktop-...-jar-with-dependencies.jar sim \
      -d Brimaz_V3.dck Kaal_9594008.dck Kaal_10347090.dck Kaal_21930525.dck \
      -D /chemin/forge_decks -f Commander -n 1 -c 360 \
      -s 20261009 -a Default Default Default Default

- `-d` : quatre decks (dans l'ordre des sièges).
- `-D` : répertoire des `.dck`.
- `-f Commander` : format EDH.
- `-n 1` : une partie par JVM ; indispensable pour inspecter séparément le résultat, le seed et les exceptions.
- `-c 360` : limite Forge par partie ; **une partie arrêtée à cette limite est censurée**, même si le moteur affiche un gagnant.
- `-s` : graine, préservée en métadonnées.
- `-a` : profil d'IA par siège (`Default`, `Experimental`, `Reckless`, `Cautious`, etc.).
- Temps limite du sous-processus Python souvent `--timeout 445` ; GitHub a son propre `timeout-minutes`.
- La graine commune **ne garantit pas des distributions de cartes identiques après que les actions d'IA divergent** et consomment des tirages différents.

### Scripts centraux
- [scripts/smoke.py](../scripts/smoke.py) : partie pilote, génération Brimaz et contrôle de terminaison.
- [scripts/batch.py](../scripts/batch.py) : parties Forge séquentielles dans une tâche, paramètres pod/rotation/profil/graine/clock, logs et `games.json`. La version corrigée **ne réécrit plus les decks canoniques** et distingue une censure attendue d'une panne CI.
- [scripts/aggregate_batch.py](../scripts/aggregate_batch.py) : agrège des artifacts de nombreux jobs, taux de victoire, intervalle de Wilson, censures et couverture des sièges. **Bug de clé corrigé** : inclure `policy` pour éviter les collisions entre mêmes sièges/graines du stock et de V4.
- [scripts/certify_commander_games.py](../scripts/certify_commander_games.py) : filtrage des victoires valides, confrontées aux rapports Scryfall, aux logs réels, au format à quatre IA, aux exceptions et aux délais.
- [scripts/diagnose_canonical.py](../scripts/diagnose_canonical.py) : métriques de diagnostic des 32 parties, cas bloqués et taux d'utilisation des cartes/du commandant.
- [scripts/audit_ai.py](../scripts/audit_ai.py) : timings, capacités et sacrifices observés.
- [scripts/audit_planner_resolution.py](../scripts/audit_planner_resolution.py) : relie les décisions IA aux véritables activations sur le **même numéro de tour**.

## D. Provenance des adversaires

Sources indépendantes utilisées avant le playgroup :
- Krenko : https://archidekt.com/decks/10174296/krenko
- Muldrotha : https://archidekt.com/decks/3732210/sac_muldrotha
- Yuriko : https://archidekt.com/decks/5411992/yuriko
- Autres candidats Sidisi, Shilgengar, Galazeth. Attention : la liste Yuriko originale n'avait que **96 cartes réellement incluses** après exclusion du Maybeboard ; **jamais remplir artificiellement**.
- L'API Archidekt a retourné ponctuellement **HTTP 403** ; les fichiers JSON ont été conservés comme artifacts GitHub pour stabiliser les importations.

Compte de membre du playgroup à privilégier :
https://archidekt.com/u/KaalDeagle

- **25 listes publiques** découvertes sur le compte (dont 22 affichées à 100 cartes), et huit listes sélectionnées et converties au format Forge à 100 cartes.
- Les catégories de travail telles que `Maybeboard`, `Consider`, `Upgrades` doivent être **exclues selon `includedInDeck`**, sans supprimer arbitrairement des cartes utiles.
- JSON/`.dck` historiques de l'import : [run 37952122924](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37952122924), artifact `kaal-playgroup-deck-snapshots`.
- Scripts : [discover_kaaldeagle.py](../scripts/discover_kaaldeagle.py), [import_playgroup.py](../scripts/import_playgroup.py), [import_archidekt.py](../scripts/import_archidekt.py).

Huit listes structurées vérifiées à l'import :

| Identifiant Forge | Commandant(s) | URL / remarques |
|---|---|---|
| `Kaal_9594008` | Radha, Heir to Keld | https://archidekt.com/decks/9594008 — `EDH Radha - Légumes explosifs` ; bracket 3 déclaré |
| `Kaal_10347090` | Tazri, Beacon of Unity | https://archidekt.com/decks/10347090 — `EDH Dungeon Party Time` ; bracket 3 déclaré |
| `Kaal_21930525` | Zimone and Dina | https://archidekt.com/decks/21930525 — aristocrats ; bracket non déclaré |
| `Kaal_23328062` | Lathril, Blade of the Elves | https://archidekt.com/decks/23328062 — elfes ; `Demonic Tutor` Game Changer |
| `Kaal_11485202` | Urza, Chief Artificer | https://archidekt.com/decks/11485202 — artefacts |
| `Kaal_20861410` | Wilson, Refined Grizzly + Noble Heritage | https://archidekt.com/decks/20861410 — commandant + background |
| `Kaal_22106142` | Quintorius, History Chaser | https://archidekt.com/decks/22106142 |
| `Kaal_22193355` | Amalia Benavides Aguirre | https://archidekt.com/decks/22193355 — `Ad Nauseam` et `Bolas's Citadel` Game Changers |

**Sept decks** (Brimaz + six adversaires) sont inclus dans le test canonique. Wilson et Quintorius ont été importés, mais ne figurent pas dans les deux pods principaux.

### Deux pods standardisés

**Pod « aristo » :**
1. Brimaz V3
2. Radha — `Kaal_9594008`
3. Tazri — `Kaal_10347090`
4. Zimone and Dina — `Kaal_21930525`

**Pod « artifact » :**
1. Brimaz V3
2. Lathril — `Kaal_23328062`
3. Urza — `Kaal_11485202`
4. Amalia — `Kaal_22193355`

Au cours d'une série, ces positions tournent : Brimaz occupe tour à tour les sièges 1/4/3/2 suivant la rotation du script. **Les deux pods ne sont pas équilibrés en restrictions de construction** : Amalia a deux Game Changers, Lathril un ; Brimaz aucun. Ne jamais traduire une faible performance contre ce panel en `winrate bracket 3 général`.

## E. Contrôle de légalité des cartes : terminé

Initialement, certaines listes `.dck` contenaient `Selfless Glyphweaver // Deadly Vanity` ou d'autres noms recto-verso composites. Scryfall les reconnaissait, mais Forge utilisait le **nom de la face principale** et pouvait signaler `Card not found`. Cela rendait les anciennes confrontations suspectes malgré leur apparent succès.

Pipeline corrigé :

1. [validate_commander_legality.py](../scripts/validate_commander_legality.py) : consulte Scryfall (`cards/collection`) ; contrôle 100 cartes, commandant(s), identité couleur, singleton, cartes bannies et Game Changers.
2. [normalize_forge_decks.py](../scripts/normalize_forge_decks.py) : convertit uniquement les noms des cartes à faces multiples en identifiants primaires compatibles Forge, sans changer une seule carte ni quantité ; consigne les mappages et SHA-256.
3. [VerifyAllForgeCards.java](../tests/java/forge/integration/VerifyAllForgeCards.java) : initialise la **vraie base Forge** et vérifie individuellement les 100 cartes de chaque deck.
4. Les jeux normés et rapports Scryfall sont conservés dans des artifacts et réutilisés avec vérification de hachage.

**Résultat : 7 decks sur 7 légaux et reconnus, 700 cartes reconnues par Forge (avec les copies).**  
Runs : [légalité 37965067128](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37965067128), [vérification Forge 37966009166](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37966009166).

Le SHA-256 du **Brimaz original au format .dck**, validé Scryfall :
`ffddc4bcc1068c22a96b115f610886f26edf38c6328469b3881110150c9d0c0d`.
Le SHA de chaque version normalisée figure dans le rapport d'artifact. Ne pas reconstituer le `.dck` en écrasant sa version canonique au moment de lancer les jeux.

## F. Chronologie factuelle des expériences

La numérotation ci-dessous distingue **vraies parties Forge** et travaux IA.

| Étape | Résultat et apprentissage |
|---|---|
| Prototype de laboratoire | Préparation d'un programme Python, decks et CI ; initialement aucune simulation réellement prouvée. |
| Mise en place GitHub | Connexion du dépôt privé, publication de la liste Brimaz et du workflow Forge. |
| Premier test miroir | 4 IA Brimaz, fin provoquée par la limite de 120 s : **non exploitable** statistiquement. |
| Deuxième test miroir | 4 IA Brimaz, une victoire naturelle d'une IA après environ 140 s ; plusieurs capacités Brimaz/Incubateurs observées. |
| Premier match mixte public | Brimaz / Krenko / Muldrotha / Krenko ; Krenko gagne ; véritable moteur Forge. |
| Première table KaalDeagle | Brimaz / Radha / Tazri / Zimone-Dina ; Zimone-Dina gagne en ~80 s. |
| Série tournante 4 parties | Brimaz 0/4 ; Radha 2, Tazri 2. |
| Première matrice parallèle | 32 parties sur 16 tâches, 31 naturelles et 1 censurée, Brimaz 0/31 (`Default` vs `Experimental`). |
| Profil agressif `Reckless` | 16 parties, 14 naturelles, 2 censurées, Brimaz 0/14. |
| Politique Brimaz V1 | 16 parties naturelles, Brimaz 0/16 ; 3 propositions du nouveau planificateur dans 2 parties. |
| Politique V2 | 16 parties, 15 naturelles, 1 censurée, Brimaz 0 ; prise en charge de plus d'outlets de sacrifice. |
| Politique V3 | 16 parties, 15 naturelles et 1 censurée ; Brimaz 0 ; 4 propositions d'actions effectivement retrouvées dans les logs au bon tour. |
| Politique V4 | 16 parties, 14 naturelles et 2 censurées ; Brimaz 0 ; 6 propositions dans 3 parties ; scoring sans poison. |
| 32 parties canoniques | Forge original vs V4, 16 chacun : **29 naturelles certifiées, 3 censurées, Brimaz 0/29**. |
| Postmortem des 32 | Détection du bug `CharmEffect` et de 9 cartes Brimaz marquées `AI:RemoveDeck:All`. |
| Reproduction du bug corrigé | Trois graines ciblées : disparition de l'exception ; 2 parties toujours censurées, 1 victoire de Brimaz. |
| **Première victoire Brimaz certifiée** | Graine 20291010, tour 24, 356,476 s / 360 s, IA Default et correctif Charm ; **une vraie victoire du moteur**. |
| IA V5 | 8 parties canoniques naturelles, Brimaz 0/8 ; meilleure priorité au commandant, 11 actions de priorité, 12 lancements de Brimaz. |
| IA V6 | 4 parties canoniques certifiées, Brimaz 0/4 ; 7 actions prioritaires de commandant, 4 cast d'engines (`Orzhov Signet` 1, `Krark-Clan Ironworks` 3, `Spawning Pit` 0). |

**Ne jamais additionner tous les numérateurs/dénominateurs comme s'il s'agissait d'un seul échantillon aléatoire homogène.** Les panels, politiques, listes historiques, bugs, seeds et critères d'acceptation ont évolué. Certaines expériences réutilisent volontairement les mêmes graines et adversaires.

Principaux runs :

- [Miroir original Forge 37948809314](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37948809314)
- [Premier test playgroup 37952258312](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37952258312)
- [Série de quatre 37952882248](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37952882248)
- [Premières 32 parallèles 37955082304](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37955082304)
- [Reckless 37957029216](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37957029216)
- [V1 37959185948](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37959185948)
- [V2 37960666613](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37960666613)
- [V3 37962437566](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37962437566)
- [V4 pilote / campagne 37965516362](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37965516362)
- [Canonique 32 37966298484](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37966298484)
- [Postmortem canonique 37968248090](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37968248090)
- [Régression de l'exception Charm 37968565113](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37968565113)
- [Certificat première victoire 37969492744](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744)
- [V5 37969072177](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969072177)
- [V6 37969934893](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969934893)
- [Régression horloge longue 37970015405](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37970015405)
- [Audit V6 37970476445](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37970476445)

## G. Causes diagnostiquées de la faiblesse de Brimaz

### G.1. Mauvaise utilisation du commandant
Dans les 32 parties canoniques :
- **4/32** n'ont enregistré **aucun lancement de Brimaz**.
- En moyenne **1,06 lancement de Brimaz par partie**.
- **26/32** sans déclenchement de prolifération en étape de fin détecté dans les logs.
- De nombreux déclenchements ont été confondus dans les premières statistiques : **« incubate » à la sortie d'un sort** et **« proliferate » au début de l'étape de fin** sont deux capacités différentes à mesurer séparément.

Le planificateur V5 a rendu le commandant plus prioritaire lorsque le sort était réellement légal, abordable (taxe incluse) et au bon timing, sans créer du mana ni tricher sur le coût.

### G.2. Mauvaise exploitation des sacrifices et des tours adverses
Règle cruciale : la seconde capacité de Brimaz vérifie si un Phyrexian contrôlé est **mort AVANT le début** de l'étape de fin. Sacrifier **pendant** l'étape de fin ne crée pas rétroactivement le déclenchement de cette étape.

- Un premier audit sur 4 parties observait 12 utilisations de moteurs de sacrifice (11 `Arcbound Ravager`, 1 `High Market`), mais pas de stratégie claire de déclenchement sur les tours adverses.
- Sur 32 parties, **32 activations d'outlets avant une étape de fin adverse**, concentrées dans seulement **7 parties**, principalement en phase de blocage. Les IA semblent réactives plutôt que proactives.
- L'IA doit décider de sacrifier **avant** l'étape de fin de chaque joueur, en tenant compte de la valeur de la créature perdue, des marqueurs à proliférer, des effets de mort et des bloqueurs requis.

### G.3. Avertissements Incubate
Forge 2.0.15 rapporte fréquemment `No AI assigned for API: Incubate` ; la capacité peut se résoudre selon les règles, mais l'IA ne dispose pas d'une logique de décision aussi ciblée.
Un essai reliant l'API `Incubate` au gestionnaire générique `AlwaysPlayAi` a **supprimé l'avertissement**, mais la partie pilote a été **censurée**. **Ne pas adopter ce patch par défaut** : supprimer un warning n'est pas démontrer un bon pilotage.

### G.4. Cartes ignorées par les heuristiques Forge
Inspection réelle des scripts de la base Forge : **9 cartes de Brimaz** ont l'indication `AI:RemoveDeck:All` :

1. Phyrexian Delver
2. Orzhov Signet
3. Krark-Clan Ironworks
4. Spawning Pit
5. Phyrexian Reclamation
6. Tortured Existence
7. Diabolic Intent
8. Fetid Heath
9. Phyrexian Tower

Cela peut retirer du choix normal de l'IA de puissants moteurs du deck. **Nuance :** certaines capacités de mana passent par des traitements différents ; « RemoveDeck:All » n'implique pas qu'aucune capacité du permanent ne fonctionne jamais. `AI:RemoveDeck:Random` (comme sur `Throne of Geth`) n'est pas le même filtre et concerne surtout la génération aléatoire de decks IA.

V6 a commencé à autoriser **conditionnellement** `Orzhov Signet`, `Spawning Pit` et `Krark-Clan Ironworks`, sur le seul siège Brimaz, avec les coûts et timing légaux de Forge ; tutorat et récursion restent difficiles et non corrigés.

### G.5. Les adversaires ne sont pas tous de puissance égale
`Amalia Benavides Aguirre` dominait particulièrement le pod artefacts : **12 victoires sur 16 matchs** cumulant stock + V4, et son deck joue deux Game Changers. Dans le pod aristo, Tazri/Radha peuvent prendre le dessus très vite. Ces parties sont utiles pour identifier la robustesse, mais pas pour obtenir un taux universel « bracket 3 ».

### G.6. Le bonus poison était hors sujet
On avait initialement ajouté au scoring une valeur pour la prolifération de marqueurs poison déjà présents sur les adversaires. **La liste Brimaz V3 n'a pas de plan produisant du poison.** Le bonus fut supprimé en V4, en valorisant plutôt `Marionette Apprentice`, `Mirkwood Bats`, `Elas il-Kor, Sadistic Pilgrim`, `Scheming Aspirant`, les marqueurs, les morts et les effets de drain.

## H. Politiques IA custom : évolution et statut

Les patchs modifient `forge.ai.AiController` et ajoutent `BrimazTurnPlanner`, après compilation depuis les sources du tag correspondant. **Ne modifient pas les cartes ni leur texte** ; la plupart ne modifient pas les règles, à l'exception de la correction séparée du bug Charm.

| Version | Principes et état |
|---|---|
| V1 — [patch_forge_brimaz.py](../scripts/patch_forge_brimaz.py) | Proposer un sacrifice volontaire de jeton Phyrexian peu puissant pendant la seconde main adverse, avant l'étape de fin, via Ravager ou Bartolomé ; choisir un jeton plutôt qu'une créature importante. Compilée, actions observées, **pas de gain de victoires**. |
| V2 — [patch_forge_brimaz_v2.py](../scripts/patch_forge_brimaz_v2.py) | Étend `Throne of Geth` et `Spawning Pit`, ajustement selon permanents porteurs de marqueurs. Compilée, meilleure couverture tactique, **pas de gain démontré**. |
| V3 — [patch_forge_brimaz_v3.py](../scripts/patch_forge_brimaz_v3.py) | Score de sacrifice fonction de la puissance du jeton, marqueurs alliés/adverses, défenses et phases de fin, y compris sa propre seconde main. **7 tests Java déterministes passés.** |
| V4 — [patch_forge_brimaz_v4.py](../scripts/patch_forge_brimaz_v4.py) | Supprime le bonus poison ; introduit l'apport des effets de mort et de drains réellement présents. **8 tests Java passés**, campagnes sans victoire et erreurs/censures historiques. |
| V5 — [patch_forge_brimaz_v5.py](../scripts/patch_forge_brimaz_v5.py) | Priorité contrôlée pour **jouer le commandant** en première main si légal/abordable, puis transformer des Incubateurs utilisables. Huit parties pilotes certifiées, **0 victoire**, 11 propositions de priorité et 12 lancements de Brimaz. |
| V6 — [patch_forge_brimaz_v6.py](../scripts/patch_forge_brimaz_v6.py) | Accès conditionnel aux sorts normalement filtrés `Orzhov Signet`, `Spawning Pit`, `Krark-Clan Ironworks` ; KCI pris en charge comme outlet de mana/sacrifice dans la politique. Quatre parties canoniques certifiées, **0 victoire** ; 7 actions de priorité commandant, 4 pour engines. |

**Aucune V1–V6 n'a prouvé qu'elle constitue un pilote humain compétent.** Les améliorations de métriques de décision et le passage des tests Java ne prouvent pas une hausse du taux de victoire.

### Qualité de l'instrumentation
Forge écrit les diagnostics `System.out` du planificateur **en temps réel**, mais restitue les événements du jeu dans un tampon **plus tard**. Un premier auditeur recherchait une activation après chaque ligne `BRIMAZ_PLANNER` et trouvait faussement zéro activation. La correction associe les événements par **identifiant de tour**.

Sur V3, **4 propositions** étaient effectivement associées à **4 activations `Arcbound Ravager`** et à des déclenchements de Brimaz pendant la fin des tours concernés. Cela prouve l'intégration technique, **pas le choix optimal**, ni que chaque sacrifice était la seule cause du déclenchement.

Audit corrigé : [37963707613](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37963707613).

## I. Bug Forge `CharmEffect` : cause, patch et reproduction

### Trace observée dans les trois matchs problématiques
Les 3 transcriptions canoniques censurées incluaient des erreurs Java liées à :

    ComputerUtilCost.checkDiscardCost
      -> Card.getAbilityText
      -> CharmEffect.makeFormatedDescription
      -> CharmEffect.makePossibleOptions
      -> TargetRestrictions.getAllCandidates
      -> SpellAbility.getActivatingPlayer() == null
      -> NullPointerException

Forge évaluait des choix de modalités/cibles alors que la capacité modale ne disposait pas encore d'un joueur activant. Cela pouvait déclencher des erreurs internes répétées et allonger ou perturber la partie.

### Correction en place
[patch_forge_charm_context.py](../scripts/patch_forge_charm_context.py) :

- Source épinglée `forge-2.0.15/forge-game/src/main/java/forge/game/ability/effects/CharmEffect.java`.
- Avant de calculer les cibles possibles, si le joueur activant manque, le récupérer sur la capacité parente ou le contrôleur de la carte.
- Ne modifie ni les coûts, ni les cartes, ni l'ordre des phases, ni les cibles légales.
- Recompile la classe contre le JAR officiel ; patch opt-in conservé séparément.
- Les trois graines de reproduction ne remontent plus la `NullPointerException`.
- À `-c 360`, deux parties restaient censurées ; la troisième, avec IA Default, gagnée par Brimaz.
- Un prolongement d'horloge `-c 600` a été exécuté sur des graines ciblées : au moins un match se termine naturellement après correction, mais un autre reste censuré à environ 612 s de durée murale. **Augmenter le délai ne garantit pas que l'IA termine la partie.**

Workflows de régression : [37968565113](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37968565113), [37970015405](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37970015405).

### Première victoire Brimaz
- [Certificat indépendant 37969492744](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37969492744).
- **Brimaz = siège 2**, pod Radha/Tazri/Zimone-Dina, seed **20291010**.
- Forge `Default` + **seul correctif Charm** pour le bug des modalités/cibles.
- **Tour 24**, durée **356 476 ms**, limite **360 000 ms**.
- Chaque adversaire perd à **0 PV** ; `Game Outcome` constate que Brimaz gagne parce que tous les autres ont perdu.
- Le certificat a vérifié la liste légale, les sièges, le gagnant, les erreurs et le transcript.
- Hash exact du transcript :
  `a3655fbb2e30ab53f581d96c3e6bb688296ef1842a6d2f8210e266e9aab85c1d`.
- **Réserve majeure :** fin seulement 3,524 s avant la limite Forge. Ne pas conclure à une supériorité ou à un taux de victoire. Rejouer à `-c 600` ou `-c 900` **avec la même graine et le correctif**, pour vérifier la stabilité, et inspecter toute la séquence finale (létalité réelle, pas un événement produit par cutoff).

## J. Parallélisation et politique de traitement des erreurs

`.github/workflows/parallel-benchmark.yml` et les workflows de campagnes V1–V6 utilisent une **matrice de jobs** (pod × rotation × profil/politique), isolés en JVM. Limite par défaut `max-parallel: 8`. Plusieurs parties successives dans un job limitent la consommation mémoire du runner. Attention : les quotas et minutes GitHub ne sont pas illimités ; éviter de lancer des centaines de nouvelles parties **avant** d'avoir résolu les bugs et les mesures.

Classification des parties :
- **`complete`** : une fin naturelle valide du moteur, gagnant unique et sortie process réussie.
- **`clock_censored`** : arrêt à la limite du moteur `-c` ; aucune victoire à attribuer, mais garder le transcript pour diagnostic.
- **`process_timeout`** : le processus ne termine pas dans la limite Python ; échec à investiguer.
- **`engine_failed`** : code sortie non nul ou erreur interne bloquante ; échec.
- **`unparsed` / `missing_game_result`** : résultat absent ou incomplet ; jamais une victoire certifiée.

Bugs CI corrigés :
1. Les parties censurées déclenchaient à tort l'échec du job, bien qu'elles soient de vrais événements statistiques à conserver. `scripts/batch.py` n'échoue plus pour une seule censure.
2. L'agrégateur utilisait `pod/rotation/repeat/seed/profil` comme identifiant et **oubliait la politique IA**, provoquant des collisions `stock` vs `V4`. Ajout de `policy` : postmortem des 32 réussi.
3. Le batch initial **réécrivait** parfois le `.dck` Brimaz après vérification de hash ; la version canonique doit rester inchangée, avec option `--require-canonical-decks`.
4. Les logs temps réel et le transcript tamponné n'étaient pas en ordre temporel ; corrélation par numéro de tour, pas par proximité de lignes.

## K. Protocole de « vraie victoire » : ce qu'il garantit et ce qu'il ne garantit pas

Le laboratoire a un protocole documenté dans [docs/realism-protocol.md](../docs/realism-protocol.md).

Une victoire digne d'intérêt exige :

1. **Légalité Commander** de tous les decks selon Scryfall (100 cartes, couleurs, singleton, bans).
2. **Identifiants de toutes les cartes reconnus par Forge** ; aucun nom composite introuvable, aucun deck tronqué.
3. **Quatre IA réellement actives**, pas deux joueurs ou un proxy statistique.
4. Coûts, phase, priorité, pile et cibles résolus par **le moteur de règles Forge**, sans créatures ou mana fabriqués.
5. Sortie **naturelle** avec un vainqueur unique ayant réellement éliminé les adversaires.
6. **Aucune erreur fatale Java** ou incohérence `Game Outcome` / `Game Result` / `games.json`.
7. Graine, rotation, versions du patch, listes et hash du transcript conservés.
8. Une partie expirée ne fournit **aucune victoire**, même si Forge désigne automatiquement un gagnant.
9. Les défaites comptent autant que les victoires ; **ne pas sélectionner uniquement les graines favorables**.
10. Les correctifs du moteur de règles (comme Charm) doivent être **déclarés** et faire l'objet de régressions, pas glissés silencieusement dans les résultats.

Ce protocole **n'est pas une preuve mathématique que chaque effet complexe respecte Oracle Magic**. Les bugs spécifiques de cartes, de contrôleurs et de règles restent possibles. L'objectif est une crédibilité empirique contrôlée, avec tests ciblés et traçabilité.

## L. Prototype multijoueur avancé : état réel

Forge dispose de simulation d'états (`USE_HYBRID_SIMULATION` / `USE_FULL_SIMULATION`), mais le code amont 2.0.15 contient des hypothèses de duel :

- `GameSimulator` utilise historiquement un adversaire représentatif (`getWeakestOpponent`), avec TODO sur les contrôleurs de tous les joueurs.
- `GameStateEvaluator` n'évalue pas encore de façon robuste toutes les réactions de trois adversaires humains/IA.
- [patch_forge_4player_stack.py](../scripts/patch_forge_4player_stack.py) a introduit un prototype qui installe des contrôleurs simulés pour tous les joueurs présents lors de certaines résolutions, et active le mode hybride **pour Brimaz seulement** par paramètre JVM.
- Le test de compilation et une partie pilote terminée sont validés : [run 37963971969](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37963971969).
- **Cela n'est PAS encore une vraie recherche multijoueur compétitive**, ni un moteur Monte Carlo Tree Search expert. Pas de gains de winrate démontrés ; ne pas annoncer qu'on a créé trois adversaires capables d'anticiper parfaitement.

Feuille de route structurelle : [docs/multiplayer-lookahead-roadmap.md](../docs/multiplayer-lookahead-roadmap.md).

À développer à terme :
- copier intégralement l'état Forge (pile, phases, priorités, zones, capacités, choix cachés avec informations autorisées) ;
- fournir un contrôleur distinct pour **chaque** adversaire et respecter APNAP ;
- proposer les **actions légales** et explorer quelques réponses adverses critiques ;
- évaluer la survie, les menaces combinées des trois adversaires, létalité, mana restant, ressources et risques sur le cycle complet ;
- budget CPU strict par décision, fallback raisonnable ;
- tests de conformité de copies d'état et de résolution de pile ;
- comparaison avec des adversaires distincts plutôt qu'un seul adversaire faible.

## M. Tâches prioritaires recommandées à la reprise

### Priorité 0 — stabiliser la base de résultats
- Vérifier les workflows **plus récents** que `37970476445` s'il y en a : toujours actualiser GitHub avant de conclure.
- Ne pas fusionner les périodes historiques incorrectement configurées et les séries canoniques.
- Archiver une release/commit **taggée** de la baseline Forge stock + Charm, des sept decks canoniques et du résultat certifié Brimaz. Conserver les hashes et la graine.
- Résoudre les parties censurées et examiner le log complet de chacune : ralentissement de l'IA, boucles de capacités, tour 25+, combat bloqué, mauvaise utilisation des removals, problèmes d'interface.
- Tester à nouveau la première victoire à **600 ou 900 secondes**, avec le **même JAR**, le patch Charm, les quatre decks, ordre de sièges et graine exacts. Répéter au moins une fois pour vérifier le caractère déterministe de cette partie très proche de 360 s.
- Séparer « partie naturelle », « partie sans avertissement IA », « partie avec règles correctement reproduites » et « pilote stratégique compétent ». Ce sont des niveaux de validation différents.

### Priorité 1 — instruments de diagnostic de l'IA, par décision
Pour chaque tour et chaque joueur :
- commandant disponible en zone de commandement / joué / taxé / mort ;
- mana disponible, couleurs, terrains jouables, courbe ;
- taille de main et sorts possibles, y compris les cartes `AI:RemoveDeck:All` ;
- Phyrexians et Incubateurs présents, capacité de transformation payable, compte de marqueurs ;
- événements de sacrifice par joueur actif et **avant** son end step ;
- cible et cible alternative des removals, sorts contrés, menaces létales ;
- multiplicité des moteurs aristocrats, drains, tokens et points de vie des trois adversaires ;
- liste d'actions légales, scores, **raisons des rejets** et résultat de l'action choisie ;
- détection de `no-progress turns` et de boucles répétitives.

Ce qui manque surtout aujourd'hui : preuves **d'occasions légales manquées**, et non simple nombre d'activations.

### Priorité 2 — correction des heuristiques spécifiques
1. Généraliser le soutien **correct et défensif** des sources de mana `Orzhov Signet`, `Fetid Heath`, `Phyrexian Tower` : plusieurs capacités de mana suivent un chemin de décision propre ; ne pas contourner les contrôles de coûts.
2. Sélectionner intelligemment coûts/sacrifices de `Spawning Pit`, `Krark-Clan Ironworks` et `Arcbound Ravager` et les capacités d'utilisation de leurs marqueurs.
3. Ajouter `Phyrexian Reclamation`, `Tortured Existence`, `Phyrexian Delver` et `Diabolic Intent` **seulement** après tests de choix de cible/ressource et de coût correct : danger d'IA lançant un tutor/removal sans cible pertinente.
4. Corriger proprement l'IA `Incubate` (l'API manquante), puis quand transformer, quand attaquer/bloquer/sacrifier. **Ne pas réutiliser `AlwaysPlayAi` simplement pour supprimer un warning.**
5. Améliorer le timing de Brimaz avant chaque étape de fin, y compris la sienne, sans sacrifier un bloqueur indispensable.
6. Travailler le combat multijoueur, évaluation des effets « chaque adversaire », menaces de combo et gestion des removals ciblés, puis tutorat/conditions de victoire.
7. Ajouter des **tests d'états ciblés** au lieu de tout déduire d'une poignée de parties aléatoires. Ces tests doivent rester compatibles avec les règles réelles de Forge.

### Priorité 3 — nouvelle série statistique uniquement APRÈS corrections
- Baseline `Forge 2.0.15 + correctif Charm` **identique dans les deux bras expérimentaux**, pour isoler les différences IA.
- Un seul delta IA à la fois, deck Brimaz toujours à 100 cartes, les mêmes six decks adverses ; les mutations des listes sont une **expérience séparée**.
- Rotations de siège et graines prédéclarées avant de lire les résultats ; au moins des dizaines de parties complètes par politique, davantage si le taux de victoire est faible.
- Distinguer panels du playgroup et panel Bracket 3 **vraiment comparable** (Game Changers, vitesse de victoire, interaction, synergies).
- Mesurer winrate ± intervalle de confiance, censures, exceptions, tour de la partie, cast du commandant, trigger prolif, ressources, damages/drains, tours sans progrès ; comparer les éléments tactiques à une baseline.
- Rejouer également des **parties humaines de référence** si l'utilisateur peut fournir des séquences/logs d'actions ; le but est de se rapprocher d'un humain compétent, pas d'obtenir une victoire artificielle par réglage d'adversaires plus faibles.

## N. Références documentaires dans le dépôt

Documents de référence :
- [docs/realism-protocol.md](../docs/realism-protocol.md) — validation des decks et des victoires.
- [docs/canonical-postmortem-and-first-win.md](../docs/canonical-postmortem-and-first-win.md) — **diagnostic le plus actuel**, erreur Charm et première victoire.
- [docs/ai-quality-and-parallelism.md](../docs/ai-quality-and-parallelism.md) — parallélisation, symptômes comportementaux.
- [docs/brimaz-turn-policy.md](../docs/brimaz-turn-policy.md) — politique V1.
- [docs/brimaz-turn-policy-v2.md](../docs/brimaz-turn-policy-v2.md) — politique V2.
- [docs/brimaz-turn-policy-v3.md](../docs/brimaz-turn-policy-v3.md) — scoring V3 et audit des actions.
- [docs/multiplayer-lookahead-roadmap.md](../docs/multiplayer-lookahead-roadmap.md) — architecture 4-IA à véritable recherche future.

Workflows et actions :
- `.github/workflows/forge-smoke.yml`
- `.github/workflows/playgroup-import.yml`
- `.github/workflows/parallel-benchmark.yml`
- `.github/workflows/canonical-benchmark.yml`
- `.github/workflows/canonical-postmortem.yml`
- `.github/workflows/commander-legality.yml`
- `.github/workflows/forge-all-cards-check.yml`
- `.github/workflows/realism-certification.yml`
- `.github/workflows/charm-npe-regression.yml`
- `.github/workflows/charm-longgame-regression.yml`
- `.github/workflows/verify-brimaz-first-win.yml`
- `.github/workflows/brimaz-v5-pilot.yml` et `brimaz-v5-postmortem.yml`
- `.github/workflows/brimaz-v6-pilot.yml` et `brimaz-v6-audit.yml`
- `.github/workflows/edh-four-player-hybrid.yml`.

## O. Points à ne jamais affirmer sans nouvelles preuves

- « Brimaz est mauvais » : **non** ; 0/29 était une expérience avec pilotage IA limité et un panel parfois plus fort.
- « Les IA jouent comme des humains compétents » : **non** ; Forte limitation Forge des combos, arbitrages de cibles, tactiques de sacrifice et multijoueur.
- « Le moteur avancé 4 joueurs simule déjà trois adversaires futurs correctement » : **non** ; le patch de contrôleurs sur la pile n'est qu'une étape.
- « Chaque `success` GitHub est une victoire valable » : **non** ; CI, simulation terminée, validation Scryfall, et règles Oracle sont des niveaux différents.
- « V6 a augmenté le winrate » : **non**, échantillon de quatre parties, aucune victoire ; quelques engines lancés, c'est tout.
- « La première victoire résout le 0/29 » : **non**, elle est un résultat séparé sur une graine choisie, après correction d'un bug et très proche du cutoff.
- « Il faut simplement augmenter `-c` jusqu'à obtenir une victoire » : **non** ; les parties longues avec peu de progrès doivent faire l'objet d'un diagnostic comportemental.
- « Toutes les listes KaalDeagle sont Bracket 3 » : **non** ; seules Radha et Tazri ont ce label explicite dans les métadonnées collectées ; Lathril et Amalia ont des Game Changers.
- « Les anciens tests comptaient 100 vraies cartes chez chaque adversaire » : **non**, les exports de noms recto-verso ont été corrigés plus tard et les anciennes séries sont surtout des tests d'ingénierie.

## P. Consigne immédiate à la prochaine IA qui reprend le dossier

1. **Lire ce rapport et les documents `docs/canonical-postmortem-and-first-win.md` + `docs/realism-protocol.md` ; contrôler les derniers workflows GitHub.**
2. Conserver Brimaz V3 et les sept decks canoniques strictement identiques, sauf changement de deck **explicitement demandé**. Ne pas optimiser les cartes sur des simulations dont l'IA est encore déficiente.
3. Partir de **Forge 2.0.15 + correctif isolé Charm** comme nouveau socle expérimental ; vérifier les hashes, la reproduction et la documentation des changements du moteur.
4. Reproduire et auditer la **première victoire** avec limite 600–900 s pour écarter une ambiguïté liée à sa proximité de la limite.
5. Approfondir et résoudre l'IA qui **ignore des cartes importantes** (9 `AI:RemoveDeck:All`) avant d'accumuler des centaines de nouvelles parties. Exploiter les pilotes V5/V6 et les logs pour démontrer que chaque capacité est réellement jouée au bon moment et selon les règles.
6. Ne lancer une grosse série parallèle qu'une fois les régressions, scénarios ciblés et règles valides ; fournir toujours un rapport de **parties complètes/censurées/rejetées**, des logs et un bilan critique, sans surestimation.
7. L'utilisateur est très technique et cherche de la **rigueur et des preuves**, pas des scénarios imaginaires. Il tient à ce que ses victoires humaines avec ce deck soient prises au sérieux comme indicateur que l'IA est actuellement insuffisante.

**Résumé en une phrase :** nous avons un véritable laboratoire Forge 4 IA parallélisé et audité, sept decks légaux/canoniques, une première victoire naturelle de Brimaz après la correction d'un bug moteur, mais il reste à transformer une IA Forge souvent trop passive face aux moteurs de sacrifice, tutorat/récursion et combats multijoueurs en adversaire/pilote suffisamment réaliste pour mesurer enfin la vraie force du deck.
