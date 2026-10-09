package forge.ai;
/** Self-checks V3's deterministic sacrifice scoring, no random mocks. */
public final class BrimazV3ScoringChecks {
    private static void test(String name, boolean ok) {
        if (!ok) throw new AssertionError(name);
        System.out.println("PASS " + name);
    }
    public static void main(String[] args) {
        int noCounters = BrimazTurnPlanner.scoreHypothetical(2, 0, 0, 0, 40, 0, "Arcbound Ravager");
        int withCounters = BrimazTurnPlanner.scoreHypothetical(1, 3, 0, 0, 40, 0, "Arcbound Ravager");
        int danger = BrimazTurnPlanner.scoreHypothetical(1, 3, 0, 0, 8, 6, "Arcbound Ravager");
        int throne = BrimazTurnPlanner.scoreHypothetical(1, 3, 0, 0, 40, 0, "Throne of Geth");
        int pit = BrimazTurnPlanner.scoreHypothetical(1, 3, 0, 0, 40, 0, "Spawning Pit");
        test("no counters: don't lose a 2-power token for no benefit", noCounters <= 0);
        test("three friendly counter permanents: sacrifice low-value token", withCounters > 0);
        test("dangerous opponent board: preserve last defender", danger < withCounters);
        test("Throne immediate proliferation more valuable than counter-only outlet", throne > withCounters);
        test("Spawning Pit produces a charge-counter payoff", pit > 0);
        int opponentPoison = BrimazTurnPlanner.scoreHypothetical(1, 0, 1, 0, 40, 0, "Throne of Geth");
        test("opponent poison increases value of proliferate", opponentPoison > 0);
        int oversized = BrimazTurnPlanner.scoreHypothetical(4, 1, 0, 0, 40, 0, "Arcbound Ravager");
        test("don't sacrifice 4-power Phyrexian with low synergy", oversized <= 0);
        System.out.println("BRIMAZ_V3_SCORING_TESTS_OK");
    }
}
