package forge.ai;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Commander V42: bounded, deck-agnostic evaluation of public information.
 *
 * This is NOT a rules engine or a prediction of combat, card draws or spells
 * in hidden hands. Its output is advisory only: Forge validates every actual
 * SpellAbility independently. No card names, commanders or archetypes are
 * hardcoded into scores.
 */
public final class CommanderGenericModelV42 {
    private CommanderGenericModelV42() {}

    public enum Kind { COMMANDER, CREATURE, ARTIFACT, ENCHANTMENT, PLANESWALKER }

    public record State(int turn, int mana, int lands, int life, int hand,
                        int creatures, int readyBlockers, boolean commanderPresent,
                        int opponentPowerA, int opponentPowerB, int opponentPowerC) {
        public State {
            if (turn < 0 || mana < 0 || lands < 0 || hand < 0
                    || creatures < 0 || readyBlockers < 0
                    || opponentPowerA < 0 || opponentPowerB < 0
                    || opponentPowerC < 0) {
                throw new IllegalArgumentException("Invalid observable Commander state");
            }
        }
    }

    public record Candidate(String name, Kind kind, int manaValue,
                            int power, int toughness, boolean manaAbility,
                            boolean playableNow) {
        public Candidate {
            if (name == null || name.isBlank() || kind == null || manaValue < 0
                    || power < 0 || toughness < 0)
                throw new IllegalArgumentException("Invalid observable candidate");
        }
    }

    public record Decision(List<Candidate> ranked, int leadingMargin,
                           boolean underPressure, String reason) {}

    /** One strongest visible board, NOT an invented combined three-player attack. */
    public static int strongestBoard(State s) {
        return Math.max(s.opponentPowerA(),
                Math.max(s.opponentPowerB(), s.opponentPowerC()));
    }

    /** Conservative threat gate: ordinary Forge may have better instant removal. */
    public static boolean danger(State s) {
        int exposed = Math.max(0, strongestBoard(s) - 2 * Math.min(8, s.readyBlockers()));
        return s.life() > 0 && (exposed >= s.life()
                || (s.life() <= 14 && exposed >= Math.max(5, s.life() / 2)));
    }

    /** A transparent marginal development score, NOT probability of winning. */
    public static int score(State s, Candidate c) {
        // Real Forge already verified the CURRENT mana payment and casting
        // restrictions on the offered SpellAbility. Card mana value is NOT
        // the payable amount (cost reductions, alternate costs, convoke,
        // commander tax, etc). Never veto a Forge-payable spell solely
        // because its printed mana value exceeds a rough mana estimate.
        if (!c.playableNow())return Integer.MIN_VALUE;
        int early = Math.max(0, 5 - s.lands());
        int score = switch(c.kind()) {
            case COMMANDER -> s.commanderPresent() ? -30 : 38;
            case CREATURE -> 22 + 3 * Math.min(6, c.power())
                    + 2 * Math.min(6, c.toughness());
            case ARTIFACT -> 24;
            case ENCHANTMENT -> 27;
            case PLANESWALKER -> 25;
        };
        // A real mana ability printed on the candidate, not a card-name guess.
        // A creature's mana ability will generally suffer summoning sickness:
        // its bonus is discounted relative to a noncreature permanent.
        if (c.manaAbility()) {
            score += (c.kind()==Kind.CREATURE ? 15 : 26)
                    + 5 * early + (s.lands() <= 3 ? 10 : 0);
        }
        if (c.kind()==Kind.COMMANDER && s.lands() >= 4)score+=8;
        if (c.kind()==Kind.CREATURE && s.creatures()==0)score+=8;
        if (s.hand()<=2 && c.kind()==Kind.ENCHANTMENT)score+=3;
        if (s.turn()<=5 && c.manaValue()>=6)score-=10;
        // Reward reasonable use of mana while mildly discouraging all-in
        // expensive development with public enemy pressure.
        score += Math.min(8, c.manaValue() * 2);
        if (s.life()<=18 && strongestBoard(s)>=s.life()/2
                && c.kind()==Kind.PLANESWALKER)score-=12;
        return score;
    }

    /**
     * Rank only real, already affordable candidate spells. Fail closed on
     * dangerous boards and ties; abstain rather than override stock Forge
     * without meaningful observable evidence.
     */
    public static Decision decide(State s, List<Candidate> candidates) {
        if (s==null || candidates==null || candidates.size()<2)
            return new Decision(List.of(),0,false,"insufficient_choices");
        if (danger(s))
            return new Decision(List.of(),0,true,"survival_priority_stock_fallback");

        List<Candidate> viable = new ArrayList<>();
        for (Candidate c : candidates) {
            if (c!=null && score(s,c)!=Integer.MIN_VALUE)viable.add(c);
        }
        if (viable.size()<2)
            return new Decision(List.of(),0,false,"insufficient_payable_choices");
        viable.sort(Comparator.comparingInt((Candidate c)->score(s,c)).reversed()
                .thenComparing(Candidate::name));
        int margin=score(s,viable.get(0))-score(s,viable.get(1));
        if (margin<12)
            return new Decision(List.of(),margin,false,"ambiguous_stock_fallback");
        return new Decision(List.copyOf(viable.subList(0,Math.min(3,viable.size()))),
                margin,false,"distinct_public_development_preference");
    }
}
