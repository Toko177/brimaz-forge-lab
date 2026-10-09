#!/usr/bin/env python3
"""Build V13: V12 Incubate AI for all seats plus equally shared adaptive thinking budget.

Patch source is pinned to Forge's exact release tag, compiled against its JAR.
The Magic rules engine remains unchanged. The patch changes only AI decisions.
It is deliberately conservative and must pass CI pilot and subsequent A/B.
"""
import argparse
import hashlib
import pathlib
import subprocess
import tempfile
import urllib.request

parser=argparse.ArgumentParser()
parser.add_argument("--jar",required=True)
parser.add_argument("--tag",default="forge-2.0.15")
args=parser.parse_args()
jar=pathlib.Path(args.jar).resolve()
if not jar.is_file(): parser.error("Forge jar missing")

files=[
"forge-ai/src/main/java/forge/ai/AiController.java",
]
def fetch(path):
    url=f"https://raw.githubusercontent.com/Card-Forge/forge/{args.tag}/{path}"
    with urllib.request.urlopen(url,timeout=90) as r:
        return r.read().decode("utf-8")
controller=fetch(files[0])

# Stock Forge 2.0.15 has no ApiType.Incubate AI mapping and falls back to
# CannotPlayAi. That is an AI support gap, NOT a Magic rules engine bug.
# Add a generic Incubate-specific willingness gate for ALL four players.
# Base SpellAbilityAi still enforces restrictions, target and payment logic.
incubate_dispatcher = fetch("forge-ai/src/main/java/forge/ai/SpellApiToAi.java")
dispatch_anchor = "            .put(ApiType.Token, TokenAi.class)"
if incubate_dispatcher.count(dispatch_anchor) != 1:
    raise ValueError("Forge SpellApiToAi Token map location changed")
if ".put(ApiType.Incubate," in incubate_dispatcher:
    raise ValueError("Incubate already has native AI support; do not double patch")
incubate_dispatcher = incubate_dispatcher.replace(
    dispatch_anchor,
    "            .put(ApiType.Incubate, IncubateAi.class)\n" + dispatch_anchor,
    1,
)
incubate_ai = r'''package forge.ai.ability;

import forge.ai.AiAbilityDecision;
import forge.ai.AiPlayDecision;
import forge.ai.SpellAbilityAi;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;

/** AI willingness for the real Forge Incubate rules effect.
 *
 * Unlike stock CannotPlayAi, permits consideration of legal affordable
 * Incubate actions for all AI players, without generating tokens itself.
 * Superclass enforces normal phase, cost, restriction and condition gates.
 * Forge's IncubateEffect continues to own all token creation rules.
 */
public final class IncubateAi extends SpellAbilityAi {
    @Override
    protected AiAbilityDecision checkApiLogic(final Player ai, final SpellAbility sa) {
        return new AiAbilityDecision(100, AiPlayDecision.WillPlay);
    }
}
'''

# V10 is a measurement layer, not a tactical-policy improvement.
# Instrument the original Forge per-decision FutureTask, keeping its timeout,
# strategic ordering, eligible choices and error-handling paths unchanged.
future_anchor = "        FutureTask<SpellAbility> future = new FutureTask<>(() -> {"
future_replacement = (
    "        final long evalBeginV10 = System.nanoTime();\n"
    "        final java.util.concurrent.atomic.AtomicReference<String> evalCandidateV10 = "
    "new java.util.concurrent.atomic.AtomicReference<>(\"<none>\");\n"
    "        final java.util.concurrent.atomic.AtomicInteger evalConsideredV10 = "
    "new java.util.concurrent.atomic.AtomicInteger();\n"
    "        final int evalAvailableV10 = all.size();\n"
    + future_anchor
)
if controller.count(future_anchor) != 1:
    raise ValueError("AiController FutureTask placement changed in upstream Forge")
controller = controller.replace(future_anchor, future_replacement, 1)

candidate_anchor = (
    "                // Don't add Counterspells to the \"normal\" playcard lookups\n"
)
candidate_instrument = (
    "                evalCandidateV10.set(sa.getHostCard() == null "
    "? \"<null>\" : sa.getHostCard().getName());\n"
    "                evalConsideredV10.incrementAndGet();\n"
)
if controller.count(candidate_anchor) != 1:
    raise ValueError("AiController counterspell processing anchor changed")
controller = controller.replace(candidate_anchor, candidate_instrument + candidate_anchor, 1)

