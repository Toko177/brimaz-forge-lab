# Brimaz AI policy V2 — release candidate (experimental)

## Why V2

The V1 policy (`patch_forge_brimaz.py`) passed Java compilation and completed real multiplayer Forge games, but it made only three explicit planner proposals in two games over 16 games and **did not win**. Its matched-seed comparison with stock Forge showed no demonstrated increase in trigger count or win performance.

V2 is an attempt to increase **legal relevant decisions**, not to claim stronger play without testing.

## More legal outlet options

V2 adds to V1:
- **Throne of Geth**: tap and sacrifice an artifact to proliferate immediately; a Phyrexian death may also enable Brimaz's following end-step proliferate.
- **Spawning Pit**: sacrifice a creature for a charge counter; both the Pit and other counters can benefit from later proliferation.

This is in addition to **Arcbound Ravager** and **Bartolomé del Presidio**, the two V1 free sacrifice/counter outlets.

Only the recognized activated abilities are added, never arbitrary non-validated outlets. Stock Forge marks Spawning Pit `AI:RemoveDeck:All` and Throne of Geth `AI:RemoveDeck:Random`; the V2 code conditionally bypasses that exclusion only when an immediate eligible Brimaz play is found. **V2 does not yet teach the AI to proactively cast Spawning Pit from hand or to convert its charge counters into creatures.** Those are separate limitations.

## Adaptive sacrifice cost

- V1 allowed a Phyrexian creature token with net power <= 2.
- V2 allows net power up to 2, 3, or 4 depending on how many other controlled permanents already hold counters (the cap rises only with substantial counter synergy).
- No non-token creature is deliberately sacrificed by this heuristic.
- No action after the end step has already begun is counted as setting up that step's Brimaz trigger.
- The planner stops proposing further sacrifices when Forge's real turn-history expression shows that a qualifying Phyrexian already died.

## Technical acceptance

- Code: `scripts/patch_forge_brimaz_v2.py`
- Smoke CI: `brimaz-v2-test.yml`
- 16-game parallel A/B: `brimaz-v2-benchmark.yml`
- Matched-seed diffs: `brimaz-v2-comparison.yml`
- Behavioral log audit: `brimaz-v2-ai-audit.yml`

The smoke test run `37960596551` **compiled V2 and finished one real four-player Commander game naturally**. The AI's strategic strength remains unproven pending repeated comparisons.

### Measurement caveat

`BRIMAZ_PLANNER` indicates a chosen action proposal, not independent proof that the sacrifice resolved and enabled an end-step trigger. Game logs need to confirm the actual activation, cost payment, and subsequent death-history trigger. Seed matching does not control later draws once actions diverge.

## Next engineering gap

Create a real board-state evaluator for sacrifice actions, including:
- value of the token being lost (power, abilities, engine/defensive importance)
- positive friendly counter permanents available for proliferation
- surviving opponents and threat levels
- how many future opponent end steps the commander is expected to survive
- opponent removal or response risks
- enabling Spawning Pit creation and spending of charge counters in a controlled manner.

Do not promote V2 until it shows either clearly improved decisions in tactical tests or a reproducible benefit over stock Forge.
