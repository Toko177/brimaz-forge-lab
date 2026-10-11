package forge.ai;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * BOUNDED imperfect-information strategic search for 4-player Commander.
 *
 * Only known cards (own hand/command zone) are projected. Future turns do not
 * invent a draw, a land drop, an opponent spell or a Forge resolution. This
 * is a fast abstract advisor, never a Magic-rules engine: AiController must
 * separately approve all real immediate spells via canPlayAndPayFor.
 *
 * V35: at most 3 card choices across this turn and next turn, with an explicit
 * pass/no-more-spells possibility and a capped branching factor.
 */
public final class MultiplayerStrategicSearchV35 {
    private MultiplayerStrategicSearchV35() {}

    public static final int DEATH_PAYOFF = 1;
    public static final int TOKEN_MULTIPLIER = 2;
    public static final int INCUBATE_ENGINE = 4;
    public static final int RECURSION = 8;
    public static final int EXPENSIVE_NONCREATURE = 16;
    public static final int INSTANT_MANA = 32;

    public record CardPlan(String name, int cost, MultiplayerStrategicModel.Role role,
                           int power, int features, boolean forgeTimingLegal) {
        public CardPlan {
            if (name == null || name.isBlank() || role == null || cost < 0 || power < 0)
                throw new IllegalArgumentException("invalid known card plan");
        }
        public boolean has(int flag) { return (features & flag) != 0; }
    }

    /** Opponent powers are public *threat indicators*, not actual expected damage. */
    public record Table(int mana, int lands, int handLands, int life, int handCards,
                        int ownCreatures, int ownTokens, int ownArtifacts,
                        int outlets, int deathPayoffs, int tokenMultipliers,
                        int tokenEngines, boolean commanderPresent,
                        int opponentPower1, int opponentPower2, int opponentPower3,
                        int opponentLife1, int opponentLife2, int opponentLife3,
                        int turn) {
        public Table {
            if (mana < 0 || lands < 0 || handLands < 0 || handCards < 0
                    || ownCreatures < 0 || ownTokens < 0 || ownArtifacts < 0
                    || outlets < 0 || deathPayoffs < 0 || tokenMultipliers < 0
                    || tokenEngines < 0 || opponentPower1 < 0 || opponentPower2 < 0
                    || opponentPower3 < 0 || turn < 0)
                throw new IllegalArgumentException("negative public table features");
        }
    }

    public record Result(CardPlan first, CardPlan currentFollowup,
                         CardPlan nextTurnFollowup, CardPlan runnerUp,
                         int score, int margin, int nodesExplored,
                         boolean underThreat, String explanation) {}

    private record State(int mana, int nextMana, int ownCreatures, int tokens,
                         int artifacts, int outlets, int payoffs,
                         int multipliers, int tokenEngines, int handSize,
                         boolean commanderPresent) {}

    private record Line(CardPlan first, CardPlan second, CardPlan third,
                        int value, int visits, String reason) {}

    private static int min(int value, int cap) { return Math.min(value, cap); }
    private static int atLeast(int value) { return Math.max(0, value); }

    /** Under multi-opponent pressure, future speculative plans are discounted. */
    public static boolean underThreat(Table t) {
        // Each opponent may choose a different defender: never pretend
        // the sum of all three boards necessarily attacks us at once.
        int strongest=Math.max(t.opponentPower1(),
                       Math.max(t.opponentPower2(),t.opponentPower3()));
        int visibleDefense=Math.min(t.ownCreatures(),8)*2;
        int exposed=Math.max(0,strongest-visibleDefense);
        return (t.life()<=14 && exposed>=Math.max(4,t.life()/2))
            || (t.life()<=25 && exposed>=t.life());
    }

    private static State initial(Table t) {
        return new State(t.mana(),t.mana(),t.ownCreatures(),t.ownTokens(),
                t.ownArtifacts(),t.outlets(),t.deathPayoffs(),
                t.tokenMultipliers(),t.tokenEngines(),t.handCards(),
                t.commanderPresent());
    }

