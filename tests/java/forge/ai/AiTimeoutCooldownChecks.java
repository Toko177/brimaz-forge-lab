package forge.ai;

public final class AiTimeoutCooldownChecks {
    private static int n=0;
    private static void check(boolean cond,String why) {
        n++;
        if(!cond) throw new AssertionError(why);
    }
    public static void main(String[]args) {
        AiTimeoutCooldownPolicy a=new AiTimeoutCooldownPolicy();
        AiTimeoutCooldownPolicy b=new AiTimeoutCooldownPolicy();
        check(!a.shouldSkip(123,10),"No unexplained initial exclusion");
        check(a.recordTimeout(123,10)==14,"First repeated-slow card gets four turns");
        check(a.shouldSkip(123,10),"Exclude at observed timeout turn");
        check(a.shouldSkip(123,14),"Inclusive end of quarantine");
        check(!a.shouldSkip(123,15),"Automatic expiry allows card again");
        check(a.strikeCount(123)==1,"Timeout provenance retained");
        check(a.recordTimeout(123,15)==23,"Second timeout increases quarantine to 8 turns");
        check(a.recordTimeout(123,25)==37,"Third timeout increases quarantine to 12 turns");
        check(a.recordTimeout(123,39)==55,"Fourth timeout capped at 16 turns");
        check(a.recordTimeout(123,60)==76,"Subsequent timeouts stay capped at 16");
        check(!a.shouldSkip(123,77),"No permanent blacklisting");
        check(!a.shouldSkip(124,65),"Different card never excluded");
        check(!b.shouldSkip(123,65),"Other AI seat never inherits cooldown");
        check(a.recordTimeout(-1,10)==-1,"Unknown card is never blocked");
        check(!a.shouldSkip(-1,10),"Unknown card cannot be skipped");
        check(a.recordTimeout(124,100)==104,"Second card has independent TTL");
        check(a.shouldSkip(124,102),"Second card cooldown valid");
        check(!a.shouldSkip(124,105),"Second card independently expires");
        System.out.println("FOUR_AI_TIMEOUT_COOLDOWN_TESTS_PASS checks="+n);
    }
}