get_anchor = "            return future.get(game.getAITimeout(), TimeUnit.SECONDS);"
get_replacement = (
    "            SpellAbility evalDecisionV10 = future.get(game.getAITimeout(), TimeUnit.SECONDS);\n"
    "            long evalElapsedV10 = (System.nanoTime() - evalBeginV10) / 1000000L;\n"
    "            if (evalElapsedV10 >= 1000) {\n"
    '                System.out.println("AI_EVAL_SLOW_V10: player=" + player.getName()\n'
    '                    + " globalTurn=" + game.getPhaseHandler().getTurn()\n'
    '                    + " phase=" + game.getPhaseHandler().getPhase()\n'
    '                    + " elapsedMs=" + evalElapsedV10 + " timeoutSecs=" + game.getAITimeout()\n'
    '                    + " listed=" + evalAvailableV10\n'
    '                    + " considered=" + evalConsideredV10.get()\n'
    '                    + " lastCandidate=" + evalCandidateV10.get());\n'
    "            }\n"
    "            return evalDecisionV10;"
)
if controller.count(get_anchor) != 1:
    raise ValueError("AiController timed FutureTask result anchor changed")
controller = controller.replace(get_anchor, get_replacement, 1)

catch_anchor = "            e.printStackTrace();\n            if (e instanceof TimeoutException) {"
catch_replacement = (
    "            if (e instanceof TimeoutException) {\n"
    '                System.out.println("AI_EVAL_TIMEOUT_V10: player=" + player.getName()\n'
    '                    + " globalTurn=" + game.getPhaseHandler().getTurn()\n'
    '                    + " phase=" + game.getPhaseHandler().getPhase()\n'
    '                    + " elapsedMs=" + ((System.nanoTime() - evalBeginV10) / 1000000L)\n'
    '                    + " timeoutSecs=" + game.getAITimeout()\n'
    '                    + " listed=" + evalAvailableV10\n'
    '                    + " considered=" + evalConsideredV10.get()\n'
    '                    + " lastCandidate=" + evalCandidateV10.get());\n'
    "            }\n"
    + catch_anchor
)
if controller.count(catch_anchor) != 1:
    raise ValueError("AiController AI timeout catch anchor changed")
controller = controller.replace(catch_anchor, catch_replacement, 1)

# V13: previously tested 5->10->15s adaptation, equal across all four seats.
# This does NOT bypass legality, pick a card for the AI, or modify opponents.
# A timed-out evaluation still fails; only subsequent decisions get more time.
adaptive_anchor = (
    "            e.printStackTrace();\n"
    "            if (e instanceof TimeoutException) {"
)
adaptive_replacement = (
    "            if (e instanceof TimeoutException && game.AI_TIMEOUT < 15) {\n"
    "                int previousV13 = game.AI_TIMEOUT;\n"
    "                game.AI_TIMEOUT = Math.min(15, previousV13 + 5);\n"
    '                System.out.println("AI_ADAPTIVE_BUDGET_V13: previousSeconds="\n'
    '                    + previousV13 + " currentSeconds=" + game.AI_TIMEOUT\n'
    '                    + " appliedTo=ALL_FOUR_SEATS");\n'
    "            }\n"
    + adaptive_anchor
)
if controller.count(adaptive_anchor)!=1:
    raise ValueError("Forge AI catch block changed; cannot safely patch adaptive timeout")
controller=controller.replace(adaptive_anchor,adaptive_replacement,1)




# Only Brimaz gets a modified opening-hand evaluation. Other players'
# original PlayerControllerAi path is left bytecode-identical.
player_controller=fetch("forge-ai/src/main/java/forge/ai/PlayerControllerAi.java")
mulligan_anchor=(
"    @Override\n"
"    public boolean mulliganKeepHand(Player firstPlayer, int cardsToReturn)  {\n"
"        return !ComputerUtil.wantMulligan(player, cardsToReturn);\n"
"    }\n"
)
# Observe all four AIs at each mulligan checkpoint; no private cards are
# exposed to any other AI. Counts are diagnostic log messages only.
opening_telemetry = (
    "        int openingLandsV10 = 0;\n"
    "        int openingCheapSpellsV10 = 0;\n"
    "        for (forge.game.card.Card openCardV10 : player.getCardsIn(ZoneType.Hand)) {\n"
    "            if (openCardV10.isLand()) openingLandsV10++;\n"
    "            else if (openCardV10.getCMC() <= 2) openingCheapSpellsV10++;\n"
    "        }\n"
    '        System.out.println("AI_OPENING_V10: player=" + player.getName()\n'
    '            + " hand=" + player.getCardsIn(ZoneType.Hand).size()\n'
    '            + " lands=" + openingLandsV10\n'
    '            + " cheapSpells=" + openingCheapSpellsV10\n'
    '            + " cardsToBottom=" + cardsToReturn);\n'
)

