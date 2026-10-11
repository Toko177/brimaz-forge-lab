package forge.ai;

import java.util.ArrayList;
import java.util.List;

/**
 * Public-board, own-hand two-turn ABSTRACT planning model for four-player EDH.
 *
 * This is not a cloned Magic state or exact spell-resolution rollout.
 * Actual legality, mana payment, targeting and stack resolution remain Forge's.
 * Immutable inputs: safe to evaluate many options without mutating Game.
 */
public final class MultiplayerStrategicModel {
    private MultiplayerStrategicModel() {}

    public enum Role { RAMP, COMMANDER, TOKEN_ENGINE, SAC_OUTLET, DRAW_ENGINE,
        PROTECTION, CREATURE, ENGINE, OTHER }

    public record Option(String name, int cmc, Role role, int power, boolean playableNow) {
        public Option {
            if (name == null || role == null || cmc < 0 || power < 0)
                throw new IllegalArgumentException("invalid strategic candidate");
        }
    }

    public record Snapshot(int mana, int lands, int life,
                           int worstOpponentPower, int secondOpponentPower,
                           int friendlyCreatures, int artifacts, int tokens,
                           int synergyPieces, int ownHandSize, int turn) {
        public Snapshot {
            if (mana < 0 || lands < 0 || friendlyCreatures < 0 || artifacts < 0
                    || tokens < 0 || synergyPieces < 0 || ownHandSize < 0
                    || turn < 0 || worstOpponentPower < 0 || secondOpponentPower < 0)
                throw new IllegalArgumentException("invalid public board snapshot");
        }
        public boolean critical() {
            return life <= 12 && worstOpponentPower + secondOpponentPower >= life;
        }
    }

    public record Choice(Option selected, int score, int immediate, int future,
                         Option projectedNext, Option runnerUp, int margin) {}

    private static int clamp(int v, int low, int high) {
        return Math.max(low, Math.min(high, v));
    }

    /** Exposed deterministic public heuristic: unit-testable adversarial examples. */
    public static int immediate(Snapshot s, Option o) {
        int pressure = Math.max(0, s.worstOpponentPower() + s.secondOpponentPower());
        int shortage = Math.max(0, 5 - s.lands());
        int base = switch (o.role()) {
            case RAMP -> 12 + 6 * shortage + (s.lands() <= 3 ? 9 : 0);
            case COMMANDER -> 22 + 3 * Math.min(5, s.synergyPieces())
                    + 2 * Math.min(6, s.artifacts());
            case TOKEN_ENGINE -> 17 + 4 * Math.min(5, s.synergyPieces())
                    + 2 * Math.min(6, s.artifacts());
            case SAC_OUTLET -> (s.tokens() == 0 ? -14 : 13 + 6 * Math.min(5, s.tokens()))
                    + 3 * Math.min(4, s.synergyPieces());
            case DRAW_ENGINE -> 16 + 5 * clamp(5 - s.ownHandSize(), 0, 5);
            case PROTECTION -> 10 + 4 * Math.min(3, s.synergyPieces());
            case CREATURE -> 11 + 3 * Math.min(7, o.power());
            case ENGINE -> 17 + 4 * Math.min(5, s.synergyPieces());
            case OTHER -> 8;
        };
        // Late and threatening table: adding an actual blocker now is more
        // important than a one-turn-distant ramp/engine line.
        if (s.critical()) {
            if (o.role() == Role.CREATURE && o.power() > 0) base += 34;
            if (o.role() == Role.RAMP || o.role() == Role.DRAW_ENGINE) base -= 30;
            if (o.role() == Role.SAC_OUTLET && s.tokens() <= 1) base -= 18;
        } else if (pressure >= s.life() && o.role() == Role.CREATURE) {
            base += 14;
        }
        // Don't spend a turn installing a high-cost engine with no board support.
        if (o.role() == Role.SAC_OUTLET && s.tokens() == 0) base -= 16;
        if (o.role() == Role.COMMANDER && s.lands() <= 2 && o.cmc() >= 4) base -= 9;
        base -= Math.max(0, o.cmc() - 4) * 2;
        return base;
    }

    /**
     * Approximate next-turn tempo, not a forecast that any card will be drawn,
     * untapped, legally targetable or payable with particular colors.
     */
    public static int projectedMana(Snapshot s, Option first) {
        int growth = s.lands() < 8 ? 1 : 0;
        int ramp = first.role() == Role.RAMP ? 1 : 0;
        return Math.min(20, s.mana() + growth + ramp);
    }

    public static Choice choose(Snapshot s, List<Option> options) {
        if (options == null || options.isEmpty()) return null;
        List<Option> viable = new ArrayList<>();
        for (Option o : options) {
            if (o.playableNow() && o.cmc() <= s.mana()) viable.add(o);
        }
        if (viable.isEmpty()) return null;
        Option best = null, second = null, nextBest = null;
        int bestTotal = Integer.MIN_VALUE, secondTotal = Integer.MIN_VALUE;
        int bestNow = 0, bestFuture = 0;
        for (Option first : viable) {
            int now = immediate(s, first);
            int forecast = Integer.MIN_VALUE;
            Option follow = null;
            int nextMana = projectedMana(s, first);
            for (Option candidate : options) {
                if (candidate == first || candidate.cmc() > nextMana) continue;
                int value = immediate(s, candidate);
                // Playing a mana rock on the previous turn improves next
                // turn's actual spell access; don't double-count its payoff.
                if (first.role() == Role.RAMP && candidate.role() == Role.RAMP) value -= 8;
                if (first.role() == Role.TOKEN_ENGINE && candidate.role() == Role.SAC_OUTLET)
                    value += 13;
                if (first.role() == Role.COMMANDER && candidate.role() == Role.TOKEN_ENGINE)
                    value += 11;
                if (value > forecast) { forecast = value; follow = candidate; }
            }
            int future = Math.max(0, forecast);
            // Discount imaginary future actions heavily, especially under
            // lethal table pressure. The only forced action is first.
            int weight = s.critical() ? 10 : 48;
            int total = 100 * now + weight * future;
            if (total > bestTotal) {
                second = best;
                secondTotal = bestTotal;
                best = first;
                bestTotal = total;
                bestNow = now;
                bestFuture = future;
                nextBest = follow;
            } else if (total > secondTotal) {
                second = first;
                secondTotal = total;
            }
        }
        return new Choice(best, bestTotal, bestNow, bestFuture,
                nextBest, second, second == null ? Integer.MAX_VALUE : bestTotal - secondTotal);
    }
}
