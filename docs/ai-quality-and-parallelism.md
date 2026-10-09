# Forge Commander AI quality and parallel benchmark

Date: 2026-10-09 | Engine: Forge 2.0.15 | Source: real game logs, not draw simulations.

## Verified baseline

- Four AI-controlled Commander seats execute headlessly in Forge.
- One mixed playgroup pilot ended with Zimone and Dina winning.
- In four complete rotated games with Brimaz / Radha / Tazri / Zimone and Dina:
  - Brimaz 0 wins, Radha 2, Tazri 2, Zimone and Dina 0.
  - All four games completed before the 360-second Forge clock.
  - Not statistically sufficient for deck ranking.

## Four-game AI audit

Machine-readable artifact from workflow "Audit Forge AI decision traces":

- 23 Brimaz Incubator transformations.
- 7 Brimaz end-step triggers; 2 were during opponents' end steps.
- 12 sacrifice-engine activations: 11 Arcbound Ravager, 1 High Market.
- No observed sacrifice activation during the opponent's turn BEFORE its end step. This is the relevant window for Brimaz's turn-specific death condition; activating after the end step starts is too late.
- Four of four logs emitted `No AI assigned for API: Incubate`.
- Substantial clustering: 11 Arcbound Ravager activations logged during one cleanup step in one match. Whether tactical or a heuristic defect is unresolved; needs game-state inspection.

**Important:** Brimaz checks Phyrexian deaths at the START of the end step; the AI must trigger an eligible death before that point. No activation does NOT mean an activation was legal, available, and beneficial. The audit does not reconstruct hands or board state, and triggers need the actual Phyrexian-death precondition.

## Implemented response

1. `scripts/batch.py` accepts `--rotation`, `--seed-base`, `--profile-brimaz`, `--profile-opponents`, `--out-tag`.
2. `parallel-benchmark.yml` distributes 2 pods × 4 positions × 2 AI profiles × 2 games = **32 real games** over 16 matrix jobs (at most 8 jobs concurrently). Each job runs its JVMs sequentially to prevent memory overcommit on a small runner.
3. Every Forge game is isolated in its own JVM, uses `-s` RNG seed and `-a` AI profile assignments, and writes logs and machine-readable outcomes.
4. `scripts/aggregate_batch.py` merges jobs, removes failed/clock-censored matches, and reports win-rate Wilson intervals, sample size, and profile-specific counters.
5. A pinned, **optional** `scripts/patch_forge_incubate.py` modifies a **copy** of Forge's `SpellApiToAi.class`: it maps `ApiType.Incubate` from its previously missing handler (implicit CannotPlayAi) to generic `AlwaysPlayAi`. It must pass a standalone pilot and statistical A/B tests before adoption. This does not add sophisticated cost/target evaluation or strategic sacrifice timing.

## AI quality roadmap (not implemented yet)

- Track legal options and chosen actions from live game state instead of inferring errors from missing log lines.
- Add a dedicated `IncubateAi` rather than a generic always-play fallback: costs, resource preservation, threats, future transforms, counter-based payoffs.
- Add Phyrexian-per-turn death optimization: understand how many end-step triggers remain, mana availability, board impact, opponent interaction, and whether to sacrifice a token now vs retain it.
- Model opponent threats, targeted removal and threat evaluation in multiplayer, combat politics, and safe sacrifice sequencing.
- Benchmark stock vs altered AI with matched seat/pod/seed designs, explicit low-confidence ratings, and holdout opponents. Never infer superiority from a small favorable score.

## Limits and fair evaluation

- Existing Forge profiles Default, Cautious, Experimental, Reckless are *different heuristics*, not increasing expertise levels.
- The matched Forge seed improves traceability but doesn't guarantee identical RNG draws once AI actions diverge.
- Any Game Changer / bracket / color identity verification must be performed independently; deck-list structural validation alone isn't proof.
- GitHub Actions minute quotas and bandwidth are finite. Scaling from 32 to hundreds of games may incur usage costs; run small pilots before larger workflows.
- Multiple queued processes on one shared runner do NOT imply true speedup. Matrix jobs are the parallelization unit, and each hosts a separate Forge JVM.

## Existing workflows

- [parallel benchmark](../.github/workflows/parallel-benchmark.yml)
- [quality log audit](../.github/workflows/ai-audit.yml)
- [isolated Incubate patch pilot](../.github/workflows/incubate-patch-test.yml)

## Incubate AI handler first pilot

The optional bytecode patch compiled and eliminated `No AI assigned for API: Incubate` in one four-player smoke game. However, that game hit the 360-second clock and was censored, so **the patch is NOT promoted to the baseline**. Removing an API warning is insufficient evidence of improved decisions. Further evaluation must compare complete-game rates, tactical decisions, and win performance before adoption.
