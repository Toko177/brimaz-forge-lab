package forge.ai;

/** Pure tactical-invariant tests; no human gameplay traces are treated as truth. */
public final class MultiOpponentDefensePolicyChecks {
    private MultiOpponentDefensePolicyChecks() {}

    static void ok(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
    }

    public static void main(String[] args) {
        // Life-based lethal threat (opponent 1).
        ok(MultiOpponentDefensePolicy.visibleLethal(
                12, 12, 0, 0, 0, 0, false, false, false),
                "Open 12 combat life damage must be recognized as lethal");
        ok(!MultiOpponentDefensePolicy.visibleLethal(
                12, 11, 0, 0, 0, 0, false, false, false),
                "Below lethal life pressure must not be treated as an elimination");
        ok(!MultiOpponentDefensePolicy.visibleLethal(
                12, 12, 0, 0, 0, 0, true, false, false),
                "Cannot-lose-at-zero must prevent life-lethal reserve");

        // Poison (opponent 2), independent of ordinary life.
        ok(MultiOpponentDefensePolicy.visibleLethal(
                40, 0, 8, 2, 0, 0, false, false, false),
                "Existing eight poison counters and two infect damage must be lethal");
        ok(!MultiOpponentDefensePolicy.visibleLethal(
                40, 0, 8, 1, 0, 0, false, false, false),
                "Nine poison total is below the normal threshold");
        ok(!MultiOpponentDefensePolicy.visibleLethal(
                40, 0, 8, 2, 0, 0, false, true, false),
                "Poison-specific loss prevention must be respected");

        // Commander damage (opponent 3), tracked per commander.
        ok(MultiOpponentDefensePolicy.visibleLethal(
                40, 0, 0, 0, 18, 3, false, false, false),
                "Three combat damage from the commander at eighteen is lethal");
        ok(!MultiOpponentDefensePolicy.visibleLethal(
                40, 0, 0, 0, 18, 2, false, false, false),
                "Twenty commander damage cannot be classified as lethal");
        ok(!MultiOpponentDefensePolicy.visibleLethal(
                40, 0, 0, 0, 18, 3, false, false, true),
                "Commander-specific loss prevention must be respected");

        ok(MultiOpponentDefensePolicy.requiredBlockers(0, 2, true, 3) == 2,
                "Keep up to two blockers for two threatening attackers");
        ok(MultiOpponentDefensePolicy.requiredBlockers(1, 2, true, 2) == 1,
                "Do not count existing legal defensive options as attack candidates");
        ok(MultiOpponentDefensePolicy.requiredBlockers(2, 2, true, 4) == 0,
                "Preserve the original game plan with sufficient held-back blockers");
        ok(MultiOpponentDefensePolicy.requiredBlockers(0, 3, false, 4) == 0,
                "No reserve when no visible loss threshold is reached");
        ok(MultiOpponentDefensePolicy.requiredBlockers(0, 2, true, 1) == 1,
                "Never reserve more legal candidates than are available");

        for (int seat=1; seat<=4; seat++) {
            ok(MultiOpponentDefensePolicy.requiredBlockers(0, seat, true, 2)
                    == Math.min(2, seat),
                    "Invariant must apply consistently to each of four seats");
        }
        System.out.println("FOUR_AI_V16_DEFENSE_INVARIANTS_PASS checks=18");
    }
}
