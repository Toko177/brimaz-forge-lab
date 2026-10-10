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
