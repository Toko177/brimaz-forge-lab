package forge.ai;

import forge.game.trigger.TriggerType;
import java.util.concurrent.atomic.LongAdder;

/** Pure mandatory-negative filter for Forge AI PREDICTION of combat triggers.
 * No new positive predictions and NO changes to the actual trigger engine.
 *
 * All conditions here are cases where forge-2.0.15
 * ComputerUtilCombat.combatTriggerWillTrigger() unconditionally returns false,
 * but AFTER costly trigger.requirementsCheck(game). Exclude those first.
 */
public final class CombatTriggerNegativePrune {
    private CombatTriggerNegativePrune() {}

    public static final boolean ENABLED =
            Boolean.getBoolean("brimaz.fastCombatTriggerNegativePrune");
    private static final boolean TRACE =
            Boolean.getBoolean("brimaz.fastCombatTriggerTrace");
    private static final LongAdder PRUNED = new LongAdder();

    static {
        if (ENABLED && TRACE) {
            Runtime.getRuntime().addShutdownHook(
                new Thread(() -> System.out.println(
                    "FOUR_AI_FAST_COMBAT_TRIGGER_PRUNED count="+PRUNED.sum())));
        }
    }

    public static boolean impossible(final TriggerType mode,
                                     final boolean defenderPresent,
                                     final boolean attackerAlreadyAttacking,
                                     final boolean incompatibleAttackAlone) {
        if (mode == TriggerType.Attacks) {
            return attackerAlreadyAttacking || incompatibleAttackAlone;
        }
        if (mode == TriggerType.AttackerUnblocked) {
            return defenderPresent;
        }
        // No defender means no blocking/damage pair. Stock Forge already
        // returns willTrigger=false here; we only move this fast reject
        // BEFORE checking every unrelated trigger's expensive requirements.
        return !defenderPresent && (mode == TriggerType.Blocks
                || mode == TriggerType.AttackerBlocked
                || mode == TriggerType.AttackerBlockedByCreature
                || mode == TriggerType.DamageDone);
    }

    public static boolean shouldSkip(final TriggerType mode,
                                     final boolean defenderPresent,
                                     final boolean attackerAlreadyAttacking,
                                     final boolean incompatibleAttackAlone) {
        if (!ENABLED) return false;
        boolean skip=impossible(mode,defenderPresent,attackerAlreadyAttacking,
                                incompatibleAttackAlone);
        if (skip && TRACE) PRUNED.increment();
        return skip;
    }
}
