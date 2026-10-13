package forge.ai;

/** 18 falsifiable synthetic scenarios, NOT simulated Commander victories. */
public final class MultiplayerIncubatorEngineV39Checks {
    private static int n=0;
    private static void ok(boolean x,String label) {
        n++;if(!x)throw new AssertionError(label);
    }
    public static void main(String[] unused) {
        var v=MultiplayerIncubatorEngineV39.class;
        ok(MultiplayerIncubatorEngineV39.minimumVisibleNetEngineValue(
             2,2,true,true)>0,"2/2 incubator + 2 distinct counter payoffs");
        ok(MultiplayerIncubatorEngineV39.minimumVisibleNetEngineValue(
             2,1,true,true)<=0,"1 counter target not enough; no free proliferate");
        ok(MultiplayerIncubatorEngineV39.minimumVisibleNetEngineValue(
             3,2,true,true)<=0,"3/3 requires more counters than 2/2");
        ok(MultiplayerIncubatorEngineV39.minimumVisibleNetEngineValue(
             3,3,true,true)>0,"3 real counter payoffs with real outlet");
        ok(MultiplayerIncubatorEngineV39.minimumVisibleNetEngineValue(
             4,3,true,true)<=0,"do not sacrifice valuable 4/4 for tiny payoff");
        ok(!MultiplayerIncubatorEngineV39.shouldPrepareSacrificeCreature(
             5,10,true,true),"5/5 should not be prepared as a cheap sacrifice");
        ok(!MultiplayerIncubatorEngineV39.shouldPrepareSacrificeCreature(
             2,10,false,true),"no commander death trigger");
        ok(!MultiplayerIncubatorEngineV39.shouldPrepareSacrificeCreature(
             2,10,true,false),"no real sacrifice outlet");
        ok(!MultiplayerIncubatorEngineV39.shouldPrepareSacrificeCreature(
             1,10,true,true),"tiny incubator not sacrificed");
        ok(!MultiplayerIncubatorEngineV39.shouldPrepareSacrificeCreature(
             2,-1,true,true),"invalid counters fail closed");
        ok(MultiplayerIncubatorEngineV39.shouldPreserveManaForRamp(
             true,40,6,2),"payable real ramp takes precedence in safe state");
        ok(!MultiplayerIncubatorEngineV39.shouldPreserveManaForRamp(
             true,7,8,0),"near-lethal board prioritizes blocker");
        ok(!MultiplayerIncubatorEngineV39.shouldPreserveManaForRamp(
             false,40,6,2),"phantom ramp does not block transform");
        ok(MultiplayerIncubatorEngineV39.visibleTransformationPriority(
             2,false,1)>MultiplayerIncubatorEngineV39.visibleTransformationPriority(
             5,true,0),"profitable sacrifice support outranks speculative 5/5 tempo");
        ok(MultiplayerIncubatorEngineV39.visibleTransformationPriority(
             5,true,0)==5,"size five is useful creature in safe board");
        ok(MultiplayerIncubatorEngineV39.visibleTransformationPriority(
             3,false,0)==-1,"no payoff does not override Forge");
        ok(MultiplayerIncubatorEngineV39.visibleTransformationPriority(
             2,true,0)==2,"defensive 2/2 valid when needed");
        ok(MultiplayerIncubatorEngineV39.visibleTransformationPriority(
             0,true,100)==-1,"zero counter incubator never transformed");
        System.out.println("FOUR_AI_V39_ENGINE_SYNTHETIC_PASS checks="+n
              +" realGamesClaimed=0");
    }
}
