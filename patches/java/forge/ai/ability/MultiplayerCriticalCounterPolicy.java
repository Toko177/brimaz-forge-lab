package forge.ai.ability;

import forge.game.ability.ApiType;
import forge.game.ability.AbilityUtils;
import forge.game.card.Card;
import forge.game.keyword.Keyword;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;

/** Public, targeted commander protection for any of four Commander AI seats.
 *
 * Only called AFTER standard Forge CounterAi validates stack, legal counter
 * target and affordability. Prevents a profile CMC/chance heuristic from
 * making us ignore known targeted removal of our own commander.
 * No peek into opponents' hands or private choices, no ability to
 * counter uncounterable spells, and no bypass of costs or targeting.
 */
public final class MultiplayerCriticalCounterPolicy {
    private MultiplayerCriticalCounterPolicy() {}

    public static boolean targetedCommanderRemoval(boolean hostile,
                                                   boolean ourCommander,
                                                   boolean targetedSpell,
                                                   boolean destructiveApi,
                                                   boolean destroyOnly,
                                                   boolean indestructible) {
        return hostile && ourCommander && targetedSpell && destructiveApi
                && !(destroyOnly && indestructible);
    }


    /**
     * This recognizes an already-on-stack, public targeted damage/life-loss
     * spell with a fixed Forge-computable value that would eliminate us.
     * No speculative X, untargeted wipes, infect assumptions or hidden hands.
     */
    public static boolean imminentLifeLoss(boolean hostile, boolean targetsUs,
                                           boolean protectedFromLifeLoss,
                                           int life, int publicDamage) {
        return hostile && targetsUs && !protectedFromLifeLoss
                && life > 0 && publicDamage >= life;
    }

    public static boolean isLethalTargetedLifeSpell(final Player ai, final SpellAbility hostile) {
        if (ai == null || hostile == null || !hostile.isSpell()
                || hostile.getActivatingPlayer() == null
                || !hostile.getActivatingPlayer().isOpponentOf(ai)
                || !hostile.usesTargeting() || !hostile.isTargeting(ai)
                || ai.cantLoseForZeroOrLessLife()
                || hostile.getHostCard() == null) return false;
        final ApiType api=hostile.getApi();
        String amountKey;
        if (api == ApiType.DealDamage) {
            amountKey = "NumDmg";
        } else if (api == ApiType.LoseLife) {
            amountKey = "LifeAmount";
        } else {
            return false;
        }
        if (!hostile.hasParam(amountKey)) return false;
        String amount=hostile.getParam(amountKey);
        // Unknown dynamic values and value-of-X attacks require actual
        // spell resolution to evaluate; don't force a counter from a guess.
        if (!amount.matches("[0-9]{1,5}")) return false;
        int publicDamage=AbilityUtils.calculateAmount(hostile.getHostCard(),amount,hostile);
        return imminentLifeLoss(true,true,false,ai.getLife(),publicDamage);
    }

    public static boolean shouldPreventPublicLethal(final Player ai, final SpellAbility hostile) {
        return isCommanderRemovalThreat(ai,hostile)
                || isLethalTargetedLifeSpell(ai,hostile);
    }

    public static boolean isCommanderRemovalThreat(final Player ai, final SpellAbility hostile) {
        if (ai == null || hostile == null || !hostile.isSpell()
                || hostile.getActivatingPlayer() == null
                || !hostile.getActivatingPlayer().isOpponentOf(ai)
                || !hostile.usesTargeting()) return false;
        final Card target = hostile.getTargetCard();
        if (target == null || target.getController() != ai || !target.isCommander()) {
            return false;
        }
        final ApiType api = hostile.getApi();
        boolean destroy=api == ApiType.Destroy;
        boolean removes=destroy || api == ApiType.ChangeZone || api == ApiType.GainControl;
        return targetedCommanderRemoval(true,true,true,removes,destroy,
                target.hasKeyword(Keyword.INDESTRUCTIBLE));
    }
}
