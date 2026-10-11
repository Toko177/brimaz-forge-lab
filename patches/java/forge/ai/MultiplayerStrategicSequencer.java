package forge.ai;

import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Four-SEAT bridge into genuine Forge card and mana legality. The model is
 * an abstract tempo forecast; it neither fabricates simulated future states
 * nor changes resolution, costs, stack timing, combat legality or card rules.
 *
 * Only voluntary, non-targeting permanent spells on an EMPTY stack and the
 * active player's main phase. All instants, interaction, alternative casting
 * modes, triggered abilities and hidden opponent cards use STOCK Forge AI.
 *
 * Opt-in -Dbrimaz.v33MultiplayerStrategicPlanner=true.
 */
public final class MultiplayerStrategicSequencer {
    private MultiplayerStrategicSequencer() {}
    public static final boolean ENABLED =
        Boolean.getBoolean("brimaz.v33MultiplayerStrategicPlanner");

    private static final Set<String> ROCKS = Set.of(
        "Sol Ring", "Arcane Signet", "Orzhov Signet", "Fellwar Stone",
        "Mind Stone", "Thought Vessel", "Talisman of Hierarchy",
        "Talisman of Dominance", "Talisman of Progress", "Talisman of Conviction",
        "Ornithopter of Paradise", "Gold Myr", "Marble Diamond",
        "Charcoal Diamond", "Commander's Sphere");
    private static final Set<String> DRAW = Set.of(
        "Skullclamp", "Phyrexian Arena", "Esper Sentinel", "Rhystic Study",
        "Mystic Remora", "The One Ring", "Idol of Oblivion");
    private static final Set<String> OUTLETS = Set.of(
        "Spawning Pit", "Ashnod's Altar", "Phyrexian Altar",
        "Krark-Clan Ironworks", "Altar of Dementia", "Viscera Seer",
        "Carrion Feeder", "Woe Strider", "Yahenni, Undying Partisan");
    private static final Set<String> PROTECTION = Set.of(
        "Lightning Greaves", "Swiftfoot Boots", "Whispersilk Cloak");

    private static MultiplayerStrategicModel.Role role(Card c) {
        String name = c.getName();
        if (ROCKS.contains(name)) return MultiplayerStrategicModel.Role.RAMP;
        if (OUTLETS.contains(name)) return MultiplayerStrategicModel.Role.SAC_OUTLET;
        if (DRAW.contains(name)) return MultiplayerStrategicModel.Role.DRAW_ENGINE;
        if (PROTECTION.contains(name)) return MultiplayerStrategicModel.Role.PROTECTION;
        if (c.isCommander()) return MultiplayerStrategicModel.Role.COMMANDER;
        if (name.equals("Brimaz, Blight of Oreskos")
                || name.equals("Otharri, Suns' Glory")
                || name.equals("Adeline, Resplendent Cathar"))
            return MultiplayerStrategicModel.Role.TOKEN_ENGINE;
        if (c.isCreature()) return MultiplayerStrategicModel.Role.CREATURE;
        if (c.isArtifact() || c.isEnchantment() || c.isPlaneswalker())
            return MultiplayerStrategicModel.Role.ENGINE;
        return MultiplayerStrategicModel.Role.OTHER;
    }

    private static MultiplayerStrategicModel.Snapshot snapshot(Player ai) {
        int lands = 0, artifacts = 0, tokens = 0, creatures = 0, synergies = 0;
        for (Card c : ai.getCardsIn(ZoneType.Battlefield)) {
            if (c.isLand()) lands++;
            if (c.isArtifact()) artifacts++;
            if (c.isToken()) tokens++;
            if (c.isCreature()) creatures++;
            if (OUTLETS.contains(c.getName()) || DRAW.contains(c.getName())
                    || c.isCommander()) synergies++;
        }
        int most = 0, second = 0;
        // Every opponent independently contributes to combined pressure:
        // threat cannot be reduced to only the leader in 4-player EDH.
        for (Player opp : ai.getOpponents()) {
            int attack = 0, seen = 0;
            for (Card c : opp.getCardsIn(ZoneType.Battlefield)) {
                if (!c.isCreature()) continue;
                attack += Math.max(0, Math.min(15, c.getNetPower()));
                if (++seen == 28) break;
            }
            if (attack >= most) { second = most; most = attack; }
            else if (attack > second) second = attack;
        }
        int mana = Math.max(0, ComputerUtilMana.getAvailableManaEstimate(ai, true));
        return new MultiplayerStrategicModel.Snapshot(
            mana, lands, ai.getLife(), most, second, creatures, artifacts,
            tokens, synergies, ai.getCardsIn(ZoneType.Hand).size(),
            ai.getGame().getPhaseHandler().getTurn());
    }

