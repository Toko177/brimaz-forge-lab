package forge.ai;

/** Pure unit tests for the opt-in Commander free mulligan heuristic. */
public final class BrimazV9MulliganChecks {
    private static void check(String label, boolean ok) {
        if (!ok) throw new AssertionError(label);
        System.out.println("V9_MULLIGAN_OK " + label);
    }

    public static void main(String[] args) {
        check("two lands no ramp high curve during free mulligan is rejected",
            BrimazMulliganPolicy.wantFreeMulligan(2, 0, 0, 3, 0));
        check("two lands with Sol Ring is kept",
            !BrimazMulliganPolicy.wantFreeMulligan(2, 1, 0, 3, 0));
        check("two lands with early draw is kept",
            !BrimazMulliganPolicy.wantFreeMulligan(2, 0, 1, 3, 0));
        check("two lands low curve is kept",
            !BrimazMulliganPolicy.wantFreeMulligan(2, 0, 0, 1, 0));
        check("three available land drops including MDFC are kept",
            !BrimazMulliganPolicy.wantFreeMulligan(3, 0, 0, 3, 0));
        check("four lands are kept",
            !BrimazMulliganPolicy.wantFreeMulligan(4, 0, 0, 3, 0));
        check("already mulliganed costs a card so no override",
            !BrimazMulliganPolicy.wantFreeMulligan(2, 0, 0, 3, 1));
        check("zero lands use stock Forge mulligan logic",
            !BrimazMulliganPolicy.wantFreeMulligan(0, 0, 0, 3, 0));
        check("one land uses stock Forge mulligan logic",
            !BrimazMulliganPolicy.wantFreeMulligan(1, 0, 0, 3, 0));
        System.out.println("BRIMAZ_V9_MULLIGAN_TESTS_OK");
    }
}