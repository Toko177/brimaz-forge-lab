package forge.ai;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Public-information counterattack risk and greedy legal blocker coverage.
 * No Forge dependency so it can be unit-tested without a game state.
 * One defender may stop at most one normal non-trample attacker; unusual
 * blocker multiplicities, menace, banding and combat tricks remain estimates.
 */
public final class DefenseCoverageModel {
    private DefenseCoverageModel() {}

    public static final class Threat {
        public final int combatDamage;
        public final boolean infect;
        public final String commanderId;
        public final int alreadyCommanderDamage;
        public final boolean reliablyStoppedByOneBlocker;
        public final boolean[] blockableBy;

        public Threat(int combatDamage, boolean infect, String commanderId,
                      int alreadyCommanderDamage,
                      boolean reliablyStoppedByOneBlocker,
                      boolean[] blockableBy) {
            this.combatDamage = Math.max(0, combatDamage);
            this.infect = infect;
            this.commanderId = commanderId;
            this.alreadyCommanderDamage = Math.max(0, alreadyCommanderDamage);
            this.reliablyStoppedByOneBlocker = reliablyStoppedByOneBlocker;
            this.blockableBy = blockableBy.clone();
        }
    }

    public static final class Risk {
        public final int lifeDamage, poisonDamage, highestCommanderTotal, riskPermille;
        public Risk(int lifeDamage, int poisonDamage, int highestCommanderTotal, int riskPermille) {
            this.lifeDamage = lifeDamage;
            this.poisonDamage = poisonDamage;
            this.highestCommanderTotal = highestCommanderTotal;
            this.riskPermille = riskPermille;
        }
    }

    static int ceilDiv(int numerator, int denominator) {
        return (numerator + denominator - 1) / denominator;
    }

    /** Indexes refer to the same defensively available creature array used for every threat. */
    public static Risk forecast(List<Threat> threats, boolean[] available,
                                int life, int currentPoison,
                                boolean lifeProtected, boolean poisonProtected,
                                boolean commanderProtected) {
        if (life <= 0) life = 1;
        List<Integer> order = new ArrayList<>();
        for (int i=0;i<threats.size();i++) order.add(i);
        final int remainingPoison = Math.max(1, 10-currentPoison);
        final int currentLife = life;
        // Prioritize defending against attacks with the largest fractional
        // contribution to one of the three independent loss thresholds.
        order.sort(Comparator.<Integer>comparingInt(i -> {
            Threat a = threats.get(i);
            int priority = a.infect
                ? (poisonProtected ? 0 : 1000*a.combatDamage/remainingPoison)
                : (lifeProtected ? 0 : 1000*a.combatDamage/currentLife);
            if (a.commanderId != null && !commanderProtected) {
                priority = Math.max(priority,
                        1000*a.combatDamage/Math.max(1,21-a.alreadyCommanderDamage));
            }
            return priority;
        }).reversed().thenComparingInt(i -> i));

        boolean[] used = new boolean[available.length];
        boolean[] prevented = new boolean[threats.size()];
        for (int attackerIndex : order) {
            Threat a=threats.get(attackerIndex);
            if (!a.reliablyStoppedByOneBlocker) continue;
            int selected=-1;
            // Least-flexible-first helps prevent wasting versatile defenders.
            int fewestOtherOptions=Integer.MAX_VALUE;
            for(int b=0;b<available.length;b++){
                if(!available[b] || used[b] || b>=a.blockableBy.length || !a.blockableBy[b]) continue;
                int options=0;
                for(int other : order){
                    if(other==attackerIndex || prevented[other]) continue;
                    Threat t=threats.get(other);
                    if(b<t.blockableBy.length && t.blockableBy[b]) options++;
                }
                if(options<fewestOtherOptions){fewestOtherOptions=options;selected=b;}
            }
            if(selected>=0){used[selected]=true;prevented[attackerIndex]=true;}
        }

        int incomingLife=0, incomingPoison=0, highestCommander=0;
        for(int i=0;i<threats.size();i++){
            Threat a=threats.get(i);
            if(prevented[i])continue;
            if(a.infect) incomingPoison+=a.combatDamage;
            else incomingLife+=a.combatDamage;
            if(a.commanderId!=null){
                // Each commander is an independent 21-damage loss track.
                // If multiple attacks arise from one source in a round, sum
                // their combat damage, but never sum different commanders.
                int sameSourceDamage=0;
                for(int j=0;j<threats.size();j++){
                    Threat t=threats.get(j);
                    if(!prevented[j] && a.commanderId.equals(t.commanderId)){
                        sameSourceDamage+=t.combatDamage;
                    }
                }
                highestCommander=Math.max(highestCommander,
                        a.alreadyCommanderDamage+sameSourceDamage);
            }
        }
        int pressure=0;
        if(!lifeProtected) pressure=Math.max(pressure,1000*incomingLife/currentLife);
        if(!poisonProtected) pressure=Math.max(pressure,1000*(currentPoison+incomingPoison)/10);
        if(!commanderProtected) pressure=Math.max(pressure,1000*highestCommander/21);
        return new Risk(incomingLife,incomingPoison,highestCommander,pressure);
    }

    public static int bestReservation(List<List<Threat>> threeOpponents,
                                     boolean[] currentlyHeld, boolean[] candidate,
                                     int life, int poison,
                                     boolean lifeProtected, boolean poisonProtected,
                                     boolean commanderProtected) {
        int base=worstRisk(threeOpponents,currentlyHeld,life,poison,
                           lifeProtected,poisonProtected,commanderProtected);
        if(base<1000) return -1; // no projected loss after existing blockers
        int best=-1, bestGain=0;
        for(int b=0;b<candidate.length;b++){
            if(!candidate[b] || currentlyHeld[b])continue;
            currentlyHeld[b]=true;
            int after=worstRisk(threeOpponents,currentlyHeld,life,poison,
                                lifeProtected,poisonProtected,commanderProtected);
            currentlyHeld[b]=false;
            int gain=base-after;
            if(gain>bestGain){bestGain=gain;best=b;}
        }
        return best;
    }

    public static int worstRisk(List<List<Threat>> opponents, boolean[] available,
                                int life, int poison,
                                boolean lifeProtected, boolean poisonProtected,
                                boolean commanderProtected) {
        int worst=0;
        for(List<Threat> threats:opponents){
            int current=forecast(threats,available,life,poison,
                                 lifeProtected,poisonProtected,commanderProtected).riskPermille;
            worst=Math.max(worst,current);
        }
        return worst;
    }
}
