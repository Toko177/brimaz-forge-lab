#!/usr/bin/env python3
"""Opt-in, all-four-seat Commander multiplayer attack target planning.

Only replaces defender preference used by Forge's standard attack planner;
Forge still decides legal attacks/blocks and resolves all damage/triggers.
No hidden opponent hand, deck peek, spell casting, rule change, or extra cards.
"""
import argparse
import hashlib
import pathlib
import subprocess
import tempfile
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--jar", required=True)
parser.add_argument("--tag", default="forge-2.0.15")
args = parser.parse_args()
jar = pathlib.Path(args.jar).resolve()
if not jar.is_file():
    parser.error("Forge executable jar is required")

source_file = "forge-ai/src/main/java/forge/ai/AiAttackController.java"
url = "https://raw.githubusercontent.com/Card-Forge/forge/" + args.tag + "/" + source_file
with urllib.request.urlopen(url, timeout=90) as resp:
    source = resp.read().decode("utf-8")

anchor = '''    public static Player choosePreferredDefenderPlayer(Player ai, boolean forCombatDmg) {
        PlayerCollection opponents = ai.getOpponents();'''
replacement = '''    public static Player choosePreferredDefenderPlayer(Player ai, boolean forCombatDmg) {
        if (forCombatDmg && Boolean.getBoolean("brimaz.fourSeatCombatTarget")) {
            Player tactical = MultiplayerCombatTargetPolicy.chooseTarget(ai);
            if (tactical != null) {
                return tactical;
            }
        }
        PlayerCollection opponents = ai.getOpponents();'''
if source.count(anchor) != 1:
    raise ValueError("Forge AiAttackController target-choice source drift")
source = source.replace(anchor, replacement, 1)

