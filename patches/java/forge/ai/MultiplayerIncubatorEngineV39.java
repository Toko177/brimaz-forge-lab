package forge.ai;

/**
 * V39 observable, turn-local incubator economics.
 * Pure helpers; no invented Magic rules and no private-zone inspection.
 */
public final class MultiplayerIncubatorEngineV39 {
    private MultiplayerIncubatorEngineV39() {}

    /**
     * Same conservative payoff accounting used by the historical Brimaz
     * sacrifice scorer: proliferate existing countered permanents (+3 each)
     * and the outlet's minimum immediate value (+3), against the loss of
     * a token valued at 2+3*power. Death triggers and poison are NOT assumed.
     * Exclude the candidate token itself from otherCounteredPermanents.
     */
    public static int minimumVisibleNetEngineValue(int incubatorSize,
                int otherCounteredPermanents, boolean commanderPresent,
                boolean hasValidSacrificeOutlet) {
        if(incubatorSize<2 || incubatorSize>4 || otherCounteredPermanents<0
            || !commanderPresent || !hasValidSacrificeOutlet)return 0;
        return 3*otherCounteredPermanents+3-(2+3*incubatorSize);
    }

    public static boolean shouldPrepareSacrificeCreature(int incubatorSize,
            int otherCounteredPermanents, boolean commanderPresent,
            boolean hasValidSacrificeOutlet) {
        return minimumVisibleNetEngineValue(incubatorSize,
                   otherCounteredPermanents,commanderPresent,
                   hasValidSacrificeOutlet)>0;
    }

    /** Our own real hand has an actually payable ramp spell. Do not
     * preempt Forge's mana acceleration just to flip an idle artifact,
     * unless the board threat urgently requires another blocker.
     */
    public static boolean shouldPreserveManaForRamp(boolean payableRamp,
           int life,int largestOppCreatureBoardPower,int readyBlockers) {
        if(!payableRamp || life<=0 || largestOppCreatureBoardPower<0
              || readyBlockers<0)return false;
        boolean urgent=readyBlockers<=1 &&
                 largestOppCreatureBoardPower>=Math.max(5,life-5);
        return !urgent;
    }

    /** Budgeted visible decision only. Aggressive transformation for
     * a real engine is separately scored from a large creature for combat. */
    public static int visibleTransformationPriority(int incubatorSize,
             boolean tempoWorthwhile,int engineBenefit) {
        if(incubatorSize<2 || (!tempoWorthwhile && engineBenefit<=0))return -1;
        if(engineBenefit>0)return 100+Math.min(40,engineBenefit);
        return incubatorSize;
    }
}
