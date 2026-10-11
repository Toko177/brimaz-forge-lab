# V33 — Planificateur stratégique à quatre IA (changement d'architecture)

**11 octobre 2026 — PR #26**, branche
`feature/v33-multiplayer-strategic-planner-20261011`, basée sur V32.
Il s'agit d'un pilote **qui modifie réellement les choix des IA lorsque
l'action est validée par Forge**, et non d'une déclaration de performance
ou de comportement de niveau humain.

## Pourquoi V14–V32 n'ont pas livré une IA tactiquement réaliste

Les anciennes versions ont beaucoup investi dans la robustesse,
les corrections de règles, la parallélisation, les timeouts,
le profilage JFR et les comparaisons de sorties. Les correctifs ont
amélioré notre capacité **à jouer et mesurer**, pas systématiquement
la capacité **à choisir** des actions gagnantes. De plus, Forge a été
conçu largement autour de heuristiques de duel ; quatre adversaires,
effets simultanés, états cachés, contre-interactions et Commander
rendent un rollout complet très coûteux.

## Changement d'architecture concret

### 1. `MultiplayerStrategicModel.java` : état abstrait + deux tours

Entrées immuables : mana disponible estimé, terrains, points de vie,
pression cumulée des deux adversaires les plus menaçants, créatures,
artefacts, jetons, pièces de synergie, nombre de cartes de la propre
main. Candidats : permanents **actuellement proposés par Forge**.

Le modèle donne à chaque action un score immédiat et un meilleur
enchaînement hypothétique au tour suivant, à coût de mana simplifié.
Il adapte le poids du futur lorsque la survie est compromise :
priorités différentes pour rampe, commandants, moteurs de jetons,
sacrifice, pioche, protection, créatures et moteurs génériques.
Le second tour est une **abstraction de tempo** : il ne prétend pas
résoudre de vrais triggers ou inventer les futurs piochages.

### 2. `MultiplayerStrategicSequencer.java` : lien avec le vrai moteur

Le module s'active pour **les quatre sièges**, mais uniquement pendant
le tour actif, MAIN1 ou MAIN2, pile vide. Il regarde les permanents
non ciblés connus de leur contrôleur (main et zone commandant),
sans consulter les mains, bibliothèques ni secrets des adversaires.
Chaque premier choix est présenté seulement après la validation réelle
des coûts, timing et jouabilité par Forge.

### 3. Approbation du moteur original

Le point d'intégration central `AiController` fait un deuxième
contrôle via **`canPlayAndPayFor` original de Forge**. Si le moteur
stock refuse le sort, aucune action n'est imposée et Forge continue
normalement son parcours (y compris le pilote Brimaz existant).

Deux journaux distincts :
- `FOUR_AI_V33_STRATEGIC_PROPOSAL` : candidat identifié, **pas un sort joué**.
- `FOUR_AI_V33_STRATEGIC_ACTION` : proposition acceptée par la
  logique `AiPlayDecision.WillPlay` de Forge. Elle n'est toujours
  pas une preuve du résultat de la résolution sur la pile.

Le V33 est OFF pour toutes les autres politiques et ON seulement
pour `v33_strategy`. Les règles, coûts, phases et résolution ne
sont jamais modifiés par ce module.

## Tests

- `tests/java/forge/ai/MultiplayerStrategicModelChecks.java` :
  rampe contre créature, besoin de défense combinant deux adversaires,
  priorité d'un outlet avec/sans jetons, commandant futur,
  refus des actions non jouables, déterminisme.
- `.github/workflows/v33-strategic-compile.yml` :
  compilation Java21 avec vrai JAR Forge 2.0.15, correctifs intégrés,
  tests de comportement du modèle. **Ce n'est pas un test réel de victoire**.
- `.github/workflows/v33-real-strategy-ab.yml` :
  deux groupes d'adversaires × quatre rotations × deux politiques
  (`v17_strict` et `v33_strategy`) = **16 vrais matchs JVM à quatre IA**,
  chacun avec SHA256 des sept decks d'origine et ses logs bruts.
- `scripts/audit_v33_real_strategy.py` : sépare les propositions,
  les choix approuvés par Forge, la modification des événements,
  les parties finies naturellement et les censures. Un run sans
  décision approuvée ne prouve aucune amélioration et échoue le gate.

Ces tests doivent être **inspectés dans leurs vrais artifacts** :
un workflow vert ne prouve ni un niveau humain ni un meilleur winrate.

## Lancement

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v33_strategy -Pod both -GamesPerRotation 1 -Parallel 2 -Clock 420
```

Ou directement sous Linux :

```bash
python3 scripts/run_paired_four_ai.py \
  --jar /chemin/forge-gui-desktop-2.0.15-jar-with-dependencies.jar \
  --reference-policy v17_strict --experiment-policy v33_strategy \
  --pod both --games-per-rotation 1 --parallel 2 --clock 420
```

## Définition d'une V33 crédible

1. Les 16 JVM sont de vrais Forge Commander à quatre sièges ;
   résultats bruts et 7 SHA256 intacts.
2. Au moins une proposition est effectivement **approuvée par Forge**
   pour ne pas annoncer une option qui ne s'exécute jamais.
3. Vérifier par siège et par pod où se produisent les changements,
   puis contrôler erreurs, lenteurs, censures et véritables sorts joués.
4. Les décisions sur des états tactiques fabriqués pour les tests
   ne sont pas une validation par des joueurs compétents.
5. Pour prétendre à une **amélioration considérable** : davantage de
   positions expert-annotées à états Forge exacts, rollouts contrôlés,
   mesure de perte de ressource/réponse et un échantillon robuste
   indépendant de parties — et non une hausse observée sur huit matchs.

**Limites critiques restantes :** menace basée sur puissance visible,
pas une prédiction fiable des attaques/blocages ; choix non ciblés
uniquement ; biais des classifications (certains moteurs sont reconnus
par leur nom exact) ; deuxième tour abstrait non garanti ; Forge stock
peut toujours prendre de mauvaises décisions hors des choix couverts.
En l'état, V33 est une architecture stratégique testable, pas encore
une IA Commander humaine.
