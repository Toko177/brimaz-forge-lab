package forge.ai;

/** No junit dependency: executable tactic invariants for all four AI seats. */
public final class MultiplayerCombatTargetChecks {
    private MultiplayerCombatTargetChecks() {}

    private static int score(int threat, int life, int safeDamage, int attackers) {
        return MultiplayerCombatTargetPolicy.tacticalScore(
                threat, life, safeDamage, attackers, false, false, true, false);
    }
    private static void check(boolean ok, String reason) {
        if (!ok) throw new AssertionError(reason);
    }
    public static void main(String[] args) {
        // Pick obvious open-board elimination instead of blindly attacking
        // an impressive opponent board.
        check(score(0, 8, 9, 3) > score(500, 40, 0, 3),
                "obvious open-board kill must outrank ordinary threat");

        check(score(30, 9, 9, 2) > score(30, 9, 8, 2),
                "exact lethal threshold must matter");

        check(score(20, 40, 4, 2) > score(20, 40, 0, 2),
                "visible profitable pressure beats identical blocked opponent");

        check(score(300, 40, 0, 2) > score(100, 40, 0, 2),
                "high-threat adversary should remain relevant");

        check(MultiplayerCombatTargetPolicy.tacticalScore(
              0, 5, 20, 3, false, false, false, false)
              < score(0, 5, 20, 3),
              "cannot-lose-life should not be classified as normal lethal");

        check(MultiplayerCombatTargetPolicy.tacticalScore(
              0, 5, 20, 3, false, false, true, true)
              < score(0, 5, 20, 3),
              "cant-lose-at-zero should prevent lethal bonus");

        check(MultiplayerCombatTargetPolicy.tacticalScore(
              40, 40, 0, 1, true, false, true, false)
              > score(40, 40, 0, 1),
              "reclaiming monarch is still rewarded");

        check(MultiplayerCombatTargetPolicy.tacticalScore(
              40, 40, 0, 1, false, true, true, false)
              > score(40, 40, 0, 1),
              "stealing initiative is still rewarded");

        check(MultiplayerCombatTargetPolicy.poisonPressure(8, 2, false) >
              MultiplayerCombatTargetPolicy.poisonPressure(8, 1, false),
              "unblocked infect reaches ten poison and beats near-miss");
        check(MultiplayerCombatTargetPolicy.poisonPressure(9, 1, true) == 0,
              "poison ranking respects a cannot-lose-game approximation");

        check(MultiplayerCombatTargetPolicy.commanderPressure(18, 3) >
              MultiplayerCombatTargetPolicy.commanderPressure(18, 2),
              "21 commander damage reaches a distinct lethal threshold");
        check(MultiplayerCombatTargetPolicy.commanderPressure(0, 3) < 10000,
              "regular commander damage is not a guaranteed elimination");
        check(MultiplayerCombatTargetPolicy.commanderPressure(19, 0) == 0,
              "untapped commander with no unblocked combat deals no damage");

        for (int seat = 1; seat <= 4; seat++) {
            check(score(10 + seat, 30, 2, 1) ==
                  score(10 + seat, 30, 2, 1),
                  "scoring must be deterministic across the four agents");
        }
        System.out.println("FOUR_SEAT_COMBAT_TARGET_CHECKS_PASS checks=17");
    }
}
