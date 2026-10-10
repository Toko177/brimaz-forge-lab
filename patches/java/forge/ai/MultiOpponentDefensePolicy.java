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
 * V16: conservative publicly-visible defensive reserve for four-seat Commander.
 *
 * Called after Forge's existing combat safety heuristics, not instead of them.
 * This prevents a frequently encountered multiplayer failure mode: spending
 * the final possible blocker against player A despite lethal counterattack
 * pressure from player B or C. All combat legality remains in Forge.
 *
 * It is an estimate, not a legal-block assignment solver: opponent choices,
 * abilities at instant speed, and hidden cards are not predicted.
 */
public final class MultiOpponentDefensePolicy {
    private MultiOpponentDefensePolicy() {}

    public static boolean visibleLethal(int life, int damage,
                                        int poisonAlready, int infectDamage,
                                        int commanderAlready, int commanderDamage,
                                        boolean lifeProtected,
                                        boolean poisonProtected,
                                        boolean commanderProtected) {
        return (!lifeProtected && life > 0 && damage >= life)
                || (!poisonProtected && poisonAlready + infectDamage >= 10
                    && infectDamage > 0)
                || (!commanderProtected && commanderAlready + commanderDamage >= 21
                    && commanderDamage > 0);
    }

    public static int requiredBlockers(int existing, int attackableThreats,
                                       boolean visibleLethal,
                                       int maxNeeded) {
        if (!visibleLethal || attackableThreats <= 0 || maxNeeded <= 0) {
            return 0;
        }
        // Reserve one extra blocker if an attack would leave us defenseless.
        // If two separate potential attackers could deal fatal damage, keep two.
        int target = Math.min(2, attackableThreats);
        return Math.max(0, Math.min(maxNeeded, target - existing));
    }

    public static void reserve(Player ai, List<Card> allowedAttackers,
                               List<Card> alreadyAttacking) {
        if (ai == null || ai.getOpponents().size() < 2
                || !ai.getGame().getPhaseHandler().isPlayerTurn(ai)
                || !ai.getGame().getPhaseHandler().is(PhaseType.COMBAT_DECLARE_ATTACKERS)
                || allowedAttackers.isEmpty()) {
            return;
        }
        List<Card> own = ai.getCreaturesInPlay();
        if (own.size() > 35) return; // avoid pathological token-board cost

        int maxRequired = 0;
        int worstIncoming = 0;
        List<Card> dangerousOppAttackers = new ArrayList<>();
        int opponentCount = 0;

        for (Player opp : ai.getOpponents()) {
            List<Card> creatures = opp.getCreaturesInPlay();
            if (creatures.size() > 35) return;
            int damage = 0;
            int poisonDamage = 0;
            int maxCommanderAlready = 0;
            int commanderPotential = 0;
            int threats = 0;
            List<Card> active = new ArrayList<>();
            for (Card c : creatures) {
                if (!ComputerUtilCombat.canAttackNextTurn(c)) continue;
                int power = Math.max(0, c.getNetCombatDamage());
                if (c.hasDoubleStrike()) power *= 2;
                if (power <= 0) continue;
                active.add(c);
                threats++;
                if (c.hasKeyword(Keyword.INFECT)) poisonDamage += power;
                else damage += power;
                if (c.isCommander()
                        && !ai.cantLoseCheck(GameLossReason.CommanderDamage)
                        && ai.getCommanderDamage(c) + power >
                           maxCommanderAlready + commanderPotential) {
                    maxCommanderAlready = ai.getCommanderDamage(c);
                    commanderPotential = power;
                }
            }
            if (active.isEmpty()) continue;

            boolean lethal = visibleLethal(
                    ai.getLife(), damage, ai.getPoisonCounters(), poisonDamage,
                    maxCommanderAlready, commanderPotential,
                    ai.cantLoseForZeroOrLessLife(),
                    ai.cantLoseCheck(GameLossReason.Poisoned),
                    ai.cantLoseCheck(GameLossReason.CommanderDamage));
            if (!lethal) continue;

            opponentCount++;
            worstIncoming = Math.max(worstIncoming, damage);
            dangerousOppAttackers.addAll(active);
            // How many already held-back creatures can legally block *some*
            // attack? This is a conservative count, not an assignment solver.
            int existing = 0;
            for (Card defender : own) {
                if (alreadyAttacking.contains(defender)
                        || allowedAttackers.contains(defender)
                        || defender.isTapped()) continue;
                for (Card attacker : active) {
                    if (CombatUtil.canBlock(attacker, defender, false)) {
                        existing++;
                        break;
                    }
                }
            }
            int needed = requiredBlockers(existing, threats, lethal,
                                          allowedAttackers.size());
            maxRequired = Math.max(maxRequired, needed);
        }
        System.out.println("FOUR_AI_DEFENSE_CHECK controller=" + ai.getName()
                + " candidates=" + allowedAttackers.size()
                + " dangerousOpponents=" + opponentCount
                + " required=" + maxRequired
                + " turn=" + ai.getGame().getPhaseHandler().getTurn());
        if (maxRequired == 0) return;

        int reserved = 0;
        for (int i = 0; i < maxRequired; i++) {
            Card best = null;
            int bestScore = Integer.MIN_VALUE;
            for (Card defender : allowedAttackers) {
                if (defender.hasKeyword(Keyword.VIGILANCE)) continue;
                int largestSave = 0;
                for (Card attacker : dangerousOppAttackers) {
                    if (CombatUtil.canBlock(attacker, defender, false)) {
                        int dmg = Math.max(0, attacker.getNetCombatDamage());
                        if (attacker.hasDoubleStrike()) dmg *= 2;
                        largestSave = Math.max(largestSave, dmg);
                    }
                }
                if (largestSave == 0) continue;
                int score = largestSave * 10 - Math.max(0, defender.getNetCombatDamage());
                if (score > bestScore) {
                    bestScore = score;
                    best = defender;
                }
            }
            if (best == null) break;
            allowedAttackers.remove(best);
            reserved++;
        }
        if (reserved > 0) {
            System.out.println("FOUR_AI_DEFENSE_RESERVE controller=" + ai.getName()
                    + " held=" + reserved
                    + " dangerousOpponents=" + opponentCount
                    + " maxVisibleLifePressure=" + worstIncoming
                    + " turn=" + ai.getGame().getPhaseHandler().getTurn());
        }
    }
}
