package forge.ai;

import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Four-seat public-board tactical triage before proactive economic development.
 *
 * Not a rules engine: returns EXISTING Forge SpellAbility objects, only
 * in active-player MAIN1/MAIN2 on empty stack. AiController must still call
 * its original canPlayAndPayFor for each proposed spell. Never invent targets,
 * values of X, colors, replacements, blockers, hidden cards or legal casts.
 *
 * Explicit card-specific knowledge; uncertain cards fall back to stock Forge.
 */
public final class MultiplayerTacticalPlannerV35 {
    private MultiplayerTacticalPlannerV35() {}
    private static final Set<String> TARGETED = Set.of(
        "Swords to Plowshares", "Anguished Unmaking", "Path to Exile",
        "Generous Gift", "Beast Within", "Chaos Warp", "Despark",
        "Utter End", "Go for the Throat", "Infernal Grasp");
    private static final Set<String> EXILE_SWEEPERS = Set.of(
        "Sunfall", "Farewell", "Merciless Eviction");
    private static final Set<String> RECURSION_SWEEPERS = Set.of("Living Death");
    private static final int MAX_ABILITIES=128;

    public record Board(int life, int ownCreatures, int ownCreaturePower,
                        int ownTokens, int ownGraveCreatures,
                        boolean commanderOnBoard,
                        int enemyCreatures, int enemyPower,
                        int greatestOpponentPower, int secondOpponentPower,
                        int greatestOpponentCreatures, int enemyGraveCreatures) {
        // Backward-compatible synthetic fixtures default to empty public graveyards.
        public Board(int life,int ownCreatures,int ownCreaturePower,int ownTokens,
                     int ownGraveCreatures,boolean commanderOnBoard,
                     int enemyCreatures,int enemyPower,int greatestOpponentPower,
                     int secondOpponentPower,int greatestOpponentCreatures) {
            this(life,ownCreatures,ownCreaturePower,ownTokens,ownGraveCreatures,
                 commanderOnBoard,enemyCreatures,enemyPower,greatestOpponentPower,
                 secondOpponentPower,greatestOpponentCreatures,0);
        }
        public Board {
            if(ownCreatures<0 || ownCreaturePower<0 || ownTokens<0
                || ownGraveCreatures<0 || enemyCreatures<0 || enemyPower<0
                || greatestOpponentPower<0 || secondOpponentPower<0
                || greatestOpponentCreatures<0 || enemyGraveCreatures<0)
                throw new IllegalArgumentException("invalid public combat snapshot");
        }
    }

    public enum Intervention { HOLD, PREEMPTIVE_REMOVAL, EXILE_SWEEP, GRAVEYARD_SWEEP }

    /**
     * Player danger is not the sum of three opponents' full power: in a
     * free-for-all they can attack one another. Use the largest one opponent
     * as a conservative capability indicator. This is not actual combat
     * validation (flying, protection, tap status, attack tax remain Forge's).
     */
    public static int danger(Board s) {
        int allyDefense=Math.min(8,s.ownCreatures())*2
                        + Math.min(5,s.ownTokens());
        return Math.max(0,s.greatestOpponentPower()-allyDefense);
    }

    public static Intervention choosePublicAction(Board s) {
        final int worst=danger(s);
        // No proactive intervention when the table is not pressuring us.
        final boolean endangered = (s.life()<=14 && worst>=Math.max(5,s.life()/2))
                || (s.life()<=24 && worst>=s.life());
        if(!endangered) return Intervention.HOLD;

        // A wipe trades board material; guard hard against resetting our own
        // commander+token payoff engine simply because others own creatures.
        int enemyAdv=s.enemyCreatures()-s.ownCreatures();
        int powerAdv=s.enemyPower()-s.ownCreaturePower();
        boolean wildlyBehind=enemyAdv>=5 && powerAdv>=12
                           && s.greatestOpponentCreatures()>=4;
        boolean desperation=s.life()<=8 && worst>=s.life();
        if((wildlyBehind || desperation) &&
              !(s.commanderOnBoard() && s.ownCreatures()>=s.enemyCreatures()/2
                && !desperation)) {
            if(s.ownGraveCreatures()>=4 &&
               s.ownGraveCreatures() >= s.ownCreatures()+2 &&
               s.ownGraveCreatures() >= s.enemyGraveCreatures()+2 &&
               s.enemyCreatures()>=4) {
                return Intervention.GRAVEYARD_SWEEP;
            }
            return Intervention.EXILE_SWEEP;
        }
        // Saving an answer for another player's main step is preferable to
        // spending it at sorcery speed if not genuinely endangered.
        if(worst >= Math.max(6,s.life()/2) &&
                s.greatestOpponentPower()>=6)
            return Intervention.PREEMPTIVE_REMOVAL;
        return Intervention.HOLD;
    }

