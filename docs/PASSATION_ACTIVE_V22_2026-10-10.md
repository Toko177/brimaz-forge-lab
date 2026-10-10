# PASSATION ACTIVE — V22, quatre IA Forge, contresorts et preuve du lanceur

**10 octobre 2026.** Ce fichier est l'entrée technique pour le prochain
chat. Lire également [passation V20](PASSATION_2026-10-10_V20.md),
[passation des contresorts](PASSATION_COUNTER_RESPONSE_2026-10-10.md)
et `NEXT_CHAT_START_HERE.md` sur `main`.

## Projet : ce qui existe vraiment

- **Forge 2.0.15**, format Commander quatre joueurs, Java 21.
- Brimaz V3 + six autres decks fixes et SHA256 vérifiés,
  deux pods `aristo` et `artifact`, quatre rotations de siège,
  processus JVM isolés et vraies règles gérées par Forge.
- Branche active :
  `feature/v22-four-ai-operator-smoke-and-counter-audit-20261010`
  basée sur `feature/four-ai-critical-counter-response-20261010` (PR #13),
  qui descend de V20 PR #12, V19 PR #11, V18 #10, etc.
- PR active V22 :
  https://github.com/Toko177/brimaz-forge-lab/pull/14
- Lanceur manuel opérationnel **dans le dépôt sur main** :
  https://github.com/Toko177/brimaz-forge-lab/actions/workflows/commander-four-ai-simulator.yml
  et [manuel](https://github.com/Toko177/brimaz-forge-lab/blob/main/docs/HOW_TO_RUN_FOUR_AI_SIMULATOR.md).

**Important :** `main` contient encore l'ancien moteur V6 mais garde
un *lanceur stable* qui checkout la branche `source_ref` active.
Les modifications IA sont dans une pile de PR en brouillon ; ne pas
partir de `main` pour développer ou présenter V22 comme fusionnée.

## Observations V19, V20, PR #13 (vérifiées)

V19 : 8 processus réels / 4 paires, chaque paire même gagnant,
événements identiques, pas de gain de jeu démontré.

V20 : run
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38086336596,
quatre jobs **SUCCESS**. Comparaison à état public identique sur les
cibles déjà légales :
- aristo rotation 1 : 69 classements de cibles ;
- aristo rotation 2 : 272 ;
- artifact rotation 2 : 258 ;
- artifact rotation 1 : 205 classements de référence,
  mais deux matchs classés `clock_censored` (205 vs 204 appels de classement).
- **804 évaluations de référence, zéro changement de meilleur choix**
  calculé avec le bonus V19. Six parties naturelles et
  **deux censurées**. Les censures ne sont pas des défaites.
  Ne pas fusionner V19 comme une amélioration démontrée de stratégie.
  L'outil V20 de comparaison **sur les mêmes cibles légales**
  est en revanche une infrastructure empirique utile.

PR #13 (contre au retrait ciblant le commandant), run
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38086348519 :
deux pods appariés, **4 vraies parties naturelles**, **11 tests
tactiques** ; **zéro déclenchement de l'override de contresort**.
La politique est valide dans ces tests mais sans bénéfice observé.

Tournoi : le rapport d'agrégation multi-job a été vérifié sur huit
vrais journaux Forge archivés :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38085452376.
8 naturelles / 0 censurées, sans certification indépendante de chaque
règle Oracle, ni démonstration statistique de compétence humaine.
Le lancement **manuel complet** sur main est toujours à éprouver ;
un succès du test d'archive n'est pas une validation du workflow_dispatch.

## Nouvelles améliorations de V22

### Réponse contre un sort public létal

Le `MultiplayerCriticalCounterPolicy` protège désormais les quatre IA
contre deux catégories de menaces ciblées :
1. Destruction, changement de zone ou prise de contrôle **de leur propre
   commandant** par un sort adverse public ;
2. Un sort public hostile `DealDamage` ou `LoseLife` ciblant
   **un seul joueur : cette IA**, avec un nombre de dégâts/perte de vie
   directement et exactement numérique, >= son total de points de vie,
   et aucune protection `cantLoseForZeroOrLessLife` active.

**Garde-fous importants :** ignore les montants inconnus
(`X`, formules et effets variables), les sorts non ciblés,
les dégâts répartis ou divisés entre plusieurs cibles et tout
contresort qui échoue aux contrôles Forge de coût, pile, légalité de
la cible, protection et contre légal.
Ne regarde aucune main cachée adverse et ne change pas les règles de
Magic. La politique reste opt-in :
`-Dbrimaz.fourSeatCounterCritical=true`.

Ce n'est pas un prédicteur Oracle absolu : un effet de prévention,
redirection ou remplacement complexe peut exister. Le mot
« létal » désigne ici une **menace publique simple**.

### Observabilité : les quatre IA et leur vraie pile

Nouveau flag `-Dbrimaz.counterDecisionAudit=true` sur le source
`CounterAi` épinglé à 2.0.15 :
`FOUR_AI_COUNTER_DECISION player=... spell=...
originalDecline=... threatensCommander=... threatensLethalLife=...`.
Chaque observation correspond à un vrai appel de l'IA à Forge,
pas à un contresort effectivement lancé. Les événements
`FOUR_AI_CRITICAL_COUNTER accepted` sont séparés des actions
`Add To Stack` réelles.

`scripts/forensic_four_seat.py` extrait ces événements par siège,
par tour, et ajoute au rapport des compteurs précis :
- sorts adverses considérés par un contresort disponible,
- refus initiaux de profil / CMC,
- menaces sur le commandant et sur les points de vie,
- exceptions acceptées, **sans assimiler acceptation à sort lancé**.
Le test de parser synthétique étiqueté
`tests/test_forensic_four_seat.py` contient une menace par `Lightning
Bolt` et ne contribue jamais aux statistiques de parties réelles.

### Premier test de bout en bout

Workflow :
`.github/workflows/four-ai-v22-end-to-end.yml`.
Run initial :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38087749915
(son statut est un instantané ; **vérifier le run le plus récent**
dans Actions au début du prochain chat).

Ce smoke exécute toutes les étapes essentielles avec une **vraie JVM** :
- 7 listes canoniques / 7 empreintes SHA256 ;
- distribution Forge 2.0.15 d'origine et patchs V13–V22 ;
- compilation / tests Java et Python ;
- **une vraie partie** Commander 4 IA (pod aristo rotation 1) ;
- `batch.py` et les vraies données de résultat,
  `forensic_four_seat.py` puis
  `aggregate_four_ai_tournament.py`, qui exige 1 job + 1 partie ;
- upload de tous les logs et des rapports.

Ce smoke valide les composants du lanceur, **pas encore le
workflow_dispatch manuel complet sur main**, ni les centaines de
parties nécessaires à une évaluation du winrate.

## Travaux prioritaires (prochain chat)

1. **Consulter le dernier run V22**. Corriger les erreurs de compilation,
   Python, ou d'agrégation au lieu de multiplier les PR. Ne pas inventer
   la réussite d'une étape inachevée.
2. Étendre les tests Forge à de **vraies situations de jeu** avec
   contresort légal, deux options de réponse et menace du commandant /
   vie. Distinguer « IA a choisi de contre » et « sort a été lancé /
   a résolu » ; prouver le bénéfice dans un état public comparable.
3. Tracer d'autres décisions où la V20 constate un **choix
   réellement différent** : priorité de survie vs développement,
   attaques vs garde de bloqueurs, activation de ressources et
   tempo du commandant. Ne plus régler les bonus V19 à l'aveugle.
4. Premier test manuel `workflow_dispatch` sur main avec
   `pod=both`, `games_per_rotation=1` (8 vraies parties),
   puis campagne 16–40 avec SHA et censures. La durée dépend des
   vraies JVM, aucun chiffre de débit n'est actuellement certifié.
5. Alimenter le pipeline humain The Command Zone / SOLRING si
   des sous-titres légalement disponibles sont récupérables ;
   aucune trajectoire humaine complète n'est encore certifiée.
6. Mettre à jour le **pointeur main**, cette passation, les PR
   et les Actions après chaque modification.

L'objectif n'est **pas** de fabriquer artificiellement 25 % de
victoires pour Brimaz, mais de disposer rapidement d'un moteur
mesurable à quatre IA, fidèle à Forge et capable de décisions
tactiques testables.

