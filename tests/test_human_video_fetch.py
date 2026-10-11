#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fetch_human_edh_captions import fetch_public_video_candidates

class Snip:
    def __init__(self,start,text):
        self.start,self.text=start,text
class Captions:
    language_code="en"
    def __iter__(self):
        return iter([Snip(10.5,"In response I counter that spell"),
                     Snip(20.3,"Everyone passed the turn"),
                     Snip(26.0,"I attack with commander for lethal damage")])
class Works:
    def fetch(self,video_id,languages):
        assert video_id=="ALUxJPWwGUE"
        return Captions()
class Blocked:
    def fetch(self,video_id,languages):
        raise RuntimeError("Public subtitles cannot be fetched from this runner")
v={"video_id":"ALUxJPWwGUE","youtube_url":"https://www.youtube.com/watch?v=ALUxJPWwGUE","channel":"The Command Zone"}
a=fetch_public_video_candidates(Works(),v)
assert a["status"]=="captions_available",a
assert a["subtitle_segments_read"]==3,a
assert a["unverified_candidate_count"]==2,a
assert all(not x["human_action_verified"] and not x["public_state_verified"]
           for x in a["samples_for_manual_verification"]),a
b=fetch_public_video_candidates(Blocked(),v)
assert b["status"]=="blocked_or_unavailable",b
assert b["unverified_candidate_count"]==0,b
assert "RuntimeError" in b["error"],b
print("FOUR_SEAT_HUMAN_VIDEO_FETCH_TEST_PASS no fabricated episodes or plays")