    private static State apply(State s, CardPlan c, boolean firstTurn) {
        int ramp = c.role() == MultiplayerStrategicModel.Role.RAMP ? 1 : 0;
        int token = c.role() == MultiplayerStrategicModel.Role.TOKEN_ENGINE ? 1 : 0;
        int creature = (c.role() == MultiplayerStrategicModel.Role.CREATURE
                || c.role() == MultiplayerStrategicModel.Role.COMMANDER
                || c.power() > 0) ? 1 : 0;
        int outlet = c.role() == MultiplayerStrategicModel.Role.SAC_OUTLET ? 1 : 0;
        // Cards entering do NOT get a mana boost for the same turn by default.
        // Any immediate-mana exception remains speculative, never a paid-cost proof.
        int next = s.nextMana() + ramp;
        int mana = s.mana() - c.cost();
        if (firstTurn && c.has(INSTANT_MANA)) mana+=2;
        return new State(atLeast(mana),next,s.ownCreatures()+creature,
                s.tokens()+token,s.artifacts()+((c.role()==MultiplayerStrategicModel.Role.RAMP ||
                    c.role()==MultiplayerStrategicModel.Role.SAC_OUTLET)?1:0),
                s.outlets()+outlet,s.payoffs()+(c.has(DEATH_PAYOFF)?1:0),
                s.multipliers()+(c.has(TOKEN_MULTIPLIER)?1:0),
                s.tokenEngines()+(c.role()==MultiplayerStrategicModel.Role.TOKEN_ENGINE ||
                    c.has(INCUBATE_ENGINE)?1:0),
                atLeast(s.handSize()-1),
                s.commanderPresent() || c.role()==MultiplayerStrategicModel.Role.COMMANDER);
    }

    /** Marginal strategic utility in a *known* board position, not a win probability. */
    public static int evaluate(Table t, CardPlan c, int tokenCount,
                               int outletCount, int payoffs, int multipliers,
                               int engines, boolean commanderPresent) {
        boolean emergency=underThreat(t);
        int landDeficit=atLeast(5-t.lands());
        int lifeRisk=Math.max(t.opponentPower1(),Math.max(t.opponentPower2(),t.opponentPower3()));
        int base = switch(c.role()) {
            case RAMP -> 16 + 5*landDeficit + (t.lands()<=3 ? 15:0);
            case COMMANDER -> 19 + 6*min(engines,3) + 4*min(t.ownArtifacts(),6)
                  + (commanderPresent ? -14:10);
            case TOKEN_ENGINE -> 23 + 6*min(payoffs,3) + 5*min(outletCount,2)
                  + 5*min(multipliers,2);
            case SAC_OUTLET -> tokenCount>0
                  ? 15+6*min(tokenCount,5)+5*min(payoffs,3)+5*min(engines,2)
                  : -9+(engines>0?14:0);
            case DRAW_ENGINE -> 14 + 7*atLeast(5-min(t.handCards(),5));
            case PROTECTION -> 12 + 5*min(engines+payoffs,4);
            case CREATURE -> 11+3*min(c.power(),8);
            case ENGINE -> 16+3*min(t.ownArtifacts(),5);
            case OTHER -> 9;
        };
        if(c.has(DEATH_PAYOFF)) base+=9+6*min(tokenCount+outletCount,5);
        if(c.has(TOKEN_MULTIPLIER)) base+=10+7*min(engines,4);
        if(c.has(INCUBATE_ENGINE)) base+=8+5*min(outletCount+payoffs,4);
        if(c.has(RECURSION)) base+=4+4*min(payoffs+outletCount,3);
        if(c.has(EXPENSIVE_NONCREATURE) && t.lands()<=4)base-=14;
        if (emergency) {
            // This is an *approximation*. No claim about who can actually attack.
            if(c.role()==MultiplayerStrategicModel.Role.CREATURE
                    || c.role()==MultiplayerStrategicModel.Role.COMMANDER) {
                base+=20+Math.min(20,c.power()*3);
            }
            if(c.role()==MultiplayerStrategicModel.Role.RAMP ||
                    c.role()==MultiplayerStrategicModel.Role.DRAW_ENGINE)base-=27;
            if(c.role()==MultiplayerStrategicModel.Role.PROTECTION)base+=12;
            if(c.role()==MultiplayerStrategicModel.Role.SAC_OUTLET && tokenCount==0)base-=22;
        } else if (lifeRisk>t.life() && c.power()>0) {
            base+=8;
        }
        // Immediate card quality is not synonymous with high mana value.
        base -= atLeast(c.cost()-4)*2;
        return base;
    }

