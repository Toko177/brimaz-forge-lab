package forge.ai;

import forge.game.card.Card;
import forge.game.combat.CombatUtil;
import forge.game.player.GameLossReason;
import forge.game.player.Player;
import forge.game.keyword.Keyword;

/**
 * Opt-in PUBLIC state-only imminent player-elimination protection.
 *
 * This does not choose legal targets. The existing Forge card target filters,
 * protections, timing, costs, and spell stack remain authoritative. It only
 * adds a bounded priority to ALREADY LEGALLY TARGETABLE enemy creatures when
 * ComputerUtilCard ranks removal targets.
 */
public final class MultiplayerRemovalUrgencyPolicy {
    private MultiplayerRemovalUrgencyPolicy() {}

    public static int urgencyScore(final int damage, final int life,
                                   final int poisonAlready, final int commanderAlready,
                                   final boolean infect, final boolean commander,
                                   final boolean noBlocker, final boolean lifeProtected,
                                   final boolean poisonProtected,
                                   final boolean commanderProtected,
                                   final boolean canAttackPlayerNextTurn) {
        if (damage<=0 || !canAttackPlayerNextTurn || !noBlocker) return 0;
        boolean directLethal=!lifeProtected && !infect && life>0 && damage>=life;
        boolean poisonLethal=infect && !poisonProtected
                             && poisonAlready+damage>=10;
        boolean commanderLethal=commander && !commanderProtected
                             && commanderAlready+damage>=21;
        if (directLethal || poisonLethal || commanderLethal) return 900;
        int remainingLife=Math.max(1,life);
        int remainingPoison=Math.max(1,10-poisonAlready);
        int remainingCommander=Math.max(1,21-commanderAlready);
        int risk=0;
        if (!infect && !lifeProtected) risk=Math.max(risk, 1000*damage/remainingLife);
        if (infect && !poisonProtected) risk=Math.max(risk, 1000*damage/remainingPoison);
        if (commander && !commanderProtected)
            risk=Math.max(risk, 1000*damage/remainingCommander);
        // Only meaningful unblocked pressure changes the ranking. Do not
        // promote irrelevant 1/1s over key engines or unblocked combos.
        if (risk>=650) return 160;
        if (risk>=400) return 70;
        return 0;
    }

    public static int publicThreatBonus(final Player ai, final Card enemy) {
        if (ai==null || enemy==null || !enemy.isCreature()
                || !enemy.getController().isOpponentOf(ai)
                || ai.getGame()==null) return 0;
        // Expensive scoring is skipped unless the card can threaten THIS
        // specific player, not merely some player at the table.
        if(!ComputerUtilCombat.canAttackNextTurn(enemy,ai)) return 0;
        int power=Math.max(0,enemy.getNetCombatDamage());
        if(enemy.hasDoubleStrike())power*=2;
        if(power<=0)return 0;

        // A possible legal blocker is enough to prevent us from treating
        // the damage as certain; do not guess the opponent's instant spells.
        boolean canBlockAny=false;
        if(CombatUtil.canBeBlocked(enemy,null,ai)){
            for(Card blocker:ai.getCreaturesInPlay()){
                if(CombatUtil.canBlock(enemy,blocker,false)){
                    canBlockAny=true;
                    break;
                }
            }
        }
        boolean noBlocker=!canBlockAny;
        // If the attack has trample, a legal block does not necessarily
        // stop ALL damage; score remains conservative until a genuine
        // multi-block combat solver is available.
        if(enemy.hasKeyword(Keyword.TRAMPLE) && !noBlocker)return 0;

        int bonus=urgencyScore(
            power,ai.getLife(),ai.getPoisonCounters(),
            enemy.isCommander()?ai.getCommanderDamage(enemy):0,
            enemy.hasKeyword(Keyword.INFECT),enemy.isCommander(),
            noBlocker,ai.cantLoseForZeroOrLessLife(),
            ai.cantLoseCheck(GameLossReason.Poisoned),
            ai.cantLoseCheck(GameLossReason.CommanderDamage),true
        );
        if(bonus>0 && Boolean.getBoolean("brimaz.removalUrgencyTrace")){
            System.out.println("FOUR_AI_REMOVAL_URGENCY target="+enemy.getName()
                +" player="+ai.getName()+" scoreBonus="+bonus
                +" predictedDamage="+power);
        }
        return bonus;
    }
}