mulligan_inject=(
"    @Override\n"
"    public boolean mulliganKeepHand(Player firstPlayer, int cardsToReturn)  {\n"
    + opening_telemetry
+ "        boolean stockKeep = !ComputerUtil.wantMulligan(player, cardsToReturn);\n"
"        Boolean special = BrimazMulliganPolicy.overrideKeep(player, cardsToReturn, stockKeep);\n"
"        return special != null ? special.booleanValue() : stockKeep;\n"
"    }\n"
)
if player_controller.count(mulligan_anchor)!=1:
    raise ValueError("PlayerControllerAi mulligan anchor mismatch")
player_controller=player_controller.replace(mulligan_anchor,mulligan_inject,1)


anchor1="        SpellAbility chosenSa = chooseSpellAbilityToPlayFromList(saList, true);"
insert1=(
"        // OPT-IN Brimaz test policy: one affordable free Phyrexian-token sacrifice\n"
"        // during the second main phase, strictly before that end step.\n"
"        // Only explicitly audited sacrifice outlets with counter/proliferate payoff are eligible.\n"
"        BrimazTurnPlanner.diagnoseDecisionWindow(player, saList);\n"
"        SpellAbility develop = BrimazTurnPlanner.planDevelopment(player, saList);\n"
"        if (develop != null) {\n"
"            return develop;\n"
"        }\n"
"        SpellAbility defensiveIncubator = BrimazTurnPlanner.planDefensiveTransformation(player, saList);\n"
"        if (defensiveIncubator != null) {\n"
"            return defensiveIncubator;\n"
"        }\n"
"        SpellAbility brimazPlanned = BrimazTurnPlanner.plan(player, saList);\n"
"        if (brimazPlanned != null) {\n"
"            return brimazPlanned;\n"
"        }\n\n"
)
if controller.count(anchor1)!=1: raise ValueError("AiController original selection anchor mismatch")
controller=controller.replace(anchor1,insert1+anchor1,1)

anchor2=(
"    public CardCollectionView chooseSacrificeType(String type, SpellAbility ability, boolean effect, int amount, final CardCollectionView exclude) {\n"
"        if (simPicker != null) {"
)
replacement2=(
"    public CardCollectionView chooseSacrificeType(String type, SpellAbility ability, boolean effect, int amount, final CardCollectionView exclude) {\n"
"        CardCollectionView plannedSacrifice = BrimazTurnPlanner.chooseSacrifice(player, type, ability, amount);\n"
"        if (plannedSacrifice != null) {\n"
"            return plannedSacrifice;\n"
"        }\n"
"        if (simPicker != null) {"
)
if controller.count(anchor2)!=1: raise ValueError("AiController payment selection anchor mismatch")
controller=controller.replace(anchor2,replacement2,1)
# Exception only for the specific Spawning Pit sacrifice ability and only
# while the Brimaz planner's narrow legal opportunity is active.
remove_anchor=("return spellAbility.isLandAbility() || "
    "(spellAbility.getHostCard() != null && ComputerUtilCard.isCardRemAIDeck(spellAbility.getHostCard()));")
remove_replacement=("return spellAbility.isLandAbility() || "
    "(spellAbility.getHostCard() != null && ComputerUtilCard.isCardRemAIDeck(spellAbility.getHostCard()) "
    "&& !BrimazTurnPlanner.allowNormallyExcludedAbility(player, spellAbility));")
if controller.count(remove_anchor)!=1: raise ValueError("AiController anti-AI card filter mismatch")
controller=controller.replace(remove_anchor,remove_replacement,1)

