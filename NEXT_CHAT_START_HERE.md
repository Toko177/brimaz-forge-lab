# REPRISE — Simulateur Magic Commander Forge, quatre IA

**Dernière passation : 10 octobre 2026.**

ATTENTION : la branche `main` contient encore un ancien moteur V6.
Les développements IA actuels sont dans une **pile de branches GitHub**.
Ne pas commencer à coder sur `main` sans avoir consulté les documents
ci-dessous.

## Branche ACTIVE et passation

- **V18, branche active :**
  `feature/v18-gameplay-forensics-and-release-gate-20261010`
- **Passation intégrale V18 :**
  [docs/PASSATION_2026-10-10_V18.md](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v18-gameplay-forensics-and-release-gate-20261010/docs/PASSATION_2026-10-10_V18.md)
- **PR #10 en développement :**
  https://github.com/Toko177/brimaz-forge-lab/pull/10
- **Base V17.1 :**
  `feature/v17-defense-robustness-20261010`,
  [PR #9](https://github.com/Toko177/brimaz-forge-lab/pull/9).
- **Histoire V13–V16 :**
  [passation V16](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v18-gameplay-forensics-and-release-gate-20261010/docs/PASSATION_2026-10-10_V16.md),
  [passation V17](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v18-gameplay-forensics-and-release-gate-20261010/docs/PASSATION_2026-10-10_V17.md),
  [passation V17.1](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v18-gameplay-forensics-and-release-gate-20261010/docs/PASSATION_2026-10-10_V17_R1.md).

## Le simulateur peut être lancé depuis GitHub

- **Workflow sur main :**
  [Commander simulator — run 4 AI games](https://github.com/Toko177/brimaz-forge-lab/actions/workflows/commander-four-ai-simulator.yml)
- **Guide d'utilisation :**
  [docs/HOW_TO_RUN_FOUR_AI_SIMULATOR.md](docs/HOW_TO_RUN_FOUR_AI_SIMULATOR.md)
- Sélectionner `source_ref` sur la branche V18 ci-dessus, un pod
  `artifact`/`aristo` ou `both`, une politique IA et 1–5 parties
  par rotation. Chaque partie utilise un **processus Forge réel**
  avec quatre sièges IA distincts, listes de cartes vérifiées SHA256.
- Les sorties sont les vrais journaux, manifestes, statistiques
  per-seat et SHA des exécutables, archivés dans GitHub Actions.

Le workflow manuel a été installé sur main, mais son **premier
lancement manuel n'a pas encore été vérifié** au moment de cette
passation. Le futur chat doit vérifier les vrais résultats GitHub
avant toute affirmation de vitesse.

## Résultats les plus utiles déjà vérifiés

- V17 : [8 parties naturelles et quatre jobs réussis](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38081333961)
  mais aucun gain de victoire ou de vitesse certifié.
- V17.1 : [8 parties naturelles, mode anticipatif](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38082154931),
  1 bloqueur retenu, aucune amélioration de winrate démontrée.
- V18 : [audit de 8 véritables logs à quatre joueurs](https://github.com/Toko177/brimaz-forge-lab/actions/runs/38082918169),
  119 sorts Brimaz, 24 lancements du commandant, 26 activations
  d'Incubateurs, 87 dégâts de combat infligés contre 389 reçus,
  0 victoire Brimaz. **Quatre conditions appariées, pas huit
  échantillons stratégiques indépendants.**

## Consignes au prochain ChatGPT

1. **Lire d'abord la passation V18 et le statut actuel de la PR #10.**
2. Vérifier les nouveaux GitHub Actions, branches, commits et artefacts
   directement dans le dépôt ; ne pas deviner les résultats.
3. Continuer à **modifier le code et lancer des tests**, en visant
   les décisions des **quatre IA**, la survie/pression de Brimaz et
   les interactions en pile avec trois adversaires.
4. Garder les options tactiques réversibles et comparables aux
   variantes V13/V17 et **ne jamais changer les règles Magic ou
   les decks adverses** pour fabriquer de meilleures statistiques.
5. Conserver les censures, séparer fonctionnalité du moteur,
   légalité Scryfall, compétence IA et winrate certifié.
6. **Mettre à jour la passation ET CE POINTEUR sur main** avant
   de terminer chaque nouveau chat de développement.

Pour contexte antérieur, conserver :
`docs/RAPPORT_TRANSFERT_INTEGRAL_2026-10-09.md` et
`docs/PASSATION_ACTIVE_2026-10-10.md` sur la branche V13.

