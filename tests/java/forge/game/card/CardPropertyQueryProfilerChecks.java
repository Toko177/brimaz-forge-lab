package forge.game.card;

/** Synthetic property-name counter smoke only; not a real Magic game. */
public final class CardPropertyQueryProfilerChecks {
    public static void main(String[]args) {
        if (!CardPropertyQueryProfiler.ENABLED) {
            throw new AssertionError("This test requires opt-in -Dbrimaz.profilePropertyQueries=true");
        }
        long start=CardPropertyQueryProfiler.total();
        long creatures=CardPropertyQueryProfiler.count("Creature");
        CardPropertyQueryProfiler.observe("Creature");
        CardPropertyQueryProfiler.observe("Creature");
        CardPropertyQueryProfiler.observe("OppCtrl");
        CardPropertyQueryProfiler.observe(null);
        if (CardPropertyQueryProfiler.total()!=start+4)
            throw new AssertionError("All observed predicate calls should be counted");
        if (CardPropertyQueryProfiler.count("Creature")!=creatures+2)
            throw new AssertionError("Repeated predicate keyword must be counted without changing anything");
        if (CardPropertyQueryProfiler.count("OppCtrl")<1)
            throw new AssertionError("Different rules keywords must be tracked separately");
        if (CardPropertyQueryProfiler.count("<null>")<1)
            throw new AssertionError("Unknown property labels must be diagnostically safe");
        System.out.println("FOUR_AI_PROPERTY_PROFILER_TESTS_PASS checks=4");
    }
}
