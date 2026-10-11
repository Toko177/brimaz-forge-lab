# V31 — PASSATION ACTIVE : pilote Commander réel, appariement et preuve d'utilisation

**11 octobre 2026.** Code de cette étape :
`feature/v31-reproducible-4ai-operator-20261011`, parent
`feature/v30-exact-card-property-fastpath-20261011`.
La branche `main` contient encore essentiellement l'ancien moteur ; ne pas
assimiler la numérotation V31 à une release fonctionnelle certifiée.

## Ce qui est réellement prouvé avant V31

Les résultats ci-dessous sont tirés des journaux GitHub Actions, pas de tests
synthétiques ou de promesses de l'ancienne conversation.

| Source réelle | Observation |
|---|---|
| [V25 — run 38094639616](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38094639616) | 16 JVM Forge Commander à quatre IA ; 14 fins naturelles / 2 censures ; 6 paires A/B naturelles à actions suivies identiques ; ratio médian de vitesse **0,9959**, aucune accélération établie |
| [V30 — run 38096353743](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38096353743) — pod artifact | trois JVM, 3 fins naturelles ; 2 251 123 comparaisons même état méthode d'origine sans divergence ; ratio descriptif 1,0427 sur une seule paire |
| Même run V30 — pod aristo | trois JVM, 3 censures à 420 s, **aucun vainqueur** ; 14 628 554 comparaisons même état sans divergence |
| [V26 JFR](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38094816646) | 46,18 % des échantillons de méthodes observés concernaient `CardProperty.cardHasProperty`, une seule partie, pas une mesure CPU exclusive |

Sur la V30 : 16 879 677 comparaisons Oracle mêmes états, zéro divergence
observée ; cela ne signifie PAS vérification exhaustive des règles de Magic.
Les comportements des IA ne sont pas certifiés comparables à des joueurs experts.

## Ce que livre la V31

- `scripts/run_local_four_ai.py` accepte deux modes supplémentaires,
  `v30_exact_rules` (raccourcis opt-in) et `v30_shadow_verify`
  (vérification des valeurs de la fonction originale aux mêmes états,
  diagnostic très coûteux, **jamais pour mesurer la vitesse**).
  La référence `v17_strict` conserve les règles non optimisées.
- `scripts/run_paired_four_ai.py` exécute une expérience A/B complète :
  mêmes sept decks canoniques SHA256, même moteur source Forge,
  mêmes graines et quatre rotations, deux politiques clairement séparées.
  Chaque partie tourne sur sa vraie JVM Forge ; **aucune simulation proxy**.
  Les sorties complètes (provenance, artefacts, traces et rapports) sont
  conservées dans `results/local_pairs/`.
- `scripts/compare_local_four_ai_campaigns.py` refuse les comparaisons
  incomplètes ou asymétriques et ne publie de rapport de vitesse que pour
  des jeux **tous deux naturels avec mêmes événements observés**, hors JFR
  et vérification Oracle shadow.
- `scripts/setup_and_run_four_ai.ps1` ajoute `-Paired` avec
  `-ReferencePolicy`, en préparant automatiquement Forge et les decks ;
  la vérification SHA256 de l'archive officielle demeure obligatoire.
- Tests unitaires synthétiques explicites sur Python 3.10 et 3.12 ;
  ces tests **ne sont pas des parties Magic**.
- `.github/workflows/v31-real-paired-forge.yml` lance l'épreuve matérielle
  8 JVM réelles sur le pod artifact, 4 rotations × 2 politiques,
  puis publie les fichiers de preuve. Le workflow n'est **pas présumé validé**
  avant inspection de ses exécutions.

## Commandes

Sous Windows, après `gh auth login`, JDK21 et Python :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v30_exact_rules -Pod artifact -GamesPerRotation 1 -Parallel 2 -Clock 420 -PreflightOnly
```

Pour lancer **huit vraies parties** et comparer les quatre positions :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_and_run_four_ai.ps1 -Paired -ReferencePolicy v17_strict -Policy v30_exact_rules -Pod artifact -GamesPerRotation 1 -Parallel 2 -Clock 420
```

Pour couvrir les deux pods : ajouter `-Pod both` = 16 vraies JVM.
Sans `-Paired`, une seule politique reste accessible via `-Policy`.

Sous Linux ou en CI, après récupération du JAR et du rapport canoniques :

```bash
python3 scripts/run_paired_four_ai.py \
  --jar /chemin/forge-gui-desktop-2.0.15-jar-with-dependencies.jar \
  --pod artifact --reference-policy v17_strict \
  --experiment-policy v30_exact_rules --parallel 2 \
  --games-per-rotation 1 --clock 420 --seed-base 20261111
```

Le succès de l'orchestrateur signifie que les deux campagnes disposent
de manifests, de vraies traces et d'une comparaison complète ; pas que
tous les matchs soient naturellement terminés. Vérifier les compteurs
`both_natural_pairs`, `pairs_with_any_censor_or_fault` et les certificats
Scryfall (si fournis). **Ne jamais fabriquer le gagnant d'une censure.**

## Pourquoi nous ne déclarons pas encore la V31 comme simulateur pertinent

1. Le moteur sait exécuter de vraies parties mais des parties longues
   s'arrêtent à l'horloge ; 3/3 matchs aristo du pilote V30 sont censurés.
2. La V24 et la V30 n'ont pas établi de gain significatif de débit global ;
   l'optimisation de branches Java seules ne suffit pas.
3. Les heuristiques Forge, même corrigées en multiplayer, ne fournissent
   pas encore un expert Commander. Les tests de qualité tactique doivent
   s'appuyer sur **alternatives légales au même état** et données humaines
   vérifiées, pas sur le nombre de versions ou le winrate de huit parties.
4. Le rapport de légalité Scryfall et une certification indépendante
   restent nécessaires avant un winrate publiable.

## Suite technique prioritaire (V32)

1. **Faire passer l'intégration :** inspecter les 8 vraies JVM V31,
   bloquer sur toute disparition de manifest, vérifier le nombre
   de parties naturelles et l'absence de timeout hors horloge.
2. **Diagnostiquer les censures aristo :** classifier les piles timeout
   (`scripts/analyze_four_ai_timeout_stacks.py`) et le JFR,
   comparer le nombre de véritables tours et d'actions développées.
3. **Réduire le coût de la recherche IA** sur les véritables états
   souvent répétés, mais seulement via des prédicteurs AI-only prouvés
   (la pile et les règles réelles restent Forge).
4. **Améliorer les décisions** à partir de contre-factuels légaux Forge
   en même état et des lignes humaines validées ; implémenter des tests
   concrets où l'action gagnante est démontrable.
5. **Consolider les PR en main** après les portes de CI, plutôt que de
   poursuivre indéfiniment un graphe Vxx expérimental.

Passation précédente : `docs/PASSATION_ACTIVE_V28_2026-10-11.md`.
Dossier local pour opérateur : `docs/RUN_LOCAL_4AI_COMMANDER.md`.
L'intégration des PR empilées n'est pas automatiquement fusionnée.
