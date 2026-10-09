# Reprise experimentale - qualite des preuves et diagnostic V7

Date: 2026-10-09 (Europe/Paris). Baseline inchangee : sept decks canoniques,
Forge 2.0.15, Brimaz V3 a 100 cartes sans Game Changers, deux pods a quatre
sieges. Aucun cout de Magic ou effet de carte ne doit etre court-circuite.

## 1. Observation V6 sur quatre parties

Le nouveau workflow commander-evidence-and-ai-audit.yml a relu les parties
reelles du run GitHub 37969934893. Certification de controle :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37992163452

- 4/4 parties certifiees, aucune victoire Brimaz, echantillon insuffisant ;
- 7 sorts Brimaz lances, 11 transformations d'Incubateurs ;
- 7 declenchements de Brimaz en etape de fin, sur 16 declenchements totaux ;
- Krark-Clan Ironworks lance trois fois, Orzhov Signet une fois ;
- une activation d'Arcbound Ravager visible sur la pile, pendant un tour
  adverse avant l'etape de fin ;
- aucune proposition BRIMAZ_PLANNER observee dans ces quatre parties.

Attention : Krark-Clan Ironworks possede une capacite de mana. Les capacites
de mana NE vont PAS sur la pile. L'absence de ligne Add To Stack n'indique pas
une absence d'utilisation de cette capacite. Absence d'action visible ne
signifie pas opportunite legale, payable et profitable ratee.

## 2. Preuve de validite des parties

- scripts/batch.py enregistre clock_seconds pour chaque partie ;
- scripts/forge_result_evidence.py controle exactement quatre issues par
  joueur, une victoire et trois defaites, les noms de joueurs, les sieges,
  le gagnant et la limite de temps effective ;
- scripts/certify_commander_games.py integre ces controles en plus du
  certificat de legalite Scryfall et de la detection d'exceptions ;
- tests/test_forge_evidence.py contient douze tests de regression ;
- les historiques sans clock_seconds sont analyses selon la limite
  historique de 360 secondes, pas comme des parties a duree inconnue.

Une preuve de sortie naturelle de Forge n'est pas une preuve formelle
qu'absolument toutes les interactions Oracle sont parfaites.

## 3. Experiences

### Rejouer la premiere victoire sans limite proche

Workflow : .github/workflows/brimaz-first-win-long-clock.yml.
La graine 20291010 est reexecutee en Brimaz siege 2 avec la politique
Forge stock et le seul correctif Charm, meme jeu canonique, limite 900 secondes.
C'est une regression ciblee, PAS un nouvel echantillon independant.

### Pilote V7 d'instrumentation

Workflow : .github/workflows/brimaz-v7-window-audit.yml.
Le comportement strategique de V6 n'est pas modifie.
scripts/patch_forge_brimaz_v7.py ajoute BRIMAZ_WINDOW pour compter les
fenetres de seconde phase principale ou l'IA a reellement ete consultee :
- commandant sur le champ de bataille ;
- morts Phyrexian deja vues par le moteur ce tour ;
- jetons Phyrexian candidats sans garantie de legalite du sacrifice ;
- permanents de sacrifice et capacites presentes dans la liste de l'IA.

scripts/audit_brimaz_windows.py fournit les totaux bruts, sans confondre
candidat et opportunite legale. Les capacites de mana font l'objet d'une
reserve specifique.

## 4. Suite

1. Qualifier les fenetres MAIN2 reellement observees avec commandant present,
   aucune mort Phyrexian encore enregistree et jetons disponibles.
2. Expliquer pourquoi les capacites sont ou non proposees a l'IA. Tester
   les couts et capacites de mana separement des actions sur la pile.
3. Developper des tests deterministes de sacrifice positif et negatif,
   de defense et de timing avant de changer la politique V8.
4. Conserver une baseline stock, un panel stable et des graines preenregistrees.
   Toujours reporter les defaites, censures et erreurs moteur.
5. Ne pas modifier la liste Brimaz V3 sur la base de cette IA encore imparfaite.

Ne revendiquer aucune amelioration de winrate sans comparaison controlee
et sans certification des vraies parties.


## Addendum 9 octobre : audit de reproductibilite et pilote V8

### Partie Brimaz historique
Graine 20291010, pod aristo, Brimaz siege 2, Forge stock + Charm corrige :
- horloge 360 s : Brimaz gagne au moteur a 356476 ms ;
- horloge 900 s : Radha gagne a 437493 ms ;
- premiere divergence de trace au tour Forge 33, choix de Dungeon of the
  Mad Mage (premiere partie) vs Tomb of Annihilation (seconde) ;
- exceptions java.util.concurrent.TimeoutException dans la voie
  AiController.chooseSpellAbilityToPlayFromList : 2 et 6 respectivement.

Le moteur source utilise MyRandom.setRandom(new Random(seed)) pour l'option
CLI -s, mais la meme graine n'a PAS suffi a reproduire cette partie. Les
exceptions de deadline IA et les choix de donjon ne permettent pas, a ce
stade, de designer la cause exacte. Ne pas ajouter cette victoire historique
au numerateur d'un winrate mesure apres correction. Etablir d'abord une
reproductibilite adaptee et documenter la censure.

Preuve et tests forensiques :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37994894861

### V8 / defence des Incubateurs
V8 intervient uniquement en deuxieme phase principale du joueur actif
pour transformer un Incubateur ayant >=2 marqueurs si le joueur dispose de
peu de bloqueurs et fait face a une menace. La vraie action est toujours
verifiee par les mecanismes de timing et de paiement de Forge. V8 n'accorde
pas de capacites gratuites et n'annule pas l'invocation du commander.

Huit tests Java dans le JAR Forge modifie : reussis. Quatre parties :
toutes certifiees, Brimaz 0/4. **Aucun message BRIMAZ_DEFENSE de choix
prioritaire n'est apparu dans ces quatre matchs.** On ne peut donc pas
affirmer que le nouveau comportement a ete exerce dans les parties.
Les differents nombres de triggers Brimaz ne suffisent pas a prouver un
gain. Prochaine priorite : des tests avec des etats Forge precis qui rendent
une transformation defensivement utile et payable ; ne pas forcer des
activations arbitraires pour produire des nombres.

Run :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995083458

### Nouveau diagnostic du temps de reflexion
Dans Forge 2.0.15, Game.AI_TIMEOUT vaut 5 secondes.
AiController.chooseSpellAbilityToPlayFromList attend le resultat de son
FutureTask a l'aide de game.getAITimeout(); le depassement annule la recherche.
La version experimentale patch_forge_ai_budget.py releve le budget a 10 s
pour les quatre joueurs, sans toucher aux regles Magic ou aux decks.
Le protocole compare 5 s vs 10 s sur memes graines et memes sieges et mesure
temps total, timeout IA et issue naturelle. Un gain de competence n'est
pas encore demontre, et la depense de CPU doit etre quantifiee.

Pilote :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995525927

### Etude avec horloge identique
Deux JVM differents, memes quatre decks canoniques, seed 20291010,
clock 600 s et IA stock+Charm. Le workflow compare les transcripts et
les issues, sans exiger une victoire de Brimaz :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/37995223230
