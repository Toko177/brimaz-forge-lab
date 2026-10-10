# Passation V23 — traiter les ralentissements réels des quatre IA

**10 octobre 2026**. Branche actuelle :
`feature/v23-ai-timeout-cooldown-20261010`, basée sur
`integration/four-ai-commander-simulator-20261010` (PR #15).
PR V23 : https://github.com/Toko177/brimaz-forge-lab/pull/16

## Motif empirique : une partie fonctionnelle mais censurée

Le test d'intégration V22 (run
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38088096334)
est **SUCCESS** : 7 SHA canoniques, 20 invariants Java,
une vraie partie Commander Forge 2.0.15 à quatre IA et les
rapports `four_seat_actions.json` + `tournament.json`.

**Mais** cette unique partie (`aristo`, rotation 1, seed 20271023)
a été **censurée par l'horloge** à 360,141 secondes de simulation,
371,59 secondes murales, après 37 événements `Turn:`.
Pas de victoire ni de défaite certifiée pour aucun des quatre sièges.
Cette distinction doit rester visible et ne peut être masquée par la
réussite technique CI.

Le journal réel démontre **3 dépassements de temps IA** pour
`Ai(3)-EDH Zimone and Dina aristo` :
- tour global 28, phase `COMBAT_BEGIN` : 5001 ms, dernière candidate
  `Magic Damper` ;
- tour global 32, `COMBAT_BEGIN` : 10000 ms, `Magic Damper` ;
- tour global 36, `COMBAT_BEGIN` : 15000 ms, `Magic Damper`.

Le moteur augmente déjà la durée autorisée à toutes les IA de
5 à 10 puis 15 secondes (V13), mais réévalue encore ce même candidat
plusieurs tours après. Ceci constitue un coût de calcul observable,
**sans preuve que Magic Damper est la cause unique du ralentissement** :
le « dernier candidat » n'est qu'un échantillon de la phase active.
Ne pas présenter une corrélation d'échantillon comme certitude.

## Changement V23 — test limité, opt-in

- Helper Java `patches/java/forge/ai/AiTimeoutCooldownPolicy.java`,
  **une instance par `AiController` et donc par siège et par partie**.
- `scripts/patch_forge_brimaz_v13.py` compile ce helper contre le
  vrai JAR Forge, l'insère dans le JAR avec `AiController`, et
  enregistre l'ID de carte Forge du dernier candidat en cours.
- **Uniquement après `TimeoutException`** : mettre en place un
  cooldown pour cet ID de carte, selon le nombre de fois où il
  a déjà provoqué un timeout : 4, 8, 12 puis 16 tours globaux maximum.
  Pas de blacklist permanente ; le cooldown expire de lui-même.
- La politique ne saute la carte que pendant l'évaluation **normale**
  des actions `skipCounter=true`. Elle n'interdit donc pas un
  contre ou une réponse urgente sur la pile.
- Jauge : `-Dbrimaz.aiTimeoutCooldown=true`. Le comportement
  historique reste `false`. Chaque décision est contrôlée
  par la version originale Forge, le patch ne change jamais les
  coûts ni les capacités des cartes.
- Log `FOUR_AI_TIMEOUT_COOLDOWN_V23` :
  siège, nom, ID de carte, tour d'expiration, nombre de frappes.
  Une attribution à la mauvaise carte n'est pas impossible si un
  sous-appel long se déroule entre deux mises à jour. C'est pourquoi
  il faut garder ce mécanisme expérimental, réversible, jamais
  activé sans essais.

## Tests / campagnes

- `tests/java/forge/ai/AiTimeoutCooldownChecks.java` :
  **18 invariants** de séparation des sièges, exclusion temporaire,
  expiration et croissance plafonnée.
- `.github/workflows/four-ai-v23-cooldown.yml` :
  deux matrices `aristo rotation 1` et `artifact rotation 2`,
  une vraie partie Forge par mode et matrice, **4 JVM réelles**.
  Même SHA de sept decklists, même graine et quatre sièges par paire.
- `scripts/audit_v23_cooldown.py` : recense les
  `AI_EVAL_TIMEOUT_V10`, les cooldowns réellement posés,
  le statut des fins naturelles/censures, les gagnants et SHA des
  événements de chaque politique. N'accorde de ratio de vitesse
  qu'aux **parties naturellement terminées avec événements comparés
  strictement identiques**.
- Run initial V23 :
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/38089880394
  (**statut à revérifier** : le processus était encore en cours au
  moment de rédaction).
- Un premier workflow YAML V23 n'avait pu démarrer car un intitulé
  contenait un deux-points non quoté ; corrigé avant le pilot actuel.
  Ne pas confondre ce refus de parser avec un défaut Java.

## Intégration future / usage

La PR #15
https://github.com/Toko177/brimaz-forge-lab/pull/15
est une candidate générale vers `main` qui reste DRAFT.
V23 est expérimentale **au-dessus** de cette candidate ; ne pas
la fusionner tant que la diminution des timeouts et l'absence de
dégradation des choix ne sont pas prouvées.

Le workflow manuel stable sur `main` reste
https://github.com/Toko177/brimaz-forge-lab/actions/workflows/commander-four-ai-simulator.yml
et le pointeur de reprise est `NEXT_CHAT_START_HERE.md` sur `main`.
Le workflow `workflow_dispatch` n'a pas encore reçu son premier
essai manuel certifié. Éviter de prétendre que l'agrégateur d'archives
équivaut à son essai bout en bout.

Prochaines priorités :
1. Lire logs réels V23; corriger compilation, commande ou audit.
2. Comparer les dépassements de délai par siège, pas seulement
   le temps total. Vérifier les éventuelles censures et même actions.
3. Tester la réactivation ultérieure de la carte par un état Forge
   contrôlé pour éviter qu'une carte importante soit injustement ignorée.
4. Profiler les hot spots du combat avec JFR avant de généraliser.
5. Garder les solutions expérimentales optionnelles, faire évoluer
   la PR #15 comme candidate intégrable.
6. Actualiser la passation et `NEXT_CHAT_START_HERE.md` à chaque
   futur chat, ainsi que les vrais numéros de run et SHA.

