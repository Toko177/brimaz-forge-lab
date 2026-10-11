#!/usr/bin/env python3
"""Tests for human video reference indexing; no network or transcripts needed."""
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from index_human_edh_captions import build, parse_srt_vtt, seconds

def run():
    assert seconds("00:01:24.500")==84.5
    with tempfile.TemporaryDirectory() as tmp:
        cap=Path(tmp)/"test.srt"
        cap.write_text(
            "1\n00:00:01,250 --> 00:00:03,250\n"
            "I should attack their commander with the elves\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\n"
            "Pass the turn, nothing special\n\n"
            "3\n00:00:08,000 --> 00:00:09,000\n"
            "En réponse je sacrifie mon artefact\n",encoding="utf-8")
        rows=list(parse_srt_vtt(cap))
        assert len(rows)==3
        r=build("my-episode",cap,{"sources":[{
            "video_id":"my-episode","youtube_url":"https://www.youtube.com/watch?v=ALUxJPWwGUE"}]})
        assert r["unverified_candidate_count"]==2, r
        assert all(not c["annotation_is_ground_truth"] and c["status"]=="needs_review"
                   for c in r["candidates"])
        assert any("combat_or_elimination" in c["candidate_topics"] for c in r["candidates"])
        assert any("interaction_timing" in c["candidate_topics"] for c in r["candidates"])
    print("HUMAN_EDH_CAPTION_INDEX_TEST_PASS source_ground_truth=none")
if __name__=="__main__":
    run()
