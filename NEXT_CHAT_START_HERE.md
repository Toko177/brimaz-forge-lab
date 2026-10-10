# REPRISE — Simulateur Magic Commander Forge, quatre IA

**Dernière passation : 10 octobre 2026.**

ATTENTION : la branche `main` contient encore un ancien moteur V6.
Les développements IA actuels sont dans une **pile de branches GitHub**.
Ne pas commencer à coder sur `main` sans avoir consulté les documents
ci-dessous.

## Branche ACTIVE et passation

- **Branche expérimentale la plus récente — performance V23 :**
  `feature/v23-ai-timeout-cooldown-20261010`
- **Passation des changements les plus récents :**
  [docs/PASSATION_ACTIVE_V23_2026-10-10.md](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v23-ai-timeout-cooldown-20261010/docs/PASSATION_ACTIVE_V23_2026-10-10.md)
- **PR #16 expérimentale :**
  https://github.com/Toko177/brimaz-forge-lab/pull/16
- **Base d’intégration V22 :**
  `integration/four-ai-commander-simulator-20261010`,
  [PR #15](https://github.com/Toko177/brimaz-forge-lab/pull/15).
- **Histoire V13–V16 :**
  [passation V16](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v22-four-ai-operator-smoke-and-counter-audit-20261010/docs/PASSATION_2026-10-10_V16.md),
  [passation V17](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v22-four-ai-operator-smoke-and-counter-audit-20261010/docs/PASSATION_2026-10-10_V17.md),
  [passation V17.1](https://github.com/Toko177/brimaz-forge-lab/blob/feature/v22-four-ai-operator-smoke-and-counter-audit-20261010/docs/PASSATION_2026-10-10_V17_R1.md).

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

## V22 — vrai test de bout en bout et trace des décisions sur la pile

- **Passation V22 active :** https://github.com/Toko177/brimaz-forge-lab/blob/feature/v22-four-ai-operator-smoke-and-counter-audit-20261010/docs/PASSATION_ACTIVE_V22_2026-10-10.md
- Nouveau modèle optionnel de contresort : menace publique ciblée
  sur notre commandant, ou dommages/perte de vie **chiffrés exactement,
  ciblant exclusivement notre joueur**, qui atteignent son total de vie.
  Les règles Forge restent seules maîtresses des cibles, du coût et
  de la pile ; évite X, répartitions et mains cachées.
- Les quatre IA journalisent leurs décisions de contresort
  (`FOUR_AI_COUNTER_DECISION`) : menaces, refus initiaux,
  acceptations **sans confondre choix et sort lancé**.
- **CI V22 de bout en bout :** https://github.com/Toko177/brimaz-forge-lab/actions/workflows/four-ai-v22-end-to-end.yml
  / PR #14. Elle exécute 1 vraie partie Forge 4 IA avec 7 SHA de decks,
  compilation et agrégation ; vérifier le **dernier** run.
- Le lanceur manuel sur main prend `source_ref` V22 et active la
  télémétrie des contresorts avec `policy=critical_counter`.
- V20 : **804 évaluations de cibles légales de référence, zéro choix
  changé par V19** ; six parties naturelles et deux censurées.
  Ne pas adopter V19 par défaut en affirmant un bénéfice non mesuré.


## CANDIDATE D'INTÉGRATION — point de réunion des branches

La [PR #15](https://github.com/Toko177/brimaz-forge-lab/pull/15)
vise directement `main` depuis
`integration/four-ai-commander-simulator-20261010`, elle-même basée
sur la V22. C'est la candidate **unique** pour sortir de l'empilement
des PR expérimentales. Elle reste volontairement en brouillon :
ce n'est pas une preuve de niveau humain ni une autorisation de
fusion sans vérification.

Lire :
[docs/INTEGRATION_RELEASE_CANDIDATE.md](https://github.com/Toko177/brimaz-forge-lab/blob/integration/four-ai-commander-simulator-20261010/docs/INTEGRATION_RELEASE_CANDIDATE.md).

La PR #15 exige un test d'intégration avec **une vraie partie Forge
à quatre IA** ; vérifier son dernier GitHub Action.
Les modifications tactiques peuvent continuer sur la V22, mais
ne pas perdre la candidate d'intégration ni le lanceur sur main.

## V23 — nouvelle expérimentation contre les répétitions de timeout

**Branche la plus récente :** `feature/v23-ai-timeout-cooldown-20261010`
**PR #16 :** https://github.com/Toko177/brimaz-forge-lab/pull/16
**Passation dédiée :**
https://github.com/Toko177/brimaz-forge-lab/blob/feature/v23-ai-timeout-cooldown-20261010/docs/PASSATION_ACTIVE_V23_2026-10-10.md

V23 descend de la **candidate d'intégration PR #15**, pas de l'ancienne
V6 sur main. Le smoke E2E de la PR #15 a réussi le pipeline mais sa
**partie a été censurée à 360 s, sans gagnant naturel**. Elle a signalé
3 timeouts IA (5/10/15 s) sur l'IA Zimone/Dina avec `Magic Damper`
comme dernière candidate observée, aux tours 28, 32 et 36.

V23 expérimente, par siège et **uniquement après un véritable timeout**,
un cooldown borné de 4/8/12/16 tours globaux pour l'ID de carte
couramment évalué. La politique n'intervient pas dans le choix des
contresorts sur la pile (`skipCounter=false`), ne blacklist jamais
une carte définitivement, et reste **désactivée** sans
`-Dbrimaz.aiTimeoutCooldown=true`.

CI appariée (4 vraies JVM) :
https://github.com/Toko177/brimaz-forge-lab/actions/workflows/four-ai-v23-cooldown.yml
Lire ses derniers logs et **vérifier que Forge démarre** avant d'en
présenter les résultats : une version initiale du patch compilait le
helper Java sans l'insérer dans le JAR, causant un
`NoClassDefFoundError` ; ce défaut d'assemblage a été corrigé.

L'ancienne PR #15 demeure candidate de consolidation vers main.
Ne pas fusionner V23 avant le comparatif réel et les contrôles de
légalité de la mise à l'écart. Les premiers logs sont des échantillons,
pas des preuves générales de gain de vitesse ou de niveau d'IA.
