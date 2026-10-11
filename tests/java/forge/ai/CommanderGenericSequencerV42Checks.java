package forge.ai;

/** Exact single-seat authorization, pure tests: never fabricated games. */
public final class CommanderGenericSequencerV42Checks {
    private static int checks=0;
    private static void ok(boolean yes,String message) {
        checks++;
        if(!yes)throw new AssertionError(message);
    }
    public static void main(String[] args) {
        ok(CommanderGenericSequencerV42.seatEligible(
            "Ai(1)-EDH Amalia","1"),"target seat 1, unrelated deck");
        ok(CommanderGenericSequencerV42.seatEligible(
            "Ai(1)-Brimaz V3","1"),"target seat 1, commander agnostic");
        ok(!CommanderGenericSequencerV42.seatEligible(
            "Ai(2)-EDH Urza","1"),"non-target opponent blocked");
        ok(!CommanderGenericSequencerV42.seatEligible(
            "Ai(4)-EDH Amalia","1"),"same deck name at wrong seat blocked");
        ok(!CommanderGenericSequencerV42.seatEligible(
            "Ai(1)-EDH Amalia","5"),"invalid configured seat blocked");
        ok(!CommanderGenericSequencerV42.seatEligible(
            "Ai(1)-EDH Amalia","12"),"invalid multi-digit seat blocked");
        ok(!CommanderGenericSequencerV42.seatEligible(
            "Ai(1)-EDH Amalia",""),"empty configuration blocked");
        ok(!CommanderGenericSequencerV42.seatEligible(
            "Ai(1)-","1"),"missing display name blocked");
        ok(!CommanderGenericSequencerV42.seatEligible(
            null,"1"),"null pilot fails closed");
        ok(CommanderGenericSequencerV42.seatEligible(
            "Ai(4)-EDH Urza",null),"V42 historical all-seat fallback");
        System.out.println("V43_SINGLE_SEAT_ISOLATION_PASS checks="+checks
            +" realGamesClaimed=0");
    }
}