# Static evaluation takes only public/visible input. The original Forge
# attacker/blocker algorithm remains authoritative after this choice.
policy = r'''package forge.ai;

import forge.game.card.Card;
import forge.game.combat.CombatUtil;
import forge.game.keyword.Keyword;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import java.util.List;

/**
 * Conservative multiplayer attack target policy, opt-in for EVERY seat.
 * Examine the three publicly visible defenders and count creatures that
 * can currently attack, plus damage unlikely to be blocked by any present
 * legally capable blocker. This is a ranking estimate, NOT a replacement
 * for Forge's combat resolution, and not a guaranteed lethal solver.
 *
 * If the board is enormous or evaluation is on another player's turn,
 * return null so unchanged Forge heuristics select a defender.
 */
public final class MultiplayerCombatTargetPolicy {
    private MultiplayerCombatTargetPolicy() {}

    public static int tacticalScore(final int boardThreat, final int life,
                                    final int immediateLifeDamage,
                                    final int attackableCreatures,
                                    final boolean monarch,
                                    final boolean initiative,
                                    final boolean canLoseLife,
                                    final boolean cantLoseAtZero) {
        int lowLifeThreshold = 20;
        int deficit = life > 0 ? Math.max(0, lowLifeThreshold - life) : 0;
        int score = boardThreat + deficit * deficit;
        if (monarch) score += 80;
        if (initiative) score += 80;
        if (!canLoseLife) score -= 100;
        if (cantLoseAtZero) score -= 50;

        // Force a clear, visible immediate elimination over a more powerful
        // but untouchable threat. Not a certainty: instants remain unknown.
        if (life > 0 && canLoseLife && !cantLoseAtZero
                && immediateLifeDamage >= life) {
            score += 10000;
        } else {
            score += Math.min(90, Math.max(0, immediateLifeDamage) * 6);
        }
        score += Math.min(24, Math.max(0, attackableCreatures) * 3);
        return score;
    }

    /** Poison also eliminates a player at ten counters, independent of life. */
    public static int poisonPressure(final int currentPoison, final int safeInfectDamage,
                                     final boolean cannotLose) {
        if (cannotLose || safeInfectDamage <= 0) return 0;
        if (currentPoison + safeInfectDamage >= 10) return 10000;
        return Math.min(90, safeInfectDamage * 7);
    }

    public static Player chooseTarget(final Player ai) {
        if (ai == null || ai.getGame() == null
                || !ai.getGame().getPhaseHandler().isPlayerTurn(ai)) {
            return null;
        }
        final List<Card> ourCreatures = ai.getCreaturesInPlay();
        if (ourCreatures.size() > 35) return null;

        Player best = null;
        int bestScore = Integer.MIN_VALUE;
        int bestSafe = 0;
        int bestPoison = 0;
        int examined = 0;
        for (Player opp : ai.getOpponents()) {
            // Stock helper includes payable Incubator transformations / animated
            // blockers, unlike a plain snapshot of current creature types.
            final List<Card> blockers = AiAttackController.getOpponentCreatures(opp);
            if (blockers.size() > 40) return null; // conservative fallback
            int ready = 0;
            int safeDamage = 0;
            int safePoison = 0;
            for (Card a : ourCreatures) {
                if (!CombatUtil.canAttack(a, opp)) continue;
                ready++;
                int damage = Math.max(0, a.getNetCombatDamage());
                if (damage == 0) continue;
                boolean canBeBlocked = false;
                for (Card b : blockers) {
                    if (CombatUtil.canBlock(a, b)) {
                        canBeBlocked = true;
                        break;
                    }
                }
                if (!canBeBlocked) {
                    if (a.hasDoubleStrike()) damage *= 2;
                    if (a.hasKeyword(Keyword.INFECT)) safePoison += damage;
                    else safeDamage += damage; // wither still damages player life
                }
            }
            if (ready == 0) continue;
            examined++;
            int score = tacticalScore(
                    ComputerUtil.evaluateBoardPosition(ai, opp),
                    opp.getLife(), safeDamage, ready,
                    opp.isMonarch() && ai.canBecomeMonarch(),
                    opp.hasInitiative(),
                    opp.canLoseLife(),
                    opp.cantLoseForZeroOrLessLife());
            score += poisonPressure(opp.getPoisonCounters(), safePoison,
                    opp.cantLoseForZeroOrLessLife());
            if (score > bestScore) {
                bestScore = score;
                bestSafe = safeDamage;
                bestPoison = safePoison;
                best = opp;
            }
        }
        if (best != null) {
            System.out.println("FOUR_AI_TARGET: controller=" + ai.getName()
                    + " chosen=" + best.getName()
                    + " visibleSafeDamage=" + bestSafe
                    + " visibleSafePoison=" + bestPoison
                    + " opponentsScored=" + examined
                    + " score=" + bestScore
                    + " globalTurn=" + ai.getGame().getPhaseHandler().getTurn());
        }
        return best;
    }
}
'''
with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td)
    folder = root / "forge/ai"
    folder.mkdir(parents=True)
    (folder / "AiAttackController.java").write_text(source, encoding="utf-8")
    (folder / "MultiplayerCombatTargetPolicy.java").write_text(policy, encoding="utf-8")
    classes = root / "classes"
    classes.mkdir()
    subprocess.run(
        ["javac", "--release", "21", "-cp", str(jar), "-d", str(classes),
         str(folder / "AiAttackController.java"),
         str(folder / "MultiplayerCombatTargetPolicy.java")],
        check=True, timeout=240,
    )
    for name in ("AiAttackController.class", "MultiplayerCombatTargetPolicy.class"):
        if not (classes / "forge/ai" / name).is_file():
            raise RuntimeError("Missing compiled " + name)
    # Avoid losing nested classes from the upstream AI controller: only
    # replace the top-level compiled class and the new, dependency-free helper.
    subprocess.run(["jar", "uf", str(jar), "-C", str(classes),
                    "forge/ai/AiAttackController.class",
                    "-C", str(classes),
                    "forge/ai/MultiplayerCombatTargetPolicy.class"],
                   check=True, timeout=120)
    print("FOUR_AI_TARGET_CLASS_SHA256", hashlib.sha256(
          (classes/"forge/ai/MultiplayerCombatTargetPolicy.class").read_bytes()).hexdigest())
print("FOUR_AI_TARGET_PATCHED_JAR_SHA256", hashlib.sha256(jar.read_bytes()).hexdigest())
