#!/usr/bin/env python3
"""Index timestamped caption excerpts as human Commander tactical *candidates*.

Never equates narration with a legal move or invents public board state.
This indexes subtitles that are supplied/downloaded separately, and requires
manual video verification before use for regression training/score.
"""
import argparse
import json
import pathlib
import re
from collections import Counter

TAGS = {
    "combat_or_elimination": [
        "attack", "block", "combat", "lethal", "kill him", "kill her",
        "commander damage", "attaque", "bloque", "tuer", "létal", "degats de commandant",
    ],
    "interaction_timing": [
        "in response", "counterspell", "counter it", "removal", "destroy",
        "swords to plowshares", "response", "en réponse", "contre", "détruit",
        "anti-bête", "exile", "exilé",
    ],
    "table_threat_politics": [
        "threat", "deal", "board wipe", "scary", "dangerous", "promise",
        "menace", "marché", "politique", "nettoyer le board",
        "il va gagner", "elle va gagner",
    ],
    "resource_and_tempo": [
        "mana", "ramp", "draw", "card advantage", "hold up", "keep mana",
        "pioch", "garde", "terrain", "sacrif", "sacrifice",
    ],
    "commander_synergy": [
        "proliferate", "incubate", "counter", "infect",
        "prolif", "incub", "marqueur", "monarch", "monarqu", "initiative",
    ],
}
TIME = re.compile(r"(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})(?:[.,](?P<ms>\d{1,3}))?")
def seconds(s):
    match = TIME.search(s.strip())
    if not match:
        raise ValueError("Time not parseable: "+s)
    return int(match["h"])*3600 + int(match["m"])*60 + int(match["s"]) + int((match["ms"] or "0").ljust(3,"0"))/1000

def parse_srt_vtt(path):
    """Caption extraction, no OCR or hidden scene reconstruction."""
    data = path.read_text(encoding="utf-8-sig", errors="replace")
    chunks = re.split(r"\n\s*\n", data.replace("\r\n","\n"))
    for chunk in chunks:
        parts = chunk.strip().splitlines()
        positions = [(i, line) for i,line in enumerate(parts) if "-->" in line]
        if not positions:
            continue
        i, timecode = positions[0]
        try:
            start = seconds(timecode.split("-->")[0])
        except ValueError:
            continue
        joined = " ".join(parts[i+1:])
        clean = re.sub(r"<[^>]+>", "", joined)
        clean = re.sub(r"\s+", " ", clean).strip()
        if clean:
            yield start, clean

def classify(txt):
    low = txt.lower()
    return [tag for tag, words in TAGS.items() if any(word in low for word in words)]

def build(video_id, captions, sources):
    known={item["video_id"]:item for item in sources["sources"]}
    if video_id not in known:
        raise ValueError("Unknown source video ID")
    candidates=[]
    dedup=set()
    for timestamp, sentence in parse_srt_vtt(captions):
        tags=classify(sentence)
        if not tags: continue
        key=(round(timestamp),sentence.casefold())
        if key in dedup: continue
        dedup.add(key)
        candidates.append({
            "video_id":video_id,
            "youtube_url":known[video_id]["youtube_url"],
            "timestamp_seconds":round(timestamp,3),
            "caption_excerpt":sentence[:350],
            "candidate_topics":tags,
            "observed_action":None,
            "public_game_state":None,
            "verified_legal_options":None,
            "status":"needs_review",
            "annotation_is_ground_truth":False,
        })
    return {"video_id":video_id,"source":str(captions),
            "caption_segments_scanned":"All cues from input file",
            "unverified_candidate_count":len(candidates),
            "topics":dict(Counter(t for r in candidates for t in r["candidate_topics"])),
            "candidates":candidates,
            "rules":["No direct model supervision without frame/video verification.",
                     "The speaker can describe opponents, speculation or past events.",
                     "A transcript alone does not expose priority, legal choices or card identities.",
                     "Do not reproduce a complete copyrighted transcript in reports."]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--video-id",required=True)
    ap.add_argument("--captions",required=True,type=pathlib.Path)
    ap.add_argument("--index",type=pathlib.Path,default=pathlib.Path("human_reference/videos.json"))
    ap.add_argument("--out",type=pathlib.Path,required=True)
    a=ap.parse_args()
    r=build(a.video_id,a.captions,json.loads(a.index.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("HUMAN_EDH_CAPTION_CANDIDATES",json.dumps({
        "video_id":a.video_id,"candidate_count":r["unverified_candidate_count"],
        "topics":r["topics"],"verified_game_states":0}))
if __name__=="__main__":
    main()
