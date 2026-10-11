package forge.ai;

/** 23 adversarial checks — no mocked Forge matches or imagined wins. */
public final class MultiplayerSacrificeAccessV41Checks {
    private static int n=0;
    private static void ok(boolean b,String s){n++;if(!b)throw new AssertionError(s);}
    public static void main(String[] args) {
        var m=MultiplayerSacrificeAccessV41.class;
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz_V3",false),"canonical mixed-seat deck ID");
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz V3",false),"canonical display name");
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz_Challenger",true),"two-Brimaz mirror ID");
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz_Challenger_A",true),"four-Brimaz first ID");
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz_Challenger_B",true),"four-Brimaz second ID");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz_Reference",true),"reference ID isolated");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz_Reference_A",true),"reference A isolated");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz_Reference_B",true),"reference B isolated");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz_Challenger_A",false),"mirror forbidden in mixed mode");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz__Challenger_A",true),"reject malformed ID");
        ok(!MultiplayerSacrificeAccessV41.authorized("Other_Brimaz_Challenger_A",true),"no substring identity");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz_V3",true),"not a mirrored challenger");
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz Challenger",true),"single mirror pilot");
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz Challenger A",true),"first mirrored pilot");
        ok(MultiplayerSacrificeAccessV41.authorized("Brimaz Challenger B",true),"second mirrored pilot");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz Reference A",true),"mirror reference strictly isolated");
        ok(!MultiplayerSacrificeAccessV41.authorized("Kaal_23328062",false),"Kaal AI unchanged");
        ok(!MultiplayerSacrificeAccessV41.authorized("Brimaz Reference",false),"do not authorize false positives");
        ok(!MultiplayerSacrificeAccessV41.authorized("NotBrimaz_V3",false),"no substring abuse");
        ok(!MultiplayerSacrificeAccessV41.authorized(null,false),"null player fails closed");
        ok(MultiplayerSacrificeAccessV41.recognizedOutlet("Ashnod's Altar","Mana",true,1,false),
             "real Ashnod sacrifice mana outlet");
        ok(MultiplayerSacrificeAccessV41.recognizedOutlet("Phyrexian Altar","Mana",true,1,false),
             "real Phyrexian sacrifice mana outlet");
        ok(MultiplayerSacrificeAccessV41.recognizedOutlet("Krark-Clan Ironworks","Mana",true,1,false),
             "artifact mana outlet");
        ok(MultiplayerSacrificeAccessV41.recognizedOutlet("Spawning Pit","PutCounter",true,1,false),
             "charge counter outlet");
        ok(MultiplayerSacrificeAccessV41.recognizedOutlet("Throne of Geth","Proliferate",true,2,true),
             "tapped artifact proliferate");
        ok(!MultiplayerSacrificeAccessV41.recognizedOutlet("Throne of Geth","Proliferate",true,2,false),
             "Throne has tap cost and cannot be treated as a free sac");
        ok(!MultiplayerSacrificeAccessV41.recognizedOutlet("Yawgmoth, Thran Physician","PutCounter",true,1,false),
             "targeted removal requires separate target risk evaluation");
        ok(!MultiplayerSacrificeAccessV41.recognizedOutlet("Ashnod's Altar","Mana",false,1,false),
             "no free mana without actual sacrifice cost");
        ok(!MultiplayerSacrificeAccessV41.recognizedOutlet("Ashnod's Altar","Mana",true,2,false),
             "reject unfamiliar multi-cost ability");
        ok(MultiplayerSacrificeAccessV41.plausibleSacrificeFodder(true,true,true,2),
             "transformed phyrexian token");
        ok(!MultiplayerSacrificeAccessV41.plausibleSacrificeFodder(true,false,true,2),
             "untransformed incubator is an artifact");
        ok(!MultiplayerSacrificeAccessV41.plausibleSacrificeFodder(false,true,true,2),
             "never sacrifice non-token phyrexian creature");
        ok(!MultiplayerSacrificeAccessV41.plausibleSacrificeFodder(true,true,false,2),
             "ordinary token does not trigger Brimaz Phyrexian death");
        ok(!MultiplayerSacrificeAccessV41.plausibleSacrificeFodder(true,true,true,5),
             "protect important large token");
        System.out.println("FOUR_AI_V41_SAC_ACCESS_SYNTHETIC_PASS checks="+n+" realWinsClaimed=0");
    }
}
