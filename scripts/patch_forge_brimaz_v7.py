#!/usr/bin/env python3
"""Build V7: V6-equivalent Brimaz AI with instrumentation of MAIN2 decision windows.

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
with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d)
    target=root/"forge"/"ai"
    target.mkdir(parents=True,exist_ok=True)
    (target/"AiController.java").write_text(controller,encoding="utf-8")
    (target/"BrimazTurnPlanner.java").write_text(planner,encoding="utf-8")
    classes=root/"classes";classes.mkdir()
    command=["javac","--release","21","-cp",str(jar),"-d",str(classes),
             str(target/"AiController.java"),str(target/"BrimazTurnPlanner.java")]
    print("COMPILING",len(controller),"AiController chars, Brimaz policy",len(planner),"chars",flush=True)
    subprocess.run(command,check=True,timeout=240)
    for name in ("AiController.class","BrimazTurnPlanner.class"):
        if not (classes/"forge"/"ai"/name).is_file():
            raise ValueError("Missing compiled "+name)
    subprocess.run(["jar","uf",str(jar),"-C",str(classes),"forge/ai/AiController.class",
                    "-C",str(classes),"forge/ai/BrimazTurnPlanner.class"],
                   check=True,timeout=180)
    print("COMPILED classes",[(x.name,x.stat().st_size) for x in (classes/"forge"/"ai").glob("*.class")],flush=True)
print("PATCHED_BRIMAZ_JAR_SHA256",hashlib.sha256(jar.read_bytes()).hexdigest(),flush=True)
