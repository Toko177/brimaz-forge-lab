# Simulateur Commander Forge à quatre IA — utilisation locale

**Branche expérimentale V24 :** `feature/v24-combat-trigger-fast-negatives-20261011`.
Exécute **de véritables** JVM Forge 2.0.15 indépendantes,
chacune avec quatre joueurs IA, mêmes cartes canoniques et profils IA
uniformes. Ce n'est pas une simulation simplifiée de probabilités.

La version locale a été ajoutée pour contourner le blocage actuel
des runners GitHub Actions ; le premier lancement Windows/Linux
complet **n'a pas encore été certifié**.

## Pré-requis

- Python 3.10+ et **Java 21**, `java`/`javac`/`jar` disponibles
  dans le `PATH`.
- Clone du dépôt sur **la branche V24** (pas le vieux `main`).
- Archive officielle `forge-installer-2.0.15.tar.bz2` puis extraction
  du fichier `forge-gui-desktop-*-jar-with-dependencies.jar`. Ne pas
  fournir directement l'archive au paramètre `--jar`.
- Depuis l'artefact GitHub Actions **forge-seven-decks-canonical-verified**
  de https://github.com/Toko177/brimaz-forge-lab/actions/runs/37966009166,
  copier les sept fichiers `.dck` normalisés dans `forge_decks/`.
- Copier le rapport de normalisation de ce même artefact dans
  `canonical/results/forge_normalization/report.json`.
  Le lanceur **vérifie les sept empreintes SHA256** et refuse une
  liste manquante ou modifiée, notamment celles des trois adversaires.

## Installation automatisée sur Windows (PowerShell)

La branche V24 contient maintenant **`scripts/setup_and_run_four_ai.ps1`**,
un lanceur de préparation qui vérifie automatiquement l'archive Forge
2.0.15 (SHA256 officiel épinglé), retrouve ou extrait le vrai JAR
desktop, télécharge les **sept decks canoniques de ton dépôt privé**
avec `gh run download`, refuse de remplacer une liste de deck
différente, vérifie Java 21 et transmet les options au vrai moteur.

Depuis un clone V24 avec `gh auth login` déjà effectué :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -PreflightOnly
```

Puis pour **huit vraies parties** (deux pods, quatre rotations, une
partie chacune, deux JVM simultanées) :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Pod both -Policy v17_strict -GamesPerRotation 1 -Parallel 2 -Clock 420
```

On peut utiliser une archive téléchargée antérieurement sans
la retélécharger avec `-ForgeArchive "C:\\Forge\\forge-installer-2.0.15.tar.bz2" -SkipForgeDownload`.
Le programme n'exige pas que la politique V24 soit activée :
`v17_strict` est le point de départ le plus prudent.

Ce script lui-même n'a **pas encore été exécuté sur un PC Windows**.
Il automatise les prérequis ; il ne garantit ni débit, ni parties
naturellement terminées, ni compétence stratégique humaine.

## Profilage CPU Java 21 avec JFR

