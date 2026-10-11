package forge.game.card;

/** Synthetic only: validate the closed set of exactly five literal cases.
 * The real four-player JVM shadow audit checks actual Card semantics.
 */
public final class CardPropertyLiteralFastPathChecks {
    private static int n;
    private static void check(boolean value, String why) {
        n++;
        if (!value) throw new AssertionError(why);
    }
    public static void main(String[]args) {
        check(CardPropertyLiteralFastPath.ENABLED,"Opt-in policy must be active");
        check(CardPropertyLiteralFastPath.supports("IsCommander"),"Commander");
        check(CardPropertyLiteralFastPath.supports("Self"),"Self");
        check(CardPropertyLiteralFastPath.supports("YouCtrl"),"Controller");
        check(CardPropertyLiteralFastPath.supports("YouOwn"),"Owner");
        check(CardPropertyLiteralFastPath.supports("Other"),"Other");
        for (String x:new String[]{"StrictlySelf","OtherCreature","YouCtrlX","YouOwnABC",
            "NotIsCommander","phasedOutSelf","Saproling","", "IsCommander ", "IsCommander2"}) {
            check(!CardPropertyLiteralFastPath.supports(x),"Reject dynamic/prefix property "+x);
        }
        check(!CardPropertyLiteralFastPath.supports(null),"Null property");
        check(CardPropertyLiteralFastPath.evaluate(null,"random",null,null,null)==null,
              "Unknown property must always fall back to original rule logic");
        // A source-identical comparator is supposed to HALT at the first
        // genuine mismatched boolean, not silently hide a rule regression.
        if (CardPropertyLiteralFastPath.SHADOW) {
            CardPropertyLiteralFastPath.verify(true,true,"Self");
            boolean failed=false;
            try {
                CardPropertyLiteralFastPath.verify(true,false,"Self");
            } catch (IllegalStateException ex) {
                failed=ex.getMessage().contains("RULE_EQUIVALENCE_FAILURE");
            }
            check(failed,"Any mismatching real game result must terminate validation");
        }
        System.out.println("FOUR_AI_V30_FIVE_EXACT_PROPERTY_LITERAL_TESTS_PASS checks="+n);
    }
}
