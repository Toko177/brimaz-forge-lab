# Brimaz tactical AI V3 — controlled experiment

Engine: Forge 2.0.15 (exact release, unmodified rules implementation).

## Implemented

- Actual Java AI decision patch: [patch_forge_brimaz_v3.py](../scripts/patch_forge_brimaz_v3.py).
- Compile and deterministic assertions: [brimaz-v3-validation.yml](../.github/workflows/brimaz-v3-validation.yml) and [BrimazV3ScoringChecks.java](../tests/java/forge/ai/BrimazV3ScoringChecks.java).
- Two independent four-player matchup pods, four seat rotations, two seeds per rotation, eight parallel CI runners: [brimaz-v3-benchmark.yml](../.github/workflows/brimaz-v3-benchmark.yml).
- Matched game reports against stock Forge, V1 and V2: [brimaz-v3-comparison.yml](../.github/workflows/brimaz-v3-comparison.yml).
- Game phase forensic audit: [brimaz-v3-ai-audit.yml](../.github/workflows/brimaz-v3-ai-audit.yml).

## Decisions evaluated using the **actual battlefield**

Unlike V1/V2's permissive rule, V3 scores each eligible sacrifice outlet and Phyrexian token:

- Benefit from friendly permanents with counters (excluding the token to sacrifice).
- Benefits from counters actually present on poisoned opponents and creatures with negative counters.
- Additional immediate payoff of `Throne of Geth` (an additional proliferate), `Spawning Pit` or a +1/+1 counter outlet.
- Opportunity cost of losing a token proportional to its current power.
- Risk of weakening defense when life is low against a large opposing creature.
- Legal costs, activation phases and real Forge turn-history expression before choosing any ability.
- **Own second main phase as well as the opponent's second main phase:** Brimaz also triggers at the beginning of *your own* end step.
- V3 never deliberately sacrifices Brimaz, non-token creatures, or a Phyrexian token over power four.

Potential outlets: Arcbound Ravager, Bartolomé del Presidio, Spawning Pit, Throne of Geth. The patch is not a general combo solver, does not evaluate opponent hands and does not explore a decision tree. Opponent-threat scoring uses visible information only.

## Confirmed tests

- Java patch compiled against Forge 2.0.15.
- All seven deterministic scoring assertions passed in CI run `37962352232`.
- One real four-AI mixed Commander game completed naturally within 360 seconds in the same CI run. Radha won that pilot.

## Limitations / next steps

- The heuristic's numerical weights are provisional; they are not calibrated on expert play traces.
- Test harness assertions only validate scoring for representative inputs, not full in-game priority and payment sequencing.
- `BRIMAZ_PLANNER:` indicates an AI proposal. Actual activation, sacrifice resolution, and end-step trigger must be verified separately in Forge transcripts.
- End-step-trigger counts must be extracted from end-step phases, not confused with the separate ability that incubates on casting Phyrexian / artifact creatures.
- This V3 policy improves how **Brimaz's pilot** considers a small subset of tactical decisions. The other three players still use Forge's normal heuristics. The full lookahead simulator in Forge 2.0.15 still has explicit multiplayer TODOs, and **an authentic 4-player multi-agent search has not yet been implemented**.
- Small numbers of games do not establish a statistical win-rate advantage; the experiment's acceptance standard is improvement in observed actions and outcomes across repeated valid games.

## Engineering next steps

1. Add instrumentation for each legal opportunity: eligible tokens, engine, opponent turn, expected proliferation payoff, rejected candidates and reason.
2. Validate game-state fixtures, including states where the AI **must not** sacrifice.
3. Extend controlled actions to Phyrexian Tower, Ashnod's Altar, Phyrexian Altar and Yawgmoth, whose *mana/other costs* require careful opportunity-cost and response analysis.
4. Investigate card AI limitations involving Incubate and Spawning Pit's charge-counter token ability without blindly mapping `Incubate` to an always-play handler.
5. Prototype true four-player evaluation on copies of the Forge game state with explicit legal opponent actions and bounded search; benchmark CPU, timeouts, and decision quality.

## Completed 16-game V3 experiment and audit

Date: 2026-10-09.

- 16 independent Forge games, 15 naturally complete, one clock-censored; **0 wins for Brimaz**.
- V3 generated four proposals across three games, using Arcbound Ravager.
- The original action-audit script wrongly searched for an activation after each real-time `System.out` proposal, while Forge **buffers its game log and prints it later**.
- Corrected audit `scripts/audit_planner_resolution.py` groups Forge entries by the exact in-game turn number. It verified that **all four proposals had a corresponding Arcbound Ravager activation on that turn**, and a Brimaz end-step trigger was logged on each of those four turns. This is strong evidence the hook is really integrated; it does **not** prove no other death could have triggered Brimaz.
- Of all V3 game transcripts, 17 Brimaz end-step triggers and 45 Incubator transforms (including censored games) were found. Comparisons against stock and V1/V2 were run on matched pods/seats/seeds; no win-rate advantage demonstrated.
- Known limitation: user-defined live diagnostic log records are not in chronological order with the buffered match log. Use in-game turn IDs when correlating actions; never assume adjacent log lines are temporal neighbors.

Runs:
- [Java tests and actual match](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37962352232)
- [16-game campaign](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37962437566)
- [True phase audit](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37963424131)
- [Turn-indexed correction](https://github.com/Toko177/brimaz-forge-lab/actions/runs/37963707613)
