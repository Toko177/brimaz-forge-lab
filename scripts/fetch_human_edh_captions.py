#!/usr/bin/env python3
"""Attempt authorized public subtitle access for verified Commander videos.

No full transcripts are persisted or republished. Store counts + timestamps
for short review candidates only. YouTube may block cloud IP addresses; record
the real exception rather than inventing a successful ingest.
"""
import argparse
import json
from pathlib import Path

from index_human_edh_captions import classify

def fetch_public_video_candidates(api, video, max_examples=12):
    language_pref=(["fr","fr-FR","en"] if video["channel"]=="Bandit"
                   else ["en","en-US","fr"])
    result={
        "video_id":video["video_id"], "youtube_url":video["youtube_url"],
        "channel":video["channel"],
        "status":"not_retrieved",
        "subtitles_language":None,
        "subtitle_segments_read":0,
        "unverified_candidate_count":0,
        "topic_counts":{},
        "samples_for_manual_verification":[],
        "error":None,
    }
    try:
        transcript=api.fetch(video["video_id"],languages=language_pref)
        result["status"]="captions_available"
        result["subtitles_language"]=transcript.language_code
        tally={}
        for row in transcript:
            result["subtitle_segments_read"]+=1
            tags=classify(row.text)
            if not tags: continue
            result["unverified_candidate_count"]+=1
            for k in tags:tally[k]=tally.get(k,0)+1
            if len(result["samples_for_manual_verification"]) < max_examples:
                # At most 12 snippets, each at most 100 characters; never
                # publish a full video caption track.
                result["samples_for_manual_verification"].append({
                    "timestamp_seconds":round(float(row.start),2),
                    "caption_excerpt":row.text[:100],
                    "candidate_topics":tags,
                    "human_action_verified":False,
                    "public_state_verified":False
                })
        result["topic_counts"]=tally
    except Exception as exc:
        result["status"]="blocked_or_unavailable"
        result["error"]=type(exc).__name__+": "+str(exc)[:220]
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--index",type=Path,default=Path("human_reference/videos.json"))
    p.add_argument("--out",type=Path,default=Path("results/human_edh/caption_fetch_report.json"))
    args=p.parse_args()
    from youtube_transcript_api import YouTubeTranscriptApi
    api=YouTubeTranscriptApi()
    catalog=json.loads(args.index.read_text(encoding="utf-8"))
    rows=[fetch_public_video_candidates(api,v) for v in catalog["sources"]]
    report={
        "source":"Official public YouTube captions through youtube-transcript-api; not game state.",
        "source_count":len(rows),
        "retrieved_count":sum(x["status"]=="captions_available" for x in rows),
        "fully_verified_game_states":0,
        "no_hidden_information_or_full_transcript_republication":True,
        "videos":rows
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("HUMAN_COMMANDER_VIDEO_FETCH",json.dumps({
        "source_count":len(rows),"retrieved_count":report["retrieved_count"],
        "statuses":[{"video_id":x["video_id"],"status":x["status"],
                     "error":x["error"]} for x in rows]
    },ensure_ascii=False),flush=True)
if __name__=="__main__":
    main()
