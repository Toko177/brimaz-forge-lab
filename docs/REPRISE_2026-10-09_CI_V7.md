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