planner=r'''package forge.ai;

import forge.game.ability.AbilityUtils;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.card.CardCollection;
import forge.game.card.CardCollectionView;
import forge.game.card.CardLists;
import forge.game.card.CounterType;
import forge.game.cost.CostSacrifice;
import forge.game.cost.CostTap;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;

import java.util.List;

/** Conservative experimental AI policy for Brimaz's each-end-step trigger.
 *
 * Exact timing: a Phyrexian must have died before the beginning of the end step.
 * Sacrificing after the end step starts is too late.
 *
 * No hidden information, no card creation, no rules patch, no illegal activation.
 * Never sacrifice Brimaz or another non-token creature; dynamic cap at 2-4 token power.
 * Do not force a sacrifice when a Phyrexian already died that turn.
 */
public final class BrimazTurnPlanner {
    private BrimazTurnPlanner() {}

    /**
     * Controlled engine-building policy. Before combat, establish Brimaz if the
     * creature spell is already LEGAL and payable according to the Forge engine.
     * Then prioritize transforming meaningful Incubators that can attack this
     * turn. Never create mana, waive commander tax, or override the stack.
     */
    public static SpellAbility planDevelopment(Player ai, List<SpellAbility> available) {
        if (ai == null || available == null || ai.getGame() == null) return null;
        var game = ai.getGame();
        var phase = game.getPhaseHandler();
        if (!phase.isPlayerTurn(ai) || !phase.is(PhaseType.MAIN1)
                || !game.getStack().isEmpty()) return null;
        boolean brimazOnField = false;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (c.getName().equals("Brimaz, Blight of Oreskos")) {
                brimazOnField = true;
                break;
            }
        }
        int opponentDamageThreat = 0;
        for (Player opp : ai.getOpponents()) {
            for (Card c : opp.getCardsIn(ZoneType.Battlefield)) {
                if (c.isCreature()) {
                    opponentDamageThreat = Math.max(opponentDamageThreat, c.getNetPower());
                }
            }
        }
        boolean criticalDefence = ai.getLife() <= 10 &&
                opponentDamageThreat >= Math.max(3, ai.getLife() / 2);
        if (!brimazOnField && !criticalDefence) {
            for (SpellAbility sa : available) {
                if (sa == null || sa.getHostCard() == null || !sa.isSpell()
                        || !sa.getHostCard().getName().equals("Brimaz, Blight of Oreskos")
                        || !sa.getHostCard().isInZone(ZoneType.Command)) continue;
                sa.setActivatingPlayer(ai);
                if (!sa.canPlay() || !sa.canCastTiming(ai)
                        || !ComputerUtilCost.canPayCost(sa, ai, false)) continue;
                System.out.println("BRIMAZ_DEVELOPMENT: cast-commander turn="
                        + phase.getTurn() + " player=" + ai.getName());
                return sa;
            }
        }
        // Construct enabling artifacts rather than restricting the AI to an
        // 8- or 9-card functional deficit. Costs and casting legality remain
        // governed by Forge. Keep tutoring/reanimation disabled until tested.
        for (String chosen : new String[]{"Orzhov Signet", "Spawning Pit", "Krark-Clan Ironworks"}) {
            for (SpellAbility sa : available) {
                if (!usefulBlockedSpell(ai, sa) ||
                        !sa.getHostCard().getName().equals(chosen)) continue;
                sa.setActivatingPlayer(ai);
                if (!sa.canPlay() || !sa.canCastTiming(ai) ||
                        !ComputerUtilCost.canPayCost(sa, ai, false)) continue;
                System.out.println("BRIMAZ_DEVELOPMENT: cast-engine turn="
                        + phase.getTurn() + " card=" + chosen);
                return sa;
            }
        }
        for (SpellAbility sa : available) {
            if (sa == null || sa.getHostCard() == null || !sa.isActivatedAbility()
                    || sa.getApi() != ApiType.SetState
                    || !"Transform".equals(sa.getParam("Mode"))) continue;
            Card card = sa.getHostCard();
            if (!card.isInZone(ZoneType.Battlefield) ||
                    !card.getName().equals("Incubator Token") ||
                    card.getController() != ai || card.hasSickness()) continue;
            int size = card.getCounters(CounterType.getType("P1P1"));
            if (size < 3) continue;
            sa.setActivatingPlayer(ai);
            if (!sa.canPlay() || !sa.canCastTiming(ai)
                    || !ComputerUtilCost.canPayCost(sa, ai, false)) continue;
            System.out.println("BRIMAZ_DEVELOPMENT: transform-incubator turn="
                    + phase.getTurn() + " size=" + size);
            return sa;
        }
        return null;
    }

    // Only this single AI deck gets experimental access to cards marked
    // AI:RemoveDeck:All. Other seats keep Forge's unchanged stock heuristics.
    private static boolean isBrimazPilot(Player ai) {
        for (Card c : ai.getCardsIn(ZoneType.Command)) {
            if (c.getName().equals("Brimaz, Blight of Oreskos")) return true;
        }
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (c.getName().equals("Brimaz, Blight of Oreskos")) return true;
        }
        return false;
    }

    private static int phyrexianOnBattlefield(Player ai) {
        int n=0;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (c.isCreature() && c.getType().hasCreatureType("Phyrexian")) n++;
        }
        return n;
    }

    private static int artifactsOnBattlefield(Player ai) {
        int n=0;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (c.isArtifact()) n++;
        }
        return n;
    }

    private static boolean usefulBlockedSpell(Player ai, SpellAbility sa) {
        if (!isBrimazPilot(ai) || sa == null || sa.getHostCard() == null
                || !sa.isSpell() || !sa.getHostCard().isInZone(ZoneType.Hand)) return false;
        String n=sa.getHostCard().getName();
        if (n.equals("Orzhov Signet")) return true; // mana stabilization
        if (n.equals("Spawning Pit")) return phyrexianOnBattlefield(ai)>=1;
        if (n.equals("Krark-Clan Ironworks")) return artifactsOnBattlefield(ai)>=3;
        return false;
    }

    private static boolean isOutlet(SpellAbility sa) {
        if (sa == null || sa.getHostCard() == null || !sa.isActivatedAbility()
                || sa.getPayCosts() == null
                || !sa.getPayCosts().hasSpecificCostType(CostSacrifice.class)) return false;
        String name = sa.getHostCard().getName();
        int parts = sa.getPayCosts().getCostParts().size();
        boolean plainSac = parts == 1 && sa.getApi() == ApiType.PutCounter;
        if (plainSac && (name.equals("Arcbound Ravager")
                || name.equals("Bartolomé del Presidio")
                || name.equals("Spawning Pit"))) return true;
        return (name.equals("Throne of Geth") && sa.getApi() == ApiType.Proliferate
                && parts == 2 && sa.getPayCosts().hasSpecificCostType(CostTap.class))
                || (name.equals("Krark-Clan Ironworks") && sa.getApi() == ApiType.Mana
                && parts == 1);
    }

    public static boolean allowNormallyExcludedAbility(Player ai, SpellAbility sa) {
        // Only whitelist three specific spell CASTS after normal mana and timing checks.
        // Phyrexian Reclamation / Diabolic Intent / Delver remain disabled
        // until the AI can select their recursion/tutor targets correctly.
        if (usefulBlockedSpell(ai, sa)) return true;
        if (sa == null || sa.getHostCard() == null
                || !(sa.getHostCard().getName().equals("Spawning Pit")
                      || sa.getHostCard().getName().equals("Throne of Geth")
                      || sa.getHostCard().getName().equals("Krark-Clan Ironworks"))
                || !needEndStepDeath(ai) || !isOutlet(sa)) return false;
        CostSacrifice sac = sa.getPayCosts().getCostPartByType(CostSacrifice.class);
        return sac != null && selectToken(ai, sac.getType(), sa, sac.getAbilityAmount(sa)) != null;
    }

    // Counterfactual score of triggering Brimaz this end step. The scoring
    // method has no Forge dependencies, which makes tactical unit tests possible.
    // NOT a true rollout: it is intentionally a bounded one-action policy.
    public static int scoreHypothetical(int power, int friendlyCounterPermanents,
                                        int enemyNegativeCounterPermanents,
                                        int deathDrainEngines, int proliferateDrainEngines,
                                        int aiLife, int greatestOppPower, String outlet) {
        // Brimaz deck does not inflict poison; no artificial poison payoff.
        // We evaluate real friendly +1/+1 / charge counter growth and life-drain.
        int countersBenefit = friendlyCounterPermanents * 3
                + enemyNegativeCounterPermanents * 2;
        int isThrone = outlet.equals("Throne of Geth") ? 1 : 0;
        int immediate = isThrone == 1 ? countersBenefit : 3;
        int deathBenefit = deathDrainEngines * 4;
        int proliferationDrain = proliferateDrainEngines * (5 + 5 * isThrone);
        int tokenCost = 2 + Math.max(0, power) * 3;
        int danger = (aiLife <= 12 && greatestOppPower >= aiLife / 2) ? 7 : 0;
        return countersBenefit + immediate + deathBenefit
                + proliferationDrain - tokenCost - danger;
    }

    private static boolean needEndStepDeath(Player ai) {
        if (ai == null || ai.getGame() == null) return false;
        var game = ai.getGame();
        var phase = game.getPhaseHandler();
        // MAIN2 is the last consistent pre-end-step priority window.
        // The ability also triggers on the controller's own end step.
        if (!phase.is(PhaseType.MAIN2) || !game.getStack().isEmpty()) return false;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (!c.getName().equals("Brimaz, Blight of Oreskos")) continue;
            int deaths = AbilityUtils.calculateAmount(c, c.getSVar("X"), null);
            return deaths == 0;
        }
        return false;
    }

    private static int evaluate(Player ai, Card token, String outlet) {
        int positive = 0;
        for (Card friendly : ai.getCardsIn(ZoneType.Battlefield)) {
            if (friendly != token && friendly.hasCounters()) positive++;
        }
        int deathDrain = 0;
        int proliferateDrain = 0;
        for (Card friendly : ai.getCardsIn(ZoneType.Battlefield)) {
            String n = friendly.getName();
            if (n.equals("Marionette Apprentice") || n.equals("Elas il-Kor, Sadistic Pilgrim")
                    || n.equals("Mirkwood Bats") ||
                    (n.equals("Marionette Master") && token.isArtifact())) deathDrain++;
            if (n.equals("Scheming Aspirant")) proliferateDrain++;
        }
        int negativeOpp = 0;
        int highestOppThreat = 0;
        for (Player enemy : ai.getOpponents()) {
            for (Card c : enemy.getCardsIn(ZoneType.Battlefield)) {
                if (c.hasCounters() && c.isCreature()) {
                    for (var counter : c.getCounters().elementSet()) {
                        if (ComputerUtil.isNegativeCounter(counter, c)) {
                            negativeOpp++;
                            break;
                        }
                    }
                }
                if (c.isCreature()) highestOppThreat = Math.max(highestOppThreat, c.getNetPower());
            }
        }
        return scoreHypothetical(token.getNetPower(), positive, negativeOpp,
                deathDrain, proliferateDrain, ai.getLife(), highestOppThreat, outlet);
    }

    private static CardCollectionView selectToken(Player ai, String costType,
                                                   SpellAbility sa, int amount) {
        if (amount != 1 || !isOutlet(sa)) return null;
        Card source = sa.getHostCard();
        CardCollection valid = CardLists.getValidCards(ai.getCardsIn(ZoneType.Battlefield),
                costType.split(";"), ai, source, sa);
        Card selected = null;
        int bestScore = 0; // strictly positive utility required
        for (Card c : valid) {
            if (!c.isToken() || !c.isCreature() || !c.getType().hasCreatureType("Phyrexian")
                    || c == source || !c.canBeSacrificedBy(sa, false)
                    || c.getNetPower() > 4) continue;
            int score = evaluate(ai, c, source.getName());
            if (score > bestScore) {
                selected = c;
                bestScore = score;
            }
        }
        if (selected == null) return null;
        CardCollection result = new CardCollection();
        result.add(selected);
        return result;
    }

    public static CardCollectionView chooseSacrifice(Player ai, String type,
                                                       SpellAbility sa, int amount) {
        if (!needEndStepDeath(ai) || !isOutlet(sa)) return null;
        return selectToken(ai, type, sa, amount);
    }

    // V7 telemetry-only: first observed empty-stack MAIN2 decision in each
    // full-game turn. No game action is modified and no private opponent zone
    // is read. A token here is a candidate, NOT proof it may be sacrificed.
    private static int diagnosticTurn = Integer.MIN_VALUE;

    public static void diagnoseDecisionWindow(Player ai, List<SpellAbility> available) {
        if (ai == null || ai.getGame() == null || !isBrimazPilot(ai)) return;
        var game = ai.getGame();
        var phase = game.getPhaseHandler();
        if (!phase.is(PhaseType.MAIN2) || !game.getStack().isEmpty()) return;
        int turn = phase.getTurn();
        if (diagnosticTurn == turn) return;
        diagnosticTurn = turn;
        boolean hasBrimaz = false;
        int deaths = -1;
        int candidateTokens = 0;
        int liveOutletCards = 0;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (c.getName().equals("Brimaz, Blight of Oreskos")) {
                hasBrimaz = true;
                deaths = AbilityUtils.calculateAmount(c, c.getSVar("X"), null);
            }
            if (c.isToken() && c.isCreature() && c.getType().hasCreatureType("Phyrexian")
                    && c.getNetPower() <= 4) candidateTokens++;
            String n = c.getName();
            if (n.equals("Arcbound Ravager") || n.equals("Spawning Pit")
                    || n.equals("Throne of Geth") || n.equals("Krark-Clan Ironworks")
                    || n.equals("Bartolomé del Presidio")) liveOutletCards++;
        }
        int listedOutlets = 0;
        if (available != null) {
            for (SpellAbility sa : available) {
                if (isOutlet(sa)) listedOutlets++;
            }
        }
        System.out.println("BRIMAZ_WINDOW: V7 turn=" + turn
                + " active=" + phase.getPlayerTurn().getName()
                + " selfTurn=" + phase.isPlayerTurn(ai)
                + " brimazOnBattlefield=" + hasBrimaz
                + " phyrexianDeathsSoFar=" + deaths
                + " candidatePhyrexianTokens=" + candidateTokens
                + " outletCardsOnBattlefield=" + liveOutletCards
                + " listedSacrificeOutletAbilities=" + listedOutlets
                + " availableAbilities=" + (available == null ? 0 : available.size()));
    }

    /**
     * V8 conservative defensive Incubator timing experiment.
     * Incubators are not creatures until transformed: an untransformed token
     * cannot block or be used as a Phyrexian creature sacrifice. Unlike V6,
     * never require absence of summoning sickness just to pay {2} to transform.
     *
     * Independent deterministic policy test. This is a heuristic, not a
     * guarantee that transforming is the optimal multiplayer decision.
     */
    public static boolean shouldTransformForDefense(int counters, int life,
                                                     int greatestThreatPower, int readyBlockers) {
        return counters >= 2 && greatestThreatPower >= 3 && readyBlockers <= 1
                && life <= Math.max(22, greatestThreatPower * 3);
    }

    public static SpellAbility planDefensiveTransformation(Player ai,
                                                            List<SpellAbility> available) {
        if (!isBrimazPilot(ai) || available == null || ai.getGame() == null) return null;
        var phase = ai.getGame().getPhaseHandler();
        if (!phase.isPlayerTurn(ai) || !phase.is(PhaseType.MAIN2)
                || !ai.getGame().getStack().isEmpty()) return null;
        int greatestThreatPower = 0;
        for (Player enemy : ai.getOpponents()) {
            for (Card c : enemy.getCardsIn(ZoneType.Battlefield)) {
                if (c.isCreature()) greatestThreatPower = Math.max(greatestThreatPower, c.getNetPower());
            }
        }
        int readyBlockers = 0;
        for (Card card : ai.getCardsIn(ZoneType.Battlefield)) {
            if (card.isCreature() && !card.isTapped() && card.getNetToughness() >= 2) readyBlockers++;
        }
        for (SpellAbility sa : available) {
            if (sa == null || sa.getHostCard() == null || !sa.isActivatedAbility()
                    || sa.getApi() != ApiType.SetState || !"Transform".equals(sa.getParam("Mode"))) continue;
            Card inc = sa.getHostCard();
            if (!inc.isInZone(ZoneType.Battlefield) || inc.getController() != ai
                    || !inc.getName().equals("Incubator Token")) continue;
            int counters = inc.getCounters(CounterType.getType("P1P1"));
            if (!shouldTransformForDefense(counters, ai.getLife(), greatestThreatPower, readyBlockers)) continue;
            sa.setActivatingPlayer(ai);
            if (!sa.canPlay() || !sa.canCastTiming(ai) || !ComputerUtilCost.canPayCost(sa, ai, false)) continue;
            System.out.println("BRIMAZ_DEFENSE: transform-incubator turn=" + phase.getTurn()
                    + " size=" + counters + " life=" + ai.getLife()
                    + " opponentMaxPower=" + greatestThreatPower + " readyBlockers=" + readyBlockers);
            return sa;
        }
        return null;
    }

    public static SpellAbility plan(Player ai, List<SpellAbility> available) {
        if (!needEndStepDeath(ai) || available == null) return null;
        SpellAbility best = null;
        int bestScore = 0;
        for (SpellAbility sa : available) {
            if (!isOutlet(sa)) continue;
            sa.setActivatingPlayer(ai);
            CostSacrifice cost = sa.getPayCosts().getCostPartByType(CostSacrifice.class);
            if (cost == null) continue;
            CardCollectionView chosen = selectToken(ai, cost.getType(), sa, cost.getAbilityAmount(sa));
            if (chosen == null || chosen.isEmpty()) continue;
            if (!sa.canPlay() || !sa.canCastTiming(ai)) continue;
            if (!ComputerUtilCost.canPayCost(sa, ai, false)) continue;
            int score = evaluate(ai, chosen.get(0), sa.getHostCard().getName());
            if (score > bestScore) {
                bestScore = score;
                best = sa;
            }
        }
        if (best != null) {
            System.out.println("BRIMAZ_PLANNER: V7 score=" + bestScore
                    + " turn=" + ai.getGame().getPhaseHandler().getTurn()
                    + " active=" + ai.getGame().getPhaseHandler().getPlayerTurn().getName()
                    + " outlet=" + best.getHostCard().getName());
        }
        return best;
    }
}
'''
mulligan_policy=r'''package forge.ai;

import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.zone.ZoneType;

/**
 * V9 opt-in Brimaz opening-hand policy.
 *
 * Preserve Commander London's normal mulligan and bottoming processes: the
 * engine is still fully responsible for drawing, shuffling and hand sizing.
 * For Brimaz only, spend a no-bottoming free mulligan on an opening hand
 * with exactly 2 possible land drops, no cheap ramp/draw, and >=2 cards
 * costing three or more mana. Subsequent mulligans retain Forge's default
 * decision because a second mulligan incurs a real hand-size cost.
 *
 * Basic test: pure decision gate without Forge side effects.
 * Not a simulation of draw probability or a statement of optimal play.
 */
public final class BrimazMulliganPolicy {
    private BrimazMulliganPolicy() {}

    public static boolean wantFreeMulligan(int potentialLandDrops, int cheapRamp,
                                           int cheapDraw, int expensiveCards,
                                           int cardsToReturn) {
        return cardsToReturn == 0 && potentialLandDrops == 2
                && cheapRamp == 0 && cheapDraw == 0 && expensiveCards >= 2;
    }

    public static Boolean overrideKeep(Player player, int cardsToReturn, boolean stockKeep) {
        if (player == null || player.getGame() == null) return null;
        boolean isBrimaz = false;
        for (Card c : player.getCardsIn(ZoneType.Command)) {
            if (c.getName().equals("Brimaz, Blight of Oreskos")) {
                isBrimaz = true;
                break;
            }
        }
        if (!isBrimaz) return null;

        int lands = 0;
        int potentialLandDrops = 0;
        int ramp = 0;
        int cheapDraw = 0;
        int expensive = 0;
        int hand = 0;
        for (Card c : player.getCardsIn(ZoneType.Hand)) {
            hand++;
            String n = c.getName();
            if (c.isLand()) {
                lands++;
                potentialLandDrops++;
                continue;
            }
            // Named modal double-faced cards in this unmodified V3 deck.
            // Their land face is available through ordinary Forge card rules.
            if (n.equals("Agadeem's Awakening") || n.equals("Malakir Rebirth")
                    || n.equals("Witch Enchanter")) {
                potentialLandDrops++;
                continue;
            }
            if (n.equals("Sol Ring") || n.equals("Arcane Signet")
                    || n.equals("Talisman of Hierarchy") || n.equals("Orzhov Signet")
                    || n.equals("Ornithopter of Paradise") || n.equals("Gold Myr")) {
                ramp++;
            }
            // A spell requiring an existing creature to sacrifice (e.g.
            // Deadly Dispute) is NOT guaranteed unconditional early draw.
            if (n.equals("Night's Whisper") || n.equals("Sign in Blood")) {
                cheapDraw++;
            }
            if (c.getCMC() >= 3) expensive++;
        }

        boolean extraMulligan = stockKeep
                && wantFreeMulligan(potentialLandDrops, ramp, cheapDraw, expensive, cardsToReturn);
        System.out.println("BRIMAZ_MULLIGAN: V9 hand=" + hand
                + " actualLands=" + lands + " potentialLandDrops=" + potentialLandDrops
                + " cheapRamp=" + ramp + " cheapDraw=" + cheapDraw
                + " expensive=" + expensive + " cardsToReturn=" + cardsToReturn
                + " stockKeep=" + stockKeep
                + " overrideFreeMulligan=" + extraMulligan);
        return extraMulligan ? Boolean.FALSE : null;
    }
}
'''
with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d)
    target=root/"forge"/"ai"
    target.mkdir(parents=True,exist_ok=True)
    (target/"AiController.java").write_text(controller,encoding="utf-8")
    (target/"PlayerControllerAi.java").write_text(player_controller,encoding="utf-8")
    (target/"BrimazMulliganPolicy.java").write_text(mulligan_policy,encoding="utf-8")
    (target/"SpellApiToAi.java").write_text(incubate_dispatcher,encoding="utf-8")
    ability_dir=target/"ability";ability_dir.mkdir(parents=True,exist_ok=True)
    (ability_dir/"IncubateAi.java").write_text(incubate_ai,encoding="utf-8")
    (target/"BrimazTurnPlanner.java").write_text(planner,encoding="utf-8")
    classes=root/"classes";classes.mkdir()
    command=["javac","--release","21","-cp",str(jar),"-d",str(classes),
             str(target/"AiController.java"),str(target/"BrimazTurnPlanner.java"),
             str(target/"PlayerControllerAi.java"),str(target/"BrimazMulliganPolicy.java"),
             str(target/"SpellApiToAi.java"),str(ability_dir/"IncubateAi.java")]
    print("COMPILING",len(controller),"AiController chars, Brimaz policy",len(planner),"chars",flush=True)
    subprocess.run(command,check=True,timeout=240)
    for name in ("AiController.class","BrimazTurnPlanner.class",
                 "PlayerControllerAi.class","BrimazMulliganPolicy.class","SpellApiToAi.class"):
        if not (classes/"forge"/"ai"/name).is_file():
            raise ValueError("Missing compiled "+name)
    subprocess.run(["jar","uf",str(jar),"-C",str(classes),"forge/ai/AiController.class",
                    "-C",str(classes),"forge/ai/BrimazTurnPlanner.class",
                    "-C",str(classes),"forge/ai/PlayerControllerAi.class",
                    "-C",str(classes),"forge/ai/BrimazMulliganPolicy.class",
                    "-C",str(classes),"forge/ai/SpellApiToAi.class",
                    "-C",str(classes),"forge/ai/ability/IncubateAi.class"],
                   check=True,timeout=180)
    print("COMPILED classes",[(x.name,x.stat().st_size) for x in (classes/"forge"/"ai").glob("*.class")],flush=True)
print("PATCHED_BRIMAZ_JAR_SHA256",hashlib.sha256(jar.read_bytes()).hexdigest(),flush=True)
