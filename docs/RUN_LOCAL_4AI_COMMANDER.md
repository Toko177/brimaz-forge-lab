# Utiliser localement le simulateur Forge Commander à quatre IA

Branche : `feature/v34-repository-cleanup-20261011`.
Le moteur utilise **Forge 2.0.15 Java 21**, les sept decks canoniques
versionnés et vérifiés SHA256, et de vrais processus indépendants.

## Préparer et vérifier sous Windows

Prérequis : Python 3.10+, JDK21 (`java`, `javac`, `jar`),
`gh` connecté au dépôt et `tar`. Télécharger le moteur via le script
ou indiquer une archive existante avec `-ForgeArchive`.

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
