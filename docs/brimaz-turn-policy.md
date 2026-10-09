# Brimaz Turn Planner — policy V1 (experimental)

Engine: Forge 2.0.15. Implemented in `scripts/patch_forge_brimaz.py`.

## Objective

Rather than asking a generic AI profile to somehow learn to sacrifice, intercept the **actual AI move selection** in `forge.ai.AiController`, using the **live game state** to identify a turn-sensitive Brimaz opportunity.

## Rules and decision logic

Brimaz's second triggered ability checks whether a Phyrexian controlled by the player died *earlier that same turn*, and triggers at the **beginning** of **each** end step (including opponents').

The policy considers a proactive sacrifice only if all conditions hold:

1. A battlefield Brimaz is under that AI's control.
2. It is an **opponent's second main phase**, before the beginning of the end step; the stack is empty.
3. The official Forge `Count$ThisTurnEntered_Graveyard_from_Battlefield_Phyrexian.YouCtrl` expression still evaluates to zero.
4. An activated counter-producing sacrifice outlet is already available: specifically Arcbound Ravager or Bartolomé del Presidio.
5. That ability has exactly one cost component, a sacrifice cost; it is legal now and affordable.
6. At least one compatible controlled **Phyrexian creature token** can legally be sacrificed, and its net power is 2 or lower.
7. Its sacrifice leaves Brimaz and all non-token creatures untouched.

When selecting the cost payment, the patch prefers the smallest eligible Phyrexian token. After the first qualifying sacrifice the Forge death counter becomes positive, so the policy does not deliberately sacrifice further tokens solely for that turn's Brimaz end-step trigger.

The additional +1/+1 counter on the outlet and proliferate at end step are the explicit payoff. **This V1 heuristic does not yet quantify opportunity cost or evaluate all counter synergies.**

## What it changes

- `AiController.getSpellAbilityToPlay()`: an **optional**, high-priority decision in the narrow allowed window.
- `AiController.chooseSacrificeType()`: selects an eligible Phyrexian token for the activated ability's mandatory sacrifice cost.
- New class `forge.ai.BrimazTurnPlanner`: policy conditions and choice.

No Magic rules, card scripts or hidden game state were modified. The source is fetched from the exact Forge 2.0.15 release, modified and compiled against its executable JAR. Every patched job uses an isolated runner. A stock Forge JAR is the control arm.

## Validation criteria

1. Compilation of patched AiController and BrimazTurnPlanner succeeds against actual Forge 2.0.15.
2. A real four-player mixed Commander game finishes naturally, not because of clock cutoff.
3. The log records `BRIMAZ_PLANNER:` when the new decision fires.
4. Outcomes and state traces are compared against stock Forge on exactly the same pods, seats, starting seed values, and opponents' Default AI profiles.
5. No wins are attributed to clock-censored games.
6. A patch is **not** promoted solely because its JVM launches or because it suppresses a warning.

**Current pilot:** compilation and one naturally completed mixed Commander game confirmed by GitHub workflow `37958831690`; planner was not activated during this specific game. More games needed to observe the tactical feature in real play.

## Proposed V2, not yet implemented

- Proper candidate sacrifice expected-value model incorporating token power, number of friendly permanents with counters, +1/+1 gains on outlet and the expected value of extra proliferate.
- Respect commander tax, multiplayer risk and remaining players' turns.
- Differentiate combat rescue sacrifices from proactive engine sacrifices.
- Expand beyond the two known outlets after explicitly testing each cost's payment logic.
- Test targeted tactical board states to prove that the policy triggers only with legal beneficial situations.
- Review the generic `Incubate` AI handler independently; the earlier always-play fallback suppressed warnings but did not yield a completed benchmark game.

## Performance

Use `brimaz-policy-benchmark.yml`: eight isolated Github Actions runners, two pods × four seat rotations, two independent seeded real games per runner, 16 games total, bounded concurrency and per-game logs. A patched game uses `--policy-label BrimazPlannerV1`. Stock comparison from the previously executed baseline contains 31 naturally completed games / 32 scheduled across two profiles; only the **Default** subsets are direct controls.