    public static SpellAbility choose(Player ai, List<SpellAbility> available) {
        if (!ENABLED || ai == null || available == null || available.isEmpty()
                || ai.getGame() == null) return null;
        var game = ai.getGame();
        var phase = game.getPhaseHandler();
        if (!phase.isPlayerTurn(ai) ||
                !(phase.is(PhaseType.MAIN1) || phase.is(PhaseType.MAIN2))
                || !game.getStack().isEmpty()) return null;
        if (available.size() > 48 || ai.getCardsIn(ZoneType.Battlefield).size() > 50)
            return null;
        for (Player opp : ai.getOpponents()) {
            if (opp.getCardsIn(ZoneType.Battlefield).size() > 50) return null;
        }

        MultiplayerStrategicModel.Snapshot board = snapshot(ai);
        List<MultiplayerStrategicModel.Option> options = new ArrayList<>();
        Map<MultiplayerStrategicModel.Option, SpellAbility> actions = new IdentityHashMap<>();
        int possibleNow = 0;
        for (SpellAbility sa : available) {
            if (sa == null || sa.getHostCard() == null || !sa.isSpell()
                    || sa.usesTargeting() || sa.isLandAbility()
                    || sa.isCopied())
                continue;
            Card card = sa.getHostCard();
            if (!(card.isCreature() || card.isArtifact()
                    || card.isEnchantment() || card.isPlaneswalker())
                    || (!card.isInZone(ZoneType.Hand) &&
                        !card.isInZone(ZoneType.Command))) continue;
            int cost = Math.max(0, card.getCMC());
            // Payability is NEVER inferred from the approximate mana model.
            // Its real validation stays exclusively in Forge.
            sa.setActivatingPlayer(ai);
            boolean playable = sa.canPlay() && sa.canCastTiming(ai)
                    && ComputerUtilCost.canPayCost(sa, ai, false);
            if (playable) possibleNow++;
            MultiplayerStrategicModel.Option option =
                new MultiplayerStrategicModel.Option(
                    card.getName(), cost, role(card),
                    card.isCreature() ? Math.max(0, card.getNetPower()) : 0,
                    playable);
            options.add(option);
            actions.put(option, sa);
            if (options.size() >= 32) break;
        }
        if (possibleNow < 2) return null;
        MultiplayerStrategicModel.Choice choice =
            MultiplayerStrategicModel.choose(board, options);
        if (choice == null || choice.selected() == null || choice.runnerUp() == null
                || choice.margin() < 700 || choice.immediate() < 12) return null;

        SpellAbility sa = actions.get(choice.selected());
        if (sa == null || !sa.canPlay() || !sa.canCastTiming(ai)
                || !ComputerUtilCost.canPayCost(sa, ai, false)) return null;
        System.out.println("FOUR_AI_V33_STRATEGIC_PROPOSAL player=" + ai.getName()
            + " turn=" + board.turn() + " first=" + choice.selected().name()
            + " role=" + choice.selected().role()
            + " second=" + (choice.projectedNext() == null ? "none"
                                : choice.projectedNext().name())
            + " alternative=" + choice.runnerUp().name()
            + " immediate=" + choice.immediate()
            + " future=" + choice.future()
            + " margin=" + choice.margin()
            + " mana=" + board.mana() + " life=" + board.life()
            + " opponentPower1=" + board.worstOpponentPower()
            + " opponentPower2=" + board.secondOpponentPower()
            + " realForgeLegalAndPayable=true");
        return sa;
    }
}
