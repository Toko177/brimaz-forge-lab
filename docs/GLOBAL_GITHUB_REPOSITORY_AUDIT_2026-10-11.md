# Bilan final — nettoyage global GitHub du 11 octobre 2026

**Nettoyage exécuté**, et pas seulement audité :
- [PR d'intégration #28](https://github.com/Toko177/brimaz-forge-lab/pull/28)
  fusionnée dans `main` sans force-push et avec double ascendance
  préservant le `main` d'origine et tous les expérimentations divergentes ;
- **30 anciennes branches distantes supprimées** et vérifiées par
  [l'action GitHub réussie #38131746597](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38131746597) ;
- **2 branches conservées :** `main` et
  `archive/experimental-branches-20261011` ;
- **0 PR ouverte** ; les anciennes PR sont closes ou fusionnées, leurs
  commentaires et commits demeurent accessibles ;
- **16 workflows de maintenance et d'expérimentation** après retrait
  du workflow de suppression unique ; conservés aussi les 7 decks SHA256,
  les tests Java21, le lanceur manuel, la filière deckbuilding ;
- la référence d'une vraie victoire Brimaz précédemment propre à
  `main` a été conservée.

L'historique des commits est volontairement conservé ; la suppression
de références ne vise pas à purger des données Git de manière irréversible.
Les artefacts des parties réelles restent utiles à la validation et
peuvent expirer suivant la rétention GitHub ; aucun effacement de preuves
n'a été effectué. Aucun gain stratégique V33 n'est encore démontré.

---

## Inventaire *avant* nettoyage (historique)

**Périmètre audité :** [Toko177/brimaz-forge-lab](https://github.com/Toko177/brimaz-forge-lab)
sur les **29 branches** exposées par l'API GitHub, la totalité des **27 pull
requests**, les arbres courants de `main` et de V34, et la liste des releases.
Toutes les comparaisons de branches ci-dessous ont été faites contre
`feature/v34-repository-cleanup-20261011`.

**Point décisif :** la V34 n'est **pas** un nettoyage global finalisé.
Elle ne nettoie qu'un arbre de travail ; elle ne supprime pas les références
distantes, ni ne réécrit l'historique. Aucun autre arbre n'a été modifié par
cet audit.

## Résumé confirmé

| Surface | État |
|---|---|
| Branches Git distantes | **29**, dont `main` et V34 |
| Branches entièrement ancestrales ou égales à V34 | **22** |
| Branches avec commits propres, non ancêtres de V34 | **7**, incluant `main` |
| Pull requests | **27 : 26 ouvertes (brouillons), 1 fermée et non fusionnée** |
| Issues distinctes des pull requests | **0** |
| GitHub Releases publiées | **0** |
| `main` | **85 fichiers suivis**, dont **42 workflows** |
| V34 | **192 fichiers suivis**, dont **15 workflows** |
| Branche V34 | 110 suppressions de fichiers historiques déjà enregistrées |
| Tags Git | **Non vérifiés** : non accessibles via les appels de ce connecteur |
| Artifacts Actions / caches / logs | **Non épurés** : garder les résultats réels tant que la qualité IA n'est pas validée |

## Sept branches divergentes : NE PAS effacer

| Branche | Commits propres absents de l'ascendance de V34 |
|---|---:|
| `main` | **48** |
| `feature/combat-trigger-fast-v13-20261010` | **8** |
| `feature/combat-trigger-scan-differential-20261010` | **4** |
| `feature/v20-counterfactual-removal-and-tournament-20261010` | **2** |
| `feature/v26-real-forge-jfr-cpu-20261011` | **2** |
| `feature/v27-four-ai-strategic-forensics-20261011` | **5** |
| `feature/v29-real-commander-recast-legal-alternatives-20261011` | **5** |

`main` comparée à V34 : **divergence (48 commits propres dans main,
455 dans V34)**. Forcer ou remplacer `main` par V34 détruirait une
ligne de développement encore non réconciliée. Utiliser une **fusion
ordinaire après revue des différences**, jamais `reset --hard` ou
force-push sans sauvegarde et évaluation.

Les branches divergentes ne sont pas nécessairement des corrections
à appliquer : certaines sont des pilotes diagnostiques. Leurs commits
doivent être classés et rapprochés de l'arbre cible avant suppression.

## 22 branches entièrement couvertes par les commits V34

Les branches suivantes ont **0 commit unique** vis-à-vis de V34 ;
la suppression éventuelle de la référence peut attendre
la consolidation de `main` et des PR :

- `feature/four-ai-critical-counter-response-20261010`
- `feature/four-ai-multiplayer-lethal-targets-20261010`
- `feature/human-video-fetch-and-tax-analysis-20261010`
- `feature/simulator-core-v15-human-playbooks-20261010`
- `feature/v16-multiplayer-defense-and-handoff-20261010`
- `feature/v17-defense-robustness-20261010`
- `feature/v17-multiplayer-threat-coverage-20261010`
- `feature/v18-gameplay-forensics-and-release-gate-20261010`
- `feature/v19-opponent-removal-urgency-20261010`
- `feature/v22-four-ai-operator-smoke-and-counter-audit-20261010`
- `feature/v23-ai-timeout-cooldown-20261010`
- `feature/v24-combat-trigger-fast-negatives-20261011`
- `feature/v25-all-seats-real-evidence-20261011`
- `feature/v28-real-card-property-hotpath-profile-20261011`
- `feature/v30-exact-card-property-fastpath-20261011`
- `feature/v31-eight-seat-property-rules-rollout-20261011`
- `feature/v31-reproducible-4ai-operator-20261011`
- `feature/v32-persistent-canonical-commander-decks-20261011`
- `feature/v33-multiplayer-strategic-planner-20261011`
- `feature/v34-repository-cleanup-20261011` (branche cible elle-même)
- `improve/realism-and-ai-diagnostics`
- `integration/four-ai-commander-simulator-20261010`

Redondance explicite : `feature/v31-eight-seat-property-rules-rollout-20261011`
et `feature/v30-exact-card-property-fastpath-20261011` pointent
exactement vers `377996e2fc5a382914ed2dcfc3c2d7c66bfc471b`.

**Nuance importante :** un ancêtre dans l'historique Git n'implique pas
que chaque ancienne expérience reste activée dans l'arbre final.
Les décisions délibérées de la V34 peuvent laisser des expériences
inactives et enlever des fichiers historiques.

## Plan de consolidation sans perte

1. **Préserver les preuves.** Conserver les SHA de tête de ces
   29 branches, les rapports de légalités et les artifacts de parties
   originales. Éviter toute réécriture de l'historique.
2. **Classifier les commits non intégrés.** Réconcilier les 48
   commits propres de `main` et les 26 commits cumulés propres aux six
   branches expérimentales divergentes (les comptages peuvent se
   chevaucher). Reprendre seulement le code nécessaire, sans perdre
   une correction importante.
3. **Établir une vraie PR d'intégration vers `main`.**
   Valider source Forge Java 21, decks SHA256, suites Python,
   vrais benchmarks A/B, absence de perte de capacité deckbuilding.
4. **Fusionner sans force-push** après revue, pas avant.
   Corriger la documentation V34 après fusion.
5. **Clore les PR devenues redondantes** après vérification de
   leur présence dans la nouvelle branche principale. Certaines PR
   s'appuient sur d'autres comme base et ne doivent pas être détruites
   pendant leur analyse.
6. **Supprimer les branches obsolètes**, idéalement après création
   d'un tag d'archive connu et résolution des divergences.
   Le connecteur GitHub disponible ici permet de modifier les fichiers,
   branches via leur ref, et PR, mais n'expose **pas d'action de
   suppression de branche** : il faut une opération GitHub UI ou Git
   distante autorisée pour cette dernière étape.
7. **Nettoyer les artefacts temporaires** seulement après avoir
   conservé les preuves de vraies parties nécessaires à la vérification
   stratégique et aux audits reproductibles.

## Blocage indépendant du nettoyage : qualité de l'IA

La [campagne V33 de 16 JVM Forge réelles](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38128781081)
a fini naturellement dans les 16 cas, mais le premier audit du
planificateur utilisait un motif de journal incorrect et une regex
doublement échappée. **Le résultat antérieur « zéro action approuvée »
est non fiable**, pas une preuve d'absence d'interventions.
La V34 corrige le parseur ; **les artifacts originaux doivent être
réanalysés** avant de prétendre que l'IA est meilleure ou inchangée.

## Modification réelle déjà effectuée

Seulement `feature/v34-repository-cleanup-20261011`
(PR [#27](https://github.com/Toko177/brimaz-forge-lab/pull/27)) :
110 fichiers supprimés, conservation des 7 decks canoniques,
15 workflows maintenus, documentation réécrite, contrôles Python 3.10/3.12
réussis. **Ni `main`, ni les 28 autres branches, ni les 27 PR n'ont
été supprimées, modifiées ou fusionnées au titre de ce nettoyage global.**
