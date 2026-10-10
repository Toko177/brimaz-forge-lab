import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from combat_jfr_probe import method_name,summarize

def frame(name, method):
    return {"method":{"type":{"name":name},"name":method}}

def sample(*frames):
    return {"type":"jdk.ExecutionSample","values":{
        "stackTrace":{"frames":[frame(a,b) for a,b in frames]}}}

class RealForgeJfrParseTests(unittest.TestCase):
    def test_cpu_hotspots_break_out_real_blocking_and_attacking(self):
        x={"recording":{"events":[
            sample(("forge/game/card/CardState","getReplacementEffects"),
                   ("forge/ai/AiBlockController","assignBlockers"),
                   ("forge/ai/ComputerUtilCombat","predictDamageTo")),
            sample(("forge/ai/AiAttackController","declareAttackers")),
            sample(("forge/ai/ComputerUtilMana","getSourcesForShards")),
            sample(("java/lang/Thread","run"))
        ]}}
        r=summarize(x)
        self.assertEqual(r["java_cpu_samples_reaching_forge_ai"],3)
        self.assertEqual(r["classified_ai_samples"]["block_assignment_or_prediction"],1)
        self.assertEqual(r["classified_ai_samples"]["attack_prediction"],1)
        self.assertEqual(r["classified_ai_samples"]["mana_search"],1)
        self.assertEqual(r["combat_related_samples"],2)
        self.assertEqual(r["share_of_cpu_samples_in_ai"],0.75)

    def test_missing_jfr_samples_do_not_invent_profile(self):
        r=summarize({"recording":{"events":[]}})
        self.assertEqual(r["events"],0)
        self.assertEqual(r["combat_related_samples"],0)

    def test_null_thread_and_stack_are_tolerated_not_counted(self):
        x={"recording":{"events":[{"type":"jdk.ExecutionSample","values":
             {"sampledThread":None,"stackTrace":None}}]}}
        r=summarize(x)
        self.assertEqual(r["java_cpu_samples_with_stack"],0)

    def test_unrelated_jvm_event_does_not_count_as_cpu_sample(self):
        r=summarize({"recording":{"events":[{"type":"jdk.CPULoad","values":{
             "stackTrace":{"frames":[frame("forge/ai/AiBlockController","assignBlockers")]}}}]}})
        self.assertEqual(r["java_cpu_samples_reaching_forge_ai"],0)

    def test_slash_delimited_jfr_method_owner_is_normalized(self):
        self.assertEqual(method_name(frame("forge/ai/AiBlockController","makeGoodBlocks")),
                         "forge.ai.AiBlockController.makeGoodBlocks")

if __name__=="__main__":
    unittest.main()
