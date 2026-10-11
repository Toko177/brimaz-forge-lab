package forge.ai;

import java.util.List;

/** Synthetic adversarial checks; NOT a claim of real-game performance. */
public final class MultiplayerEvidenceGateV36Checks {
    private static int checks=0;
    private static void ok(boolean yes,String reason) {
        checks++;if(!yes)throw new AssertionError(reason);
    }
    private static MultiplayerStrategicSearchV35.Table state(
            int mana,int lands,int handLands,int life,int worst,
            boolean commander,int tokenArtifacts) {
        return new MultiplayerStrategicSearchV35.Table(
            mana,lands,handLands,life,4,1,tokenArtifacts,tokenArtifacts,
            0,0,0,0,commander,worst,3,2,40,40,40,8);
    }
    private static MultiplayerStrategicSearchV35.CardPlan c(
            String name,int cost,MultiplayerStrategicModel.Role role,
            int features,boolean legal) {
        return new MultiplayerStrategicSearchV35.CardPlan(
            name,cost,role,role==MultiplayerStrategicModel.Role.CREATURE?3:0,
            features,legal);
    }
    public static void main(String[] unused) {
        var br=c("Brimaz, Blight of Oreskos",4,
            MultiplayerStrategicModel.Role.COMMANDER,0,true);
        var phy=c("Phyrexian Fleshgorger",3,
            MultiplayerStrategicModel.Role.CREATURE,
            MultiplayerStrategicSearchV35.PHYREXIAN_CAST,true);
        var vanilla=c("Vanilla",3,MultiplayerStrategicModel.Role.CREATURE,0,true);
        var rock=c("Arcane Signet",2,MultiplayerStrategicModel.Role.RAMP,0,true);
        var sol=c("Sol Ring",1,MultiplayerStrategicModel.Role.RAMP,
                  MultiplayerStrategicSearchV35.INSTANT_MANA,true);
        var myr=c("Gold Myr",2,MultiplayerStrategicModel.Role.RAMP,0,true);
        var altar=c("Ashnod's Altar",3,
            MultiplayerStrategicModel.Role.SAC_OUTLET,0,true);
        var safe=state(4,4,0,35,4,false,0);
        var commanderFirst=MultiplayerEvidenceGateV36.choose(
            safe,List.of(br,phy,vanilla),0);
        ok(commanderFirst!=null&&commanderFirst.selected()==br,
            "Brimaz before known Phyrexian in hand");
        ok(commanderFirst.reason().equals("BRIMAZ_BEFORE_KNOWN_PHYREXIAN"),
            "auditable reason");
        ok(MultiplayerEvidenceGateV36.choose(
            state(4,4,0,35,4,true,0),List.of(phy,vanilla),0).selected()==phy,
            "cast a real Phyrexian when Brimaz is present");
        var remotePhy=c("Uncastable 9-cost Phyrexian",9,
            MultiplayerStrategicModel.Role.CREATURE,
            MultiplayerStrategicSearchV35.PHYREXIAN_CAST,true);
        ok(MultiplayerEvidenceGateV36.choose(
            safe,List.of(br,remotePhy,vanilla),0)==null,
            "no invented affordable future Phyrexian");
        ok(MultiplayerEvidenceGateV36.choose(
            safe,List.of(br,vanilla),0)==null,
            "no speculative Brimaz preference without known Phyrexian");
        ok(MultiplayerEvidenceGateV36.choose(
            state(2,2,1,35,2,false,0),List.of(br,rock,vanilla),0)
            ==null,"no non-affordable alternatives: preserve stock ordering");
        ok(MultiplayerEvidenceGateV36.choose(
            state(2,2,1,35,2,false,0),List.of(br,rock,sol),0)
            .selected()==rock,"known ramp unlocks printed commander CMC");
        ok(MultiplayerEvidenceGateV36.choose(
            state(2,2,1,35,2,false,0),List.of(br,myr,sol),0)
            .selected()==sol,"exclude summoning-sick Myr from guaranteed ramp");
        ok(MultiplayerEvidenceGateV36.optimisticNextTurnRockMana("Gold Myr")==0,
            "Myr has no immediately available tap mana");
        ok(MultiplayerEvidenceGateV36.choose(
            state(4,4,0,8,18,false,0),List.of(br,phy,rock),0)==null,
            "acute public threat goes back to original Forge");
        ok(MultiplayerEvidenceGateV36.choose(
            state(4,4,0,35,1,false,6),List.of(altar,vanilla),0)==null,
            "untransformed Incubators cannot justify creature sacrifice");
        ok(MultiplayerEvidenceGateV36.choose(
            safe,List.of(c("Brimaz, Blight of Oreskos",4,
                MultiplayerStrategicModel.Role.COMMANDER,0,false),phy),0)==null,
            "respect Forge timing and abstain");
        ok(MultiplayerEvidenceGateV36.choose(safe,List.of(phy),0)==null,
            "single feasible card needs no intervention");
        ok(MultiplayerEvidenceGateV36.choose(safe,List.of(),0)==null,
            "empty candidates fail closed");
        ok(MultiplayerEvidenceGateV36.choose(safe,null,0)==null,
            "null candidates fail closed");
        ok(MultiplayerEvidenceGateV36.choose(safe,List.of(br,phy),-1)==null,
            "invalid public token count fails closed");
        System.out.println("FOUR_AI_V36_EVIDENCE_SYNTHETIC_PASS checks="+checks
             +" realGamesClaimed=0");
    }
}
