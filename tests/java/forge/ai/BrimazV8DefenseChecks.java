package forge.ai;

/** Deterministic checks for V8 tactical guardrails; no altered MTG rules. */
public final class BrimazV8DefenseChecks {
    private static void check(String label, boolean predicate) {
        if (!predicate) throw new AssertionError(label);
        System.out.println("V8_DEFENSE_OK " + label);
    }

    private static boolean score(int counters, int life, int opponentPower, int blockers) {
        return BrimazTurnPlanner.shouldTransformForDefense(counters, life, opponentPower, blockers);
    }

    public static void main(String[] args) {
        check("low life + 2-counter token + threatening enemy + no blocker",
            score(2, 15, 4, 0));
        check("avoid transforming 1-counter token", !score(1, 10, 8, 0));
        check("preserve mana when not threatened", !score(3, 40, 3, 0));
        check("no creature pressure means no transform", !score(4, 12, 0, 0));
        check("enough blockers means no forced transform", !score(4, 12, 6, 3));
        check("large lethal opponent remains urgent", score(2, 25, 10, 1));
        check("only 1 blocker left is vulnerable", score(2, 20, 3, 1));
        check("conservative versus high life", !score(2, 27, 4, 0));
        System.out.println("BRIMAZ_V8_DEFENSE_TESTS_OK");
    }
}