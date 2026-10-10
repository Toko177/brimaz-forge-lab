package forge.ai.ability;

import forge.game.ability.ApiType;
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
