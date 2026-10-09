#!/usr/bin/env python3
"""Build an opt-in Forge 2.0.15 Brimaz end-step sacrifice planner.

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
"        // on an opponent's second main phase, strictly before their end step.\n"
"        // Only explicitly audited sacrifice outlets with counter/proliferate payoff are eligible.\n"
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
        return name.equals("Throne of Geth") && sa.getApi() == ApiType.Proliferate
                && parts == 2 && sa.getPayCosts().hasSpecificCostType(CostTap.class);
    }

    public static boolean allowNormallyExcludedAbility(Player ai, SpellAbility sa) {
        // Spawning Pit has AI:RemoveDeck:All in Forge card script.
        // Allow ONLY its eligible one-sacrifice ability, not arbitrary other use.
        if (sa == null || sa.getHostCard() == null
                || !(sa.getHostCard().getName().equals("Spawning Pit")
                      || sa.getHostCard().getName().equals("Throne of Geth"))
                || !needEndStepDeath(ai) || !isOutlet(sa)) return false;
        CostSacrifice sac = sa.getPayCosts().getCostPartByType(CostSacrifice.class);
        return sac != null && selectToken(ai, sac.getType(), sa, sac.getAbilityAmount(sa)) != null;
    }

    private static boolean needEndStepDeath(Player ai) {
        if (ai == null || ai.getGame() == null) return false;
        var game = ai.getGame();
        var phase = game.getPhaseHandler();
        if (!phase.is(PhaseType.MAIN2) || !phase.getPlayerTurn().isOpponentOf(ai)
                || !game.getStack().isEmpty()) return false;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (!c.getName().equals("Brimaz, Blight of Oreskos")) continue;
            // Use the same turn-based history expression as the official Forge card.
            int deaths = AbilityUtils.calculateAmount(c, c.getSVar("X"), null);
            return deaths == 0;
        }
        return false;
    }

    private static CardCollectionView selectToken(Player ai, String costType, SpellAbility sa, int amount) {
        if (amount != 1 || !isOutlet(sa)) return null;
        Card source = sa.getHostCard();
        CardCollection valid = CardLists.getValidCards(ai.getCardsIn(ZoneType.Battlefield),
                costType.split(";"), ai, source, sa);
        Card selected = null;
        for (Card c : valid) {
            if (!c.isToken() || !c.isCreature() || !c.getType().hasCreatureType("Phyrexian")
                    || c == source || !c.canBeSacrificedBy(sa, false)
                    || c.getNetPower() > 4) continue;
            // More +1/+1/charge/loyalty counter permanents make a one-time
            // proliferate more valuable, allowing a slightly larger token cost.
            int counterPermanents = 0;
            for (Card friendly : ai.getCardsIn(ZoneType.Battlefield)) {
                if (friendly != c && friendly.hasCounters()) counterPermanents++;
            }
            int maxSacPower = 2 + Math.min(2, counterPermanents / 3);
            if (c.getNetPower() > maxSacPower) continue;
            if (selected == null || c.getNetPower() < selected.getNetPower()) selected = c;
        }
        if (selected == null) return null;
        CardCollection out = new CardCollection();
        out.add(selected);
        return out;
    }

    public static CardCollectionView chooseSacrifice(Player ai, String type, SpellAbility sa, int amount) {
        if (!needEndStepDeath(ai)) return null;
        if (!isOutlet(sa)) return null;
        return selectToken(ai, type, sa, amount);
    }

    public static SpellAbility plan(Player ai, List<SpellAbility> available) {
        if (!needEndStepDeath(ai) || available == null) return null;
        for (SpellAbility sa : available) {
            if (!isOutlet(sa)) continue;
            sa.setActivatingPlayer(ai);
            CostSacrifice sac = sa.getPayCosts().getCostPartByType(CostSacrifice.class);
            if (sac == null || selectToken(ai, sac.getType(), sa, sac.getAbilityAmount(sa)) == null) continue;
            if (!sa.canPlay() || !sa.canCastTiming(ai)) continue;
            if (!ComputerUtilCost.canPayCost(sa, ai, false)) continue;
            System.out.println("BRIMAZ_PLANNER: sacrifice Phyrexian token before opponent end step via "
                    + sa.getHostCard().getName() + " / active turn " + ai.getGame().getPhaseHandler().getPlayerTurn().getName());
            return sa;
        }
        return null;
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
