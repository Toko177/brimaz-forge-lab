package forge.ai;

import forge.game.card.Card;
import forge.game.combat.CombatUtil;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.GameLossReason;
import forge.game.player.Player;

import java.util.ArrayList;
import java.util.List;

/**
 * V17 public-board three-opponent defense model.
 * Does not replace the Forge combat legality or the V13 attack policy.
 * Selects a maximum of two candidates *after* stock Forge safety decisions.
 */
public final class MultiplayerDefenseCoverage {
    private MultiplayerDefenseCoverage() {}

    public static void reserve(final Player ai, final List<Card> allowedAttackers,
                               final List<Card> alreadyAttacking) {
        if (ai == null || allowedAttackers.isEmpty()
                || ai.getOpponents().size() < 2
                || !ai.getGame().getPhaseHandler().isPlayerTurn(ai)
                || !ai.getGame().getPhaseHandler().is(PhaseType.COMBAT_DECLARE_ATTACKERS)) return;

        final List<Card> own=ai.getCreaturesInPlay();
        if (own.size()>35) return;
        final boolean[] alreadyHeld=new boolean[own.size()];
        final boolean[] candidates=new boolean[own.size()];
        for(int j=0;j<own.size();j++){
            Card c=own.get(j);
            if(c.isTapped() || alreadyAttacking.contains(c)) continue;
            if(allowedAttackers.contains(c)){
                // Vigilance can both attack and block; no need to reserve it.
                if(!c.hasKeyword(Keyword.VIGILANCE)) candidates[j]=true;
            } else {
                alreadyHeld[j]=true;
            }
        }
        boolean anyCandidate=false;
        for(boolean b:candidates)anyCandidate|=b;
        if(!anyCandidate)return;

        final List<List<DefenseCoverageModel.Threat>> threatsByOpponent=new ArrayList<>();
        int eligibleOpponents=0;
        for(Player opp:ai.getOpponents()){
            final List<Card> threats=opp.getCreaturesInPlay();
            if(threats.size()>35)return;
            final List<DefenseCoverageModel.Threat> current=new ArrayList<>();
            for(Card attacker:threats){
                // Important: canAttackNextTurn(attacker) tests ANY defender;
                // the target-specific overload prevents phantom danger.
                if(!ComputerUtilCombat.canAttackNextTurn(attacker, ai))continue;
                int power=Math.max(0,attacker.getNetCombatDamage());
                if(attacker.hasDoubleStrike())power*=2;
                if(power<=0)continue;
                boolean[] edges=new boolean[own.size()];
                for(int j=0;j<own.size();j++){
                    Card blocker=own.get(j);
                    if(!blocker.isTapped() && !alreadyAttacking.contains(blocker)){
                        edges[j]=CombatUtil.canBlock(attacker,blocker,false);
                    }
                }
                // Single ordinary block reliably prevents life/poison damage.
                // Trample, menace and extraordinary assignment are deliberately
                // not treated as guaranteed preventions in this estimate.
                boolean singleBlockReliable= !attacker.hasKeyword(Keyword.TRAMPLE)
                                             && !attacker.hasKeyword(Keyword.MENACE);
                current.add(new DefenseCoverageModel.Threat(
                        power,attacker.hasKeyword(Keyword.INFECT),
                        attacker.isCommander()?Integer.toString(attacker.getId()):null,
                        attacker.isCommander()?ai.getCommanderDamage(attacker):0,
                        singleBlockReliable,edges));
            }
            if(!current.isEmpty())eligibleOpponents++;
            threatsByOpponent.add(current);
        }
        boolean lifeProtected=ai.cantLoseForZeroOrLessLife();
        boolean poisonProtected=ai.cantLoseCheck(GameLossReason.Poisoned);
        boolean commanderProtected=ai.cantLoseCheck(GameLossReason.CommanderDamage);
        int baseline=DefenseCoverageModel.worstRisk(
                threatsByOpponent,alreadyHeld,ai.getLife(),ai.getPoisonCounters(),
                lifeProtected,poisonProtected,commanderProtected);
        int reserved=0;
        int after=baseline;
        while(reserved<2){
            int pick=DefenseCoverageModel.bestReservation(
                    threatsByOpponent,alreadyHeld,candidates,ai.getLife(),ai.getPoisonCounters(),
                    lifeProtected,poisonProtected,commanderProtected);
            if(pick<0)break;
            Card held=own.get(pick);
            allowedAttackers.remove(held);
            candidates[pick]=false;
            alreadyHeld[pick]=true;
            reserved++;
            after=DefenseCoverageModel.worstRisk(
                    threatsByOpponent,alreadyHeld,ai.getLife(),ai.getPoisonCounters(),
                    lifeProtected,poisonProtected,commanderProtected);
        }
        System.out.println("FOUR_AI_V17_COVERAGE controller="+ai.getName()
                +" threatPlayers="+eligibleOpponents
                +" baselinePermille="+baseline
                +" afterPermille="+after
                +" reserved="+reserved
                +" turn="+ai.getGame().getPhaseHandler().getTurn());
        if(reserved>0){
            System.out.println("FOUR_AI_V17_RESERVE controller="+ai.getName()
                    +" held="+reserved+" riskReduction="+(baseline-after));
        }
    }
}