Pour savoir quelles **méthodes Java réellement exécutées** prennent
du temps, plutôt que d'accuser le dernier candidat observé pendant
un timeout, lancer une campagne avec `-Jfr` dans le script PowerShell
ou `--jfr` dans le lanceur Python.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Pod aristo -Policy v17_strict -GamesPerRotation 1 -Parallel 2 -Clock 420 -Jfr
```

Chaque véritable JVM enregistre un fichier `.jfr` plafonné à
**128 Mio** par partie, archivé avec ses vrais logs et sa graine.
Le lanceur crée également sous `jfr_summaries/` des vues Java 21 :

- `hot_methods` : les méthodes les plus présentes dans
  les échantillons d'exécution ;
- `cpu_load` : utilisation CPU par thread ;
- `summary` : quantité des événements enregistrés.

On pourra ainsi inspecter objectivement `ComputerUtilCombat`,
`AiBlockController`, les capacités statiques et la gestion des
remplacements, et prioriser les vrais points chauds.

**JFR peut modifier les chronométrages.** Le comparateur de
campagnes désactive explicitement les ratios de vitesse lorsque
JFR est actif ; ces parties servent au diagnostic, pas à proclamer
un gain de performance.

## Pré-validation, sans lancer une partie

Depuis la racine du clone :

```powershell
python scripts/run_local_four_ai.py --jar "C:\Forge\forge-gui-desktop-2.0.15-jar-with-dependencies.jar" --preflight-only
```

Le chemin est à adapter au nom et à l'emplacement réel du JAR.
Cette commande vérifie Java 21, les sept decks, la présence du JAR,
le profil/pod demandés et le nombre de véritables parties prévues.
Elle **ne** télécharge pas de sources, ne patche pas le JAR et ne
lance aucune partie.

## Tournoi réel

```powershell
python scripts/run_local_four_ai.py --jar "C:\Forge\forge-gui-desktop-2.0.15-jar-with-dependencies.jar" --pod both --policy v17_strict --profile Default --games-per-rotation 2 --parallel 4 --clock 420 --seed-base 20261027
```

Ceci lance **16 parties réelles**, deux groupes de quatre joueurs
sur les quatre rotations, deux matchs par matrice. Les quatre IA
reçoivent **le même profil**. Les quatre travailleurs peuvent consommer
jusqu'à environ **16 Gio de mémoire JVM** (4 Gio max chacun), en plus
du système et du cache. Réduire à `--parallel 2` si nécessaire.

Politiques proposées :
- `v17_strict` : référence recommandée, pas de nouvelle heuristique
  lente de V23/V24 ;
- `v19_removal`, `v20_shadow` : ciblage et contre-factuel V19/V20
  **sans gain de décision démontré** ;
- `critical_counter` : tentative optionnelle de protection du
  commandant et de la vie contre certains sorts publics ciblés ;
- `v23_cooldown` : exclusion temporaire d'un candidat après timeout,
  **n'a pas réduit les timeouts dans le pilote** ;
- `v24_trigger_prune` : filtrage expérimental des calculs d'IA
  prouvablement impossibles dans l'estimation des déclenchements de
  combat, **sans modification des véritables règles ou triggers Magic**.
  Aucun gain de vitesse ne doit être présumé avant test.

Pour `v24_trigger_prune`, remplacer simplement
`--policy v17_strict` par `--policy v24_trigger_prune`, conserver
le même `--seed-base` et les mêmes rotations et analyser
**les deux campagnes complètes**. Une même graine ne garantit
pas un déroulement identique ; les proportions de victoire ne doivent
pas être comparées comme des observations indépendantes.

## Comparer deux politiques sur de VRAIES parties appariées

Pour tester deux stratégies sans mélanger profils, decks ou graines,
effectuer **deux campagnes réelles** avec les mêmes paramètres, en
changeant uniquement `--policy`. Exemple :

```powershell
python scripts/run_local_four_ai.py --jar "C:\\Forge\\forge-gui-desktop-2.0.15-jar-with-dependencies.jar" --pod both --policy v17_strict --profile Default --games-per-rotation 2 --parallel 2 --clock 420 --seed-base 20261027
python scripts/run_local_four_ai.py --jar "C:\\Forge\\forge-gui-desktop-2.0.15-jar-with-dependencies.jar" --pod both --policy v24_trigger_prune --profile Default --games-per-rotation 2 --parallel 2 --clock 420 --seed-base 20261027
python scripts/compare_local_four_ai_campaigns.py --reference "results/local_campaigns/CAMPAGNE_REFERENCE" --experiment "results/local_campaigns/CAMPAGNE_V24" --output "results/v24_paired.json"
```

Remplacer `CAMPAGNE_REFERENCE` et `CAMPAGNE_V24` par les vrais
répertoires horodatés, produits lors de chaque exécution. Le comparateur
**refuse les campagnes incomplètes**, les decks dont les SHA diffèrent,
les parties manquantes, les profils asymétriques, les graines, rotations
ou durées de partie différentes. Il conserve séparément les fins
naturelles, les censures et les erreurs. Un ratio de vitesse n'est
présenté que pour deux parties naturellement terminées avec les mêmes
événements observables. Cela ne prouve pas une victoire causale.

### Certification optionnelle des vraies victoires

Si le rapport de légalité Scryfall a déjà été produit depuis les **sept
decks exacts** par `scripts/validate_commander_legality.py`, ajouter :

```powershell
--scryfall-legality-report "results/legality/report.json"
```

à la commande de lancement de tournoi. Le programme appelle alors
`scripts/certify_commander_games.py` pour recouper chaque résultat
avec les listes Commander légales, la déclaration de match à quatre IA,
le gagnant dans le journal Forge, le dépassement de l'horloge, les
exceptions et les issues naturelles. Toute victoire que Forge indique
comme naturelle **mais que le certificateur rejette** bloque la validation
de la campagne. Les censures sont archivées sans victoire fabriquée.
Ce contrôle reste un certificat documentaire, pas une preuve formelle
de conformité de chaque interaction à l'Oracle Magic.

### Corrigé : JAR modifié et ressources Forge

Le JAR compilé est stocké dans la campagne pour que sa SHA256 reste
unique ; **le processus Java est désormais lancé depuis le répertoire
de l'installation Forge d'origine** grâce à `--runtime-dir` dans
`batch.py`. Cela permet de conserver la résolution des ressources
de Forge sans modifier ou écraser l'installation source. Lancer toutes
les JVM depuis un simple répertoire temporaire sans ses ressources
aurait pu empêcher le démarrage du moteur.

## Sécurité et sorties

Le programme fait une **copie** du JAR original avant de le patcher.
Les scripts de patching Java téléchargent **les sources officielles
épinglées au tag Forge 2.0.15** : une connexion à GitHub est donc
nécessaire lors de la compilation initiale.

Tout est conservé dans
`results/local_campaigns/<horodatage>-<identifiant>/` :
- `forge-2.0.15-4AI-patched.jar` ;
- `provenance.json` : SHA256 du JAR original/modifié, sept SHA des decks,
  branche et commit Git, options Java, profils, politiques, graines ;
- `games/` : manifeste réel et journaux de chaque JVM, y compris
  erreurs et censures ;
- `summary/tournament.md` et `tournament.json` : résultats naturels
  par pod, censoring, incertitude descriptive de Wilson ;
- `forensics/` : timeline des sorts, attaques, dégâts, décisions
  par IA et activations d'Incubateurs ;
- `timeouts/` : classement des piles Java des véritables timeouts
  dans l'évaluation du combat, les capacités statiques ou remplacement.

La collecte n'invente pas de gagnant pour une partie censurée. Une fin
naturelle affichée par Forge n'est **pas** une validation Oracle
indépendante. L'option `--preflight-only` et les tests de garde-fous
sont implémentés, mais la première exécution complète sur Windows
reste à valider.

## Pourquoi ce lanceur est utile

Des jobs GitHub Actions V24 ont échoué **avant d'obtenir un runner et
sans exécuter de commandes** ; le diagnostic matériel ou de quota n'a
pas pu être confirmé. La version locale évite de dépendre des quotas
de runners et permet d'exploiter le matériel disponible sans toucher
aux listes de cartes ni affirmer des victoires inexistantes.

Pour les prochains chats :
- [Passation V24](PASSATION_ACTIVE_V24_2026-10-11.md)
- [Point de reprise permanent sur main](../NEXT_CHAT_START_HERE.md)
- [PR #17](https://github.com/Toko177/brimaz-forge-lab/pull/17)
