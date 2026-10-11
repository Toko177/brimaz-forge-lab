#!/usr/bin/env python3
"""Synthetic V35 audit fixture only. NEVER a fabricated Commander result."""
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_v35_real_search import audit

banner="Ai(1)-Brimaz Ai(2)-A Ai(3)-B Ai(4)-C\nTurn: Turn 3\n"
window=("FOUR_AI_V35_WINDOW player=Ai(2)-A turn=3 rawAbilities=17 "
  "eligiblePerms=4 estimatedMana=3 ranked=3 best=Arcane Signet "
  "plannedSecond=none plannedNext=Brimaz searchNodes=54 "
  "immediateForgeApprovalPending=true\n")
approved=("FOUR_AI_V35_STOCK_APPROVED player=Ai(2)-A turn=3 card=Arcane Signet "
  "rejectedEarlier=0 genuineForgeAIDecision=true\n")
rejected=("FOUR_AI_V35_STOCK_REJECTED player=Ai(3)-B turn=4 "
  "proposed=2 stockFallback=true\n")
tactical_window=("FOUR_AI_V35_TACTICAL_WINDOW player=Ai(1)-Brimaz turn=5 "
  "intervention=EXILE_SWEEP ownCreatures=1 enemyCreatures=12 "
  "worstOpponentPower=25 life=9 candidateSpells=2 "
  "originalForgeValidationPending=true\n")
tactical_approved=("FOUR_AI_V35_TACTICAL_STOCK_APPROVED player=Ai(1)-Brimaz "
  "turn=5 card=Sunfall rejectedEarlier=0 genuineForgeAIDecision=true\n")
tactical_rejected=("FOUR_AI_V35_TACTICAL_STOCK_REJECTED player=Ai(3)-B "
  "turn=6 rejected=2 stockFallback=true\n")
with tempfile.TemporaryDirectory() as td:
    d=Path(td)
    a=d/"a.log";b=d/"b.log"
    a.write_text(banner,encoding="utf-8")
    b.write_text(banner+window+approved+rejected+tactical_window+tactical_approved+tactical_rejected,encoding="utf-8")
    sha={str(i):"abcdef" for i in range(7)}
    def report():
        return {"type":"Actual Forge 2.0.15 four-AI Commander controlled real-game campaign A/B",
          "reference_provenance":{"policy":"v17_strict","canonical_seven_deck_sha256":sha},
          "experiment_provenance":{"policy":"v35_strategy","canonical_seven_deck_sha256":sha},
          "real_process_pairs":1,"real_forge_jvm_processes":2,
          "both_natural_pairs":1,"pairs_with_any_censor_or_fault":0,
          "natural_pairs_with_different_winner":1,
          "pairs":[{"reference":{"log":str(a),"status":"complete","winner":"Brimaz_V3","event_sha256":"1"},
                    "experiment":{"log":str(b),"status":"complete","winner":"Kaal_9594008","event_sha256":"2",
                                  "pod":"artifact","rotation":2}}]}
    x=audit(report())
    assert x["real_forge_jvms"]==2
    assert x["reference_is_byte_identical_to_stock_forge"] is False
    assert x["arm_natural_finishes"]=={"reference":1,"experiment":1}
    assert x["paired_natural_brimaz_wins"]["both_natural_pairs"]==1
    assert x["paired_brimaz_evidence"]["brimaz_wins_stock_reference"]==1
    assert x["paired_brimaz_evidence"]["brimaz_wins_v35"]==0
    assert x["paired_brimaz_evidence"]["stock_only_brimaz_wins"]==1
    assert x["paired_brimaz_evidence"]["two_sided_p_value_on_discordant_pairs"]==1.0
    assert x["paired_brimaz_evidence"]["insufficient_to_claim_general_ai_superiority"]
    stock=report()
    stock["reference_provenance"].update({
        "policy":"forge_stock","upstream_forge_unmodified":True,
        "upstream_byte_identical":True,"patches":[],
        "original_forge_sha256":"original",
        "patched_forge_sha256":"original",
    })
    assert audit(stock)["reference_is_byte_identical_to_stock_forge"] is True
    duel=report()
    duel["experiment_provenance"]["policy"]="v35_brimaz_duel"
    duel["pairs"][0]["experiment"]["seats"]=["Brimaz_V3","Kaal_1","Kaal_2","Kaal_3"]
    duel["pairs"][0]["reference"]["seats"]=["Brimaz_V3","Kaal_1","Kaal_2","Kaal_3"]
    # Approval belongs to seat 2, an opponent: the new audit MUST reject it.
    try:
        audit(duel)
        raise AssertionError("V35 brIMAZ-only policy leaked to a stock seat")
    except ValueError:
        pass
    duel["pairs"][0]["experiment"]["seats"]=["Kaal_1","Brimaz_V3","Kaal_2","Kaal_3"]
    duel["pairs"][0]["reference"]["seats"]=["Kaal_1","Brimaz_V3","Kaal_2","Kaal_3"]
    b.write_text(banner+window+approved+rejected,encoding="utf-8")
    assert audit(duel)["mixed_seat_brimaz_vs_v17_opponents"] is True
    stock["reference_provenance"]["patches"]=["patch_forge_brimaz_v13.py"]
    try:
        audit(stock)
        raise AssertionError("Patched Forge was passed as unmodified stock")
    except ValueError:
        pass
    assert x["actual_stock_forge_approved_strategic_actions_not_cast_proof"]==1
    assert x["approved_actions_by_seat"]=={2:1}
    assert x["candidate_slots_ranked"]==3
    assert x["stock_forge_rejections_before_fallback"]==2
    assert x["different_game_event_sequences"]==1
    assert x["approved_examples"][0]["card"]=="Arcane Signet"
    assert x["public_board_tactical_windows_logged"]==1
    assert x["tactical_stock_forge_approved_not_cast_proof"]==1
    assert x["tactical_approved_by_seat"]=={1:1}
    assert x["tactical_approved_by_card"]=={"Sunfall":1}
    assert x["tactical_candidates_rejected_by_forge"]==2
    b.write_text(banner+window+rejected,encoding="utf-8")
    no=audit(report())
    assert no["actual_stock_forge_approved_strategic_actions_not_cast_proof"]==0
    b.write_text(banner+tactical_approved,encoding="utf-8")
    try:
        audit(report())
        raise AssertionError("Tactical approval without public-board window accepted")
    except ValueError:
        pass
    b.write_text(banner+approved,encoding="utf-8")
    try:
        audit(report())
        raise AssertionError("Approval without search window accepted")
    except ValueError:
        pass
    a.write_text(banner+window+approved,encoding="utf-8")
    b.write_text(banner+window+approved,encoding="utf-8")
    try:
        audit(report())
        raise AssertionError("Control polluted by strategy logs")
    except ValueError:
        pass
    a.write_text(banner,encoding="utf-8")
    q=report()
    q["experiment_provenance"]["canonical_seven_deck_sha256"]={"altered":"not original"}
    try:
        audit(q)
        raise AssertionError("Altered canonical decks not rejected")
    except ValueError:
        pass
print("FOUR_AI_V35_SYNTHETIC_LOG_AUDIT_PASS no_real_games_claimed=true")
