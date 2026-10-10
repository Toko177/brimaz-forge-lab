# V27 — Diagnostic stratégique, fondé uniquement sur 16 vraies parties Forge

**11 octobre 2026.** PR à ouvrir depuis
`feature/v27-four-ai-strategic-forensics-20261011` vers
`feature/v26-real-forge-jfr-cpu-20261011`, qui hérite du
vrai moteur quatre IA de V25/V24.

## Pourquoi

Le pilote V24 sur deux paires A/B était naturellement terminé
avec le même déroulement et **30 921 prédictions de déclenchement
impossibles évitées** (ratios 1,041× et 1,022×). Sur la campagne
V25 à huit rotations, au moins une paire a divergé :
**Aristocrates, rotation 0** (Brimaz vainqueur dans le contrôle,
Kaal_9594008 dans l'expérimental), 1 timeout IA dans chaque
partie et 757 948 appels hypothétiques évités. Une graine identique
ne suffit pas à prouver une équivalence des décisions dans un
moteur où les IA utilisent des délais et de la concurrence.

Le but de V27 est de **rendre ces différences explicables sans
inventer de coups légaux non joués** et de prioriser de vraies
hypothèses d'amélioration stratégique.

## Code

- `scripts/first_real_four_ai_divergence.py` :
  lit les **16 journaux réels**, 2 pods, 4 rotations, V24 OFF/ON,
  mêmes listes et graines. Compare séquentiellement les événements
  `Turn`, `Phase`, `Add To Stack`, `Combat`, `Life`,
  `Damage`, `Land`, `Zone Change`, `Game Outcome`,
  `Counter` et `Poison`. Enregistre le **premier événement
  différent** (ou l'existence d'un événement manquant), avec
  trois événements antérieurs, quatre suivants et le nombre de
  vrais `AI_EVAL_TIMEOUT_V10` déjà observés avant cette divergence.
  Aucune inférence causale automatique.
- `scripts/triage_real_four_ai_strategy.py` :
  combine les vraies métriques **des quatre IA**, par deck, pod,
  politique, siège et partie : terres et sorts joués,
  attaques/dégâts, timeouts, commander Brimaz relancé plusieurs
  fois, état des fenêtres de synergie Phyrexian/sacrifice,
  contresorts effectivement envisagés.
  Les **activations** d'Incubateur sont nommées *activations non
  certifiées comme transformations*, puisque `Add To Stack:
  activated Incubator Token` n'est pas preuve de résolution.
- Tests exclusivement SYNTHÉTIQUES pour vérifier la détection
  de divergences et timeouts :
  `tests/test_first_real_four_ai_divergence.py`,
  `tests/test_triage_real_four_ai_strategy.py`.
  Ils ne comptent jamais comme jeux réels.
- `.github/workflows/v27-four-ai-strategic-triage.yml` :
  récupère **les vrais artefacts du run V25**
  https://github.com/Toko177/brimaz-forge-lab/actions/runs/38094639616
  ; exige exactement **16 manifests + 16 vrais journaux**
  et publie `strategic_triage.md/json`,
  `first_gameplay_divergence.json`,
  `four_seat_summary.md`, `tournament.json`,
  `ai_timeout_stacks.json`, `readiness.json`.

## Règles de lecture

- Une IA jouant trois tours sans poser de terrain n'a pas
  nécessairement raté une pose légale : elle peut n'avoir
  aucun terrain en main.
- Aucune activation d'outlet dans un journal ne prouve
  qu'un sacrifice était légal ou bénéfique.
- Des gagnants différents sur une paire A/B après timeout
  ne prouvent ni un bug ni une amélioration stratégique.
- Une victoire naturelle Forge ne certifie pas toutes les
  règles Oracle.
- Les paires A/B partagent graines et adversaires, donc
  leur taux de victoire n'est pas une estimation iid
  de la compétence humaine de Brimaz.

## Prochaines améliorations efficaces

1. Examiner l'ordre de la **première divergence** sur aristo
   rotation 0, notamment les timeouts préalables et
   les vraies décisions de combat.
2. Examiner les **30 premières méthodes CPU JFR**, avec
   `CardProperty.cardHasProperty` à **46,18 % des
   échantillons** lors d'une vraie partie aristo :
   https://github.com/Toko177/brimaz-forge-lab/actions/runs/38095235384.
3. La branche `feature/v28-real-card-property-hotpath-profile-20261011`
   ajoute une sonde en lecture seule à cette fonction de
   règles : identifier les propriétés dominantes avant
   toute optimisation. Ne JAMAIS fabriquer un cache de règles
   sans gérer l'invalidation quand la pile et les statics évoluent.
4. Implémenter **seulement ensuite** des tests de
   contrefactuels aux mêmes états publics avec options
   légales Forge, dans les combats, les réponses sur pile et
   la gestion des coûts du commandant.

**Point d'entrée de tous les futurs chats :**
`NEXT_CHAT_START_HERE.md` sur `main`. Candidate
d'intégration PR #15 non fusionnée.
