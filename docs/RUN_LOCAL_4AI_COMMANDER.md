# Utiliser localement le simulateur Forge Commander à quatre IA

Socle : `main`. Recherche V35 opt-in : `feature/v35-strategic-search-20261011`.
Le moteur utilise **Forge 2.0.15 Java 21**, les sept decks canoniques
versionnés et vérifiés SHA256, et de vrais processus indépendants.

## Préparer et vérifier sous Windows

Prérequis : Python 3.10+, JDK21 (`java`, `javac`, `jar`) et `tar`.
Les sept decks originaux sont déjà dans `forge_decks/` sur `main` ; `gh`
n'est nécessaire que si l'on utilise une ancienne version sans decks.
Télécharger le moteur via le script ou indiquer une archive existante
avec `-ForgeArchive`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v33_strategy -Pod both -GamesPerRotation 1 -Parallel 2 -Clock 420 -PreflightOnly
```

Puis la même commande sans `-PreflightOnly` pour une comparaison réelle
sur les quatre rotations et deux pods, **16 JVM Forge au total**.
Une JVM demande jusqu'à environ 4 Gio de mémoire ; limiter `-Parallel`
selon les ressources.

Pour compiler seulement les patchs conservés :
```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -CompileOnly
```

## Linux / CI

Après installation du JAR original, utiliser :

```bash
python3 scripts/run_paired_four_ai.py \
  --jar /chemin/forge-gui-desktop-2.0.15-jar-with-dependencies.jar \
  --pod both --reference-policy v17_strict \
  --experiment-policy v33_strategy --profile Default \
  --games-per-rotation 1 --parallel 2 --clock 420 \
  --seed-base 20261221
```

Le lanceur copie le moteur avant modification et conserve les manifests,
les logs bruts, les SHA256, les rotations et les statuts de parties.
La même graine Forge n'assure pas une trace déterministe.

## Méthodologie de preuve

- `complete` signifie fin naturelle déclarée par Forge, pas certification
  indépendante des règles de toutes les cartes.
- La certification de victoire passe par
  `scripts/certify_commander_games.py`, avec les listes et rapport de
  légalité Scryfall exacts.
- `scripts/compare_local_four_ai_campaigns.py` compare les jeux réellement
  enregistrés et refuse les campagnes incomplètes ; des parties censurées ne
  sont pas converties en défaites.
- `scripts/audit_v33_real_strategy.py` distingue propositions V33,
  approbations Forge et véritables résultats. Son succès exige une
  intervention observée si `--require-intervention` est utilisé.
- Les rapports de vitesse excluent JFR et vérification shadow des règles.

**État empirique :** le [pilote V33 sur 16 JVM](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38128781081)
a produit 16 fins naturelles. Son premier résultat « zéro choix V33 »
était fondé sur des expressions régulières erronées : le parseur corrigé
sur V34 doit être réappliqué aux traces archivées avant interprétation.
Ne pas parler de gain stratégique démontré.

Documentation de l'IA :
[Planificateur V33](V33_MULTIPLAYER_STRATEGIC_PLANNER.md).

## Tester la V35 contre la référence Forge

Sur la branche V35 (après compilation réelle du patch Java21), le test
comparatif à **quatre sièges et deux pods** est :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v35_strategy -Pod both -GamesPerRotation 1 -Parallel 2 -Clock 420
```

La porte de mesure de cette évolution est
`scripts/audit_v35_real_search.py` : utiliser le
`comparison.json` produit par les vrais processus Forge, pas des sorties
inventées. Il compte les propositions, les refus et les décisions
acceptées par le **véritable** contrôle de jouabilité de Forge ; aucune
approbation n'est par elle-même preuve de résolution ou de victoire.

## Mesures tactiques V35

L'auditeur `scripts/audit_v35_real_search.py` sépare désormais les
interventions de développement `FOUR_AI_V35_STOCK_APPROVED` des
interventions de retrait/nettoyage/réanimation
`FOUR_AI_V35_TACTICAL_STOCK_APPROVED`. Ni l'une ni l'autre n'est
une preuve de lancement ou de résolution effective du sort.
Les propositions refusées par les critères originaux de Forge
sont journalisées et ne sont pas comptées comme des actions.
