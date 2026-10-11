package forge.ai;

/**
 * V41 auditable seat isolation + genuinely useful existing sacrifice outlets.
 *
 * This is deliberately a narrowly typed admission rule, not a generic "play
 * all spells" bypass. Actual SpellAbility cost/timing/choice and resolution
 * remain under the real Forge 2.0.15 engine.
 */
public final class MultiplayerSacrificeAccessV41 {
    private MultiplayerSacrificeAccessV41() {}

    /** Four-Brimaz mirror names and the ORIGINAL canonical Brimaz deck ID
     * are disjoint. Both require the explicit challenger JVM flag.
     */
    public static boolean authorized(String playerName, boolean mirror) {
        if (playerName == null) return false;
        // Forge's actual getName() is "Ai(1)-Brimaz Challenger", not just
        // the deck Name= field or file basename. Only a strictly numbered
        // seat prefix and one of the exact permitted deck labels is accepted.
        if (playerName.startsWith("Ai(")) {
            if (playerName.length()<7 || playerName.charAt(4)!=')'
                    || playerName.charAt(5)!='-'
                    || playerName.charAt(3)<'1' || playerName.charAt(3)>'4')
                return false;
            playerName=playerName.substring(6);
        }
        if (mirror) {
            return playerName.equals("Brimaz_Challenger")
                || playerName.equals("Brimaz_Challenger_A")
                || playerName.equals("Brimaz_Challenger_B")
                || playerName.equals("Brimaz Challenger")
                || playerName.equals("Brimaz Challenger A")
                || playerName.equals("Brimaz Challenger B");
        }
        return playerName.equals("Brimaz_V3")
            || playerName.equals("Brimaz V3");
    }

    /**
     * Strictly recognize physical Forge sacrifice outlets and supported
     * activated ability classes. A payment requiring a sacrifice is mandatory.
     * Mana generation on the altar is useful but the AI must still demonstrate
     * net-positive Brimaz end-step payoff before giving up a real creature.
     */
    public static boolean recognizedOutlet(String cardName,String api,
                              boolean sacrificeCost,int costPartCount,
                              boolean hasTapCost) {
        if(!sacrificeCost || cardName == null || api == null ||
            costPartCount<1)return false;
        if(("Arcbound Ravager".equals(cardName)
             || "Bartolomé del Presidio".equals(cardName)
             || "Spawning Pit".equals(cardName))
             && "PutCounter".equals(api) && costPartCount==1)return true;
        if("Throne of Geth".equals(cardName) && "Proliferate".equals(api)
             && costPartCount==2 && hasTapCost)return true;
        if(("Krark-Clan Ironworks".equals(cardName)
             || "Ashnod's Altar".equals(cardName)
             || "Phyrexian Altar".equals(cardName))
             && "Mana".equals(api) && costPartCount==1)return true;
        return false;
    }

    /** Side-effect-free diagnostic: can this token be a plausible payment
     * for an end-step Brimaz trigger, before Forge checks real restrictions?
     * Do not accidentally treat an untransformed Incubator as a creature.
     */
    public static boolean plausibleSacrificeFodder(boolean token,
                 boolean creature,boolean phyrexian,int netPower) {
        return token && creature && phyrexian && netPower >= 0 && netPower <= 4;
    }
}
