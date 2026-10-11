#!/usr/bin/env python3
"""Small labeled synthetic parser fixture, NEVER a real Forge victory."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from analyze_four_ai_timeout_stacks import examine,classify

raw="""Turn: Turn 1 (Ai(1)-A)
AI_EVAL_SLOW_V10: player=Ai(2)-B globalTurn=10 phase=MAIN1 elapsedMs=1800 timeoutSecs=5 listed=12 considered=2 lastCandidate=Spell
AI_EVAL_TIMEOUT_V10: player=Ai(3)-C globalTurn=28 phase=COMBAT_BEGIN elapsedMs=5001 timeoutSecs=5 listed=7 considered=1 lastCandidate=Magic Damper
AI_ADAPTIVE_BUDGET_V13: previousSeconds=5 currentSeconds=10 appliedTo=ALL_FOUR_SEATS
AI eval thread at timeout:
    at forge.ai.ComputerUtilCombat.combatTriggerWillTrigger(ComputerUtilCombat.java:759)
    at forge.game.trigger.Trigger.requirementsCheck(Trigger.java:340)
    at forge.game.card.Card.getStaticAbilities(Card.java:6949)
OTHER
AI_EVAL_TIMEOUT_V10: player=Ai(1)-A globalTurn=30 phase=UPKEEP elapsedMs=10000 timeoutSecs=10 listed=9 considered=6 lastCandidate=Card Y
AI eval thread at timeout:
    at forge.game.replacement.ReplacementHandler.getReplacementList(ReplacementHandler.java:136)
    at forge.game.card.Card.updateReplacementEffects(Card.java:7021)
OTHER
"""
x,slow=examine(raw,{"pod":"fixture","policy":"synthetic-only"})
assert len(x)==2,x
assert len(slow)==1 and slow[0]["elapsed_ms"]==1800
assert x[0]["global_turn"]==28 and x[0]["player"]=="Ai(3)-C"
assert "combat_search" in x[0]["observed_stack_categories"]
assert "trigger_requirements" in x[0]["observed_stack_categories"]
assert "static_abilities" in x[0]["observed_stack_categories"]
assert "replacement_effects" in x[1]["observed_stack_categories"]
assert x[0]["last_visited_card_not_proven_cause"]=="Magic Damper"
assert x[0]["stack_available"] and len(x[0]["java_frames"])==3
assert classify([])==["unclassified"]
print("FOUR_AI_TIMEOUT_FORENSIC_UNIT_PASS fixture=synthetic_only tests=9")