    private static int power(Card c) {
        return c.isCreature() ? Math.max(0,Math.min(30,c.getNetPower())) : 0;
    }

    public static Board observe(Player ai) {
        int ours=0,ownPower=0,tokens=0,ownGrave=0;
        boolean commander=false;
        for(Card c:ai.getCardsIn(ZoneType.Battlefield)) {
            if(c.isCreature()){ours++;ownPower+=power(c);}
            if(c.isToken() && c.isCreature())tokens++;
            if(c.isCommander())commander=true;
        }
        for(Card c:ai.getCardsIn(ZoneType.Graveyard)) {
            if(c.isCreature())ownGrave++;
        }
        int enemyCreatures=0,enemyPower=0,maxPower=0,secondPower=0,maxCount=0;
        int enemyGrave=0;
        for(Player enemy:ai.getOpponents()) {
            int count=0,attack=0;
            for(Card c:enemy.getCardsIn(ZoneType.Battlefield)) {
                if(c.isCreature()){count++;attack+=power(c);}
            }
            for(Card c:enemy.getCardsIn(ZoneType.Graveyard)) {
                if(c.isCreature())enemyGrave++;
            }
            enemyCreatures+=count;
            enemyPower+=attack;
            maxCount=Math.max(maxCount,count);
            if(attack>=maxPower){secondPower=maxPower;maxPower=attack;}
            else if(attack>secondPower)secondPower=attack;
        }
        return new Board(ai.getLife(),ours,ownPower,tokens,ownGrave,
                    commander,enemyCreatures,enemyPower,maxPower,secondPower,maxCount,enemyGrave);
    }

    /**
     * Rank defensive spells; actual feasibility and targets are only decided
     * in stock Forge canPlayAndPayFor. Proposals are capped and do not cast.
     */
    public static List<SpellAbility> rank(Player ai,List<SpellAbility> available) {
        if(!MultiplayerStrategicSequencerV35.enabledFor(ai) ||
           available==null || available.isEmpty() || available.size()>MAX_ABILITIES
           || ai.getGame()==null)return List.of();
        var phase=ai.getGame().getPhaseHandler();
        if(!phase.isPlayerTurn(ai) ||
           !(phase.is(PhaseType.MAIN1)||phase.is(PhaseType.MAIN2)) ||
           !ai.getGame().getStack().isEmpty())return List.of();
        Board b=observe(ai);
        Intervention action=choosePublicAction(b);
        if(action==Intervention.HOLD)return List.of();
        List<SpellAbility> sweep=new ArrayList<>(2);
        List<SpellAbility> removal=new ArrayList<>(3);
        List<SpellAbility> recursion=new ArrayList<>(2);
        Set<Card> seen=new HashSet<>();
        for(SpellAbility sa:available) {
            if(sa==null || sa.getHostCard()==null || !sa.isSpell()
                 || sa.isCopied() || sa.isLandAbility())continue;
            Card c=sa.getHostCard();
            if(!c.isInZone(ZoneType.Hand) || !seen.add(c))continue;
            String name=c.getName();
            // Never infer timing from card type or model. Forge judges it.
            if(EXILE_SWEEPERS.contains(name)) sweep.add(sa);
            else if(RECURSION_SWEEPERS.contains(name))recursion.add(sa);
            else if(TARGETED.contains(name))removal.add(sa);
        }
        List<SpellAbility> ranked=new ArrayList<>(6);
        if(action==Intervention.GRAVEYARD_SWEEP) ranked.addAll(recursion);
        if(action==Intervention.EXILE_SWEEP || action==Intervention.GRAVEYARD_SWEEP)
            ranked.addAll(sweep);
        ranked.addAll(removal);
        if(ranked.size()>6)ranked=new ArrayList<>(ranked.subList(0,6));
        if(!ranked.isEmpty()) {
            System.out.println("FOUR_AI_V35_TACTICAL_WINDOW player="+ai.getName()
               +" turn="+phase.getTurn()+" intervention="+action
               +" ownCreatures="+b.ownCreatures()
               +" enemyCreatures="+b.enemyCreatures()
               +" worstOpponentPower="+b.greatestOpponentPower()
               +" life="+b.life()+" candidateSpells="+ranked.size()
               +" originalForgeValidationPending=true");
        }
        return ranked;
    }
}
