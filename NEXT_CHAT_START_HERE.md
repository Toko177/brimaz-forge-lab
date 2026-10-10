# REPRISE — Simulateur Magic Commander Forge, quatre IA

**Dernière passation : 10 octobre 2026.**

ATTENTION : la branche `main` contient encore un ancien moteur V6.
Les développements IA actuels sont dans une **pile de branches GitHub**.
Ne pas commencer à coder sur `main` sans avoir consulté les documents
ci-dessous.

## Branche ACTIVE et passation

- **Branche la plus récente — interactions sur pile :**
  `feature/four-ai-critical-counter-response-20261010`
- **Passation des changements les plus récents :**
  [docs/PASSATION_COUNTER_RESPONSE_2026-10-10.md](https://github.com/Toko177/brimaz-forge-lab/blob/feature/four-ai-critical-counter-response-20261010/docs/PASSATION_COUNTER_RESPONSE_2026-10-10.md)
- **PR #13 en développement :**
  https://github.com/Toko177/brimaz-forge-lab/pull/13
- **Base V20 :**
  `feature/v20-counterfactual-removal-and-tournament-20261010`,
  [PR #12](https://github.com/Toko177/brimaz-forge-lab/pull/12).
- **Histoire V13–V16 :**
  [passation V16](https://github.com/Toko177/brimaz-forge-lab/blob/feature/four-ai-critical-counter-response-20261010/docs/PASSATION_2026-10-10_V16.md),
  [passation V17](https://github.com/Toko177/brimaz-forge-lab/blob/feature/four-ai-critical-counter-response-20261010/docs/PASSATION_2026-10-10_V17.md),
  [passation V17.1](https://github.com/Toko177/brimaz-forge-lab/blob/feature/four-ai-critical-counter-response-20261010/docs/PASSATION_2026-10-10_V17_R1.md).

## Le simulateur peut être lancé depuis GitHub

- **Workflow sur main :**
  [Commander simulator — run 4 AI games](https://github.com/Toko177/brimaz-forge-lab/actions/workflows/commander-four-ai-simulator.yml)
- **Guide d'utilisation :**
  [docs/HOW_TO_RUN_FOUR_AI_SIMULATOR.md](docs/HOW_TO_RUN_FOUR_AI_SIMULATOR.md)
- Sélectionner `source_ref` sur la branche de développement la plus récente ci-dessus, un pod
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

1. **Lire d'abord la passation de la PR #13, puis celle de V20 PR #12.**
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


## V19 — amélioration expérimentale des décisions anti-créatures

La PR #11 propose de mieux sélectionner les **cibles de retrait déjà
légales** en présence d'une menace visible de perte à cause des blessures,
du poison ou des 21 blessures d'un commandant. Ce calcul s'applique aux
**quatre IA** mais ne modifie pas les règles Magic. Comparaison A/B :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38083587718

Le manuel sur main accepte `policy=v19_removal` ; ne pas considérer ce mode
comme supérieur tant que ses résultats et son audit ne sont pas examinés.

## V20 : expérience contrefactuelle et agrégation des tournois

La PR #12 ajoute un relevé **à état public identique** des deux cibles
qu'auraient choisies les politiques de retrait classique et urgente,
sans modifier les cibles légales ou les règles. Test A/B :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38085352043

Le workflow de lancement manuel sur main contient maintenant un job
`tournament-summary` qui agrège tous les processus Forge indépendants,
contrôle les artefacts et publie des résultats par pod avec incertitude
descriptive. Il n'a PAS encore été vérifié en lancement manuel complet.
Le mode `policy=v20_shadow` exploite la branche V20. La PR #12 doit
rester en draft jusqu'aux résultats de ses comparaisons à état identique.

## Expérience publique sur la pile — PR #13

Nouvelle politique optionnelle `fourSeatCounterCritical` : si Forge a déjà
validé la cible et le coût d'un contresort, ne pas le refuser uniquement à
cause d'une probabilité de contre faible lorsque le sort adverse vise
précisément à détruire/exiler/voler notre commandant. Pour les quatre IA.
CI de deux pods appariés :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38085855529

**L'ancienne V20 demeure nécessaire**, notamment le test contrefactuel de
classement des cibles et le rapport de tournoi fan-in sur main.
Validation V20 :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38085885574
Le job agrégateur sur huit véritables parties archivées a déjà réussi :
https://github.com/Toko177/brimaz-forge-lab/actions/runs/38085452376

Le lanceur manuel sur main accepte `policy=critical_counter`, mais
conserver la PR #13 en brouillon tant que les derniers logs et les
résultats naturels ne sont pas vérifiés. Ne pas conclure à une meilleure
IA sur des règles de score non exercées.