    private static int score(Table t, CardPlan c, State s) {
        return evaluate(t,c,s.tokens(),s.outlets(),s.payoffs(),s.multipliers(),
                s.tokenEngines(),s.commanderPresent());
    }

    private static int nextMana(Table t, State s) {
        // Only a LAND ALREADY IN OWN HAND can justify a next-turn land drop.
        // Sources tapped during the current turn normally untap next turn.
        // Use only already-controlled lands and known ramp, never a blind draw.
        int recovered=Math.max(t.mana(),t.lands());
        int gained=Math.max(0,s.nextMana()-t.mana());
        return min(recovered+gained+(t.handLands()>0?1:0),20);
    }

    /**
     * Exhaustive small-prefix search bounded by MAX_CANDIDATES and MAX_EXPANSIONS;
     * no recursion, no engine calls, no unseen-card draws, no opponent omniscience.
     */
    public static Result choose(Table t, List<CardPlan> all) {
        if(all==null || all.isEmpty()) return null;
        final int MAX_CANDIDATES=20;
        List<CardPlan> options=new ArrayList<>(Math.min(all.size(),MAX_CANDIDATES));
        for(CardPlan c:all) {
            if(c!=null && options.size()<MAX_CANDIDATES) options.add(c);
        }
        if(options.isEmpty())return null;
        State starting=initial(t);
        boolean danger=underThreat(t);
        Line best=null, runner=null;
        int explored=0;
        for(int i=0;i<options.size();i++) {
            CardPlan first=options.get(i);
            if(!first.forgeTimingLegal()) continue;
            // Available mana is an estimate; the real engine confirms payment.
            if(first.cost()>t.mana()+2)continue;
            State afterFirst=apply(starting,first,true);
            int initial=score(t,first,starting)*100;
            Line bestForFirst=new Line(first,null,null,initial,1,"one-play");
            int futureWeight=danger ? 6 : 26;
            int secondWeight=danger ? 14 : 34;
            // Pass is always a valid abstract continuation.
            for(int j=-1;j<options.size();j++) {
                if(j==i)continue;
                CardPlan second=j<0?null:options.get(j);
                if(second!=null && (!second.forgeTimingLegal()
                        || second.cost()>afterFirst.mana()))continue;
                State afterSecond=second==null?afterFirst:apply(afterFirst,second,true);
                int now=initial+(second==null?0:secondWeight*score(t,second,afterFirst));
                CardPlan next=null;int future=0;
                int budget=nextMana(t,afterSecond);
                for(int k=0;k<options.size();k++) {
                    if(k==i || k==j)continue;
                    CardPlan third=options.get(k);
                    if(third.cost()>budget)continue;
                    int bonus=score(t,third,afterSecond);
                    // Explicit mana-unlock / token-sacrifice combo payoff in forecast.
                    if(first.role()==MultiplayerStrategicModel.Role.RAMP
                            && third.cost()>t.mana())bonus+=14;
                    if(afterSecond.tokens()>0 &&
                            third.role()==MultiplayerStrategicModel.Role.SAC_OUTLET)bonus+=10;
                    if(bonus>future){future=bonus;next=third;}
                    explored++;
                }
                int total=now+futureWeight*future;
                if(total>bestForFirst.value())
                    bestForFirst=new Line(first,second,next,total,explored,
                            second==null?"one-now-next-turn":"two-now-next-turn");
            }
            if(best==null || bestForFirst.value()>best.value()) {
                runner=best;best=bestForFirst;
            } else if(runner==null || bestForFirst.value()>runner.value()) {
                runner=bestForFirst;
            }
        }
        if(best==null)return null;
        return new Result(best.first(),best.second(),best.third(),
                runner==null?null:runner.first(),best.value(),
                runner==null?Integer.MAX_VALUE:best.value()-runner.value(),
                explored,danger,best.reason());
    }
}
