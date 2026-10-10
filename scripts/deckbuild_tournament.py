#!/usr/bin/env python3
"""Prepare and assemble a genuine multi-candidate Commander card-swap tournament.

One immutable reference, 2 fixed pods x 4 rotated seats, N independently
legality-checked candidate .dck decks. Share the actual eight baseline Forge
matches exactly once across candidate A/B certificates. Do not fabricate
missing games or alter Magic rules, decks, outcomes or AI player abilities.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

from deckbuild_prepare import prepare
from deckbuild_swaps import apply_swaps,save_candidate
from deckbuild_cache import stamp, validate_reference_logs
from deckbuild_run import OPPONENTS

SLUG=re.compile(r"[a-z][a-z0-9_-]{1,39}\Z")
FIRST="baseline"
POLICY="V13-incubate-adaptive"

def parse_recipe(path):
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    variants=payload.get("variants")
    if not isinstance(variants,list) or not 2<=len(variants)<=8:
        raise ValueError("Tournament requires 2 to 8 distinct experimental variants")
    ids=set(); swaps=set()
    for item in variants:
        if not isinstance(item,dict) or not SLUG.fullmatch(item.get("id","")):
            raise ValueError("Each variant requires a safe 2-40 character slug id")
        if item["id"]==FIRST or item["id"] in ids:
            raise ValueError("Duplicate or reserved variant id")
        if not isinstance(item.get("swaps"),str) or not item["swaps"].strip():
            raise ValueError("Each variant needs a nonempty swap recipe")
        if item["swaps"] in swaps:
            raise ValueError("Duplicate experimental swap recipe")
        ids.add(item["id"]);swaps.add(item["swaps"])
    if set(payload)!={"variants"}:
        raise ValueError("Tournament recipe accepts only a 'variants' list; reference is pinned by caller")
    return variants

def prepare_tournament(*,base,commander,recipe,opponents,root,repo_root,seed_base,repeats):
    variants=parse_recipe(recipe)
    if not (1<=repeats<=6 and isinstance(seed_base,int) and seed_base>=0):
        raise ValueError("Invalid tournament repeats/seed")
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    common=Path(opponents)
    for cards in OPPONENTS.values():
        for name in cards:
            if not (common/(name+".dck")).is_file():
                raise FileNotFoundError(f"Original Forge opponent deck is missing: {name}")
    manifests={}
    seen_hashes=set()
    baseline_hash=None
    for item in variants:
        slug=item["id"]
        counts,cmdrs,removed,added=apply_swaps(base,commander,item["swaps"])
        source=root/"input"/(slug+".txt")
        save_candidate(source,counts,cmdrs)
        dest=root/"variants"/slug/"forge_decks"
        m=prepare(base,source,dest,commander,commander)
        candsha=m["decks"]["candidate"]["forge_sha256"]
        refsha=m["decks"]["reference"]["forge_sha256"]
        if not m["delta"]["added"] or not m["delta"]["removed"]:
            raise ValueError(f"Variant {slug} makes no net card change")
        if candsha==refsha or candsha in seen_hashes:
            raise ValueError("Candidate is identical to reference or an earlier candidate")
        if baseline_hash is not None and baseline_hash!=refsha:
            raise ValueError("The original reference deck unexpectedly changed")
        baseline_hash=refsha;seen_hashes.add(candsha)
        for names in OPPONENTS.values():
            for name in names:
                shutil.copyfile(common/(name+".dck"),dest/(name+".dck"))
        manifests[slug]={"id":slug,"swaps":item["swaps"],
                         "candidate_sha256":candsha,"reference_sha256":refsha,
                         "added":m["delta"]["added"],"removed":m["delta"]["removed"]}
    first=variants[0]["id"]
    key=stamp(repo_root,root/"variants"/first/"forge_decks",
              root/"variants"/first/"forge_decks"/"candidate-manifest.json",
              seed_base=seed_base,repeats=repeats)
    (root/"reference-cache-key.json").write_text(json.dumps(key,indent=2)+"\n")
    expected=[]
    for role,slug in [("reference",first)]+[("candidate",x["id"]) for x in variants]:
        for pod in ("aristo","artifact"):
            for rot in range(4):
                expected.append({"arm":role,"variant":slug,"pod":pod,"rotation":rot})
    result={"version":1,"policy":POLICY,"seed_base":seed_base,"repeats":repeats,
            "reference_variant":first,"reference_fingerprint":key["fingerprint"],
            "reference_deck_sha256":baseline_hash,
            "variants":manifests,"jobs":expected,
            "scheduled":len(expected)*repeats,
            "expected_pods":["aristo","artifact"],"expected_rotations":[0,1,2,3],
            "caveat":"Exploratory card-swap screening; candidate wins require independent Forge/Scryfall certificates. Same seed does not imply the same game actions."}
    (root/"tournament.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    return result

def assemble(*,plan,game_root,output):
    """Fail closed if any of the eight baseline or any candidate shards is missing.

    Copy the ORIGINAL raw Forge bytes and manifests into an isolated A/B directory
    for each candidate. The existing independent deckbuild_certify.py then tests
    every original log hash, deck legality and the true four-player result.
    """
    plan=json.loads(Path(plan).read_text(encoding="utf-8"))
    game_root=Path(game_root)
    out=Path(output)
    if out.exists() and any(out.iterdir()):
        raise ValueError("Tournament staging output must be empty; no mixing runs")
    expected_jobs={(j["arm"],j["variant"],j["pod"],j["rotation"]) for j in plan["jobs"]}
    observed={}
    for f in sorted(game_root.rglob("games.json")):
        entries=json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(entries,list) or len(entries)!=plan["repeats"]:
            raise ValueError(f"Game shard is missing repeats: {f}")
        ex=entries[0]
        slug=f.parts[-4] if False else None
        arm=ex.get("arm")
        # Variant recorded by artifact path (cannot trust an unbound display name)
        candidates=[key for key in expected_jobs
                    if key[0]==arm and key[2]==ex.get("pod") and key[3]==ex.get("rotation")
                    and (arm=="reference" or plan["variants"][key[1]]["candidate_sha256"]==
                         ex.get("candidate_deck_sha256"))]
        if len(candidates)!=1:
            raise ValueError(f"Cannot tie genuine Forge shard to exactly one planned variant: {f}")
        k=candidates[0]
        if k in observed:
            raise ValueError(f"Duplicate tournament shard {k}")
        expected_label="Deck_Reference" if arm=="reference" else "Deck_Candidate"
        expected_sha=(plan["reference_deck_sha256"] if arm=="reference"
                      else plan["variants"][k[1]]["candidate_sha256"])
        if any(x.get("arm")!=arm or x.get("pod")!=k[2] or x.get("rotation")!=k[3] or
               x.get("repeat")!=i or x.get("candidate_deck")!=expected_label or
               x.get("candidate_deck_sha256")!=expected_sha or
               x.get("policy")!=plan["policy"] or
               x.get("seed")!=plan["seed_base"]+(100000 if k[2]=="artifact" else 0)
                                      +10000*k[3]+i
               for i,x in enumerate(entries)):
            raise ValueError(f"Forge data differs from announced immutable tournament matrix: {k}")
        for row in entries:
            src=f.parent/Path(row["log"]).name
            if not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest()!=row["log_sha256"]:
                raise ValueError("Missing/tampered original Forge game log")
        observed[k]=(entries,f)
    if set(observed)!=expected_jobs:
        raise ValueError(f"Missing actual Forge job shards: {sorted(expected_jobs-set(observed))}")
    for slug in plan["variants"]:
        for arm in ("reference","candidate"):
            keyslug=plan["reference_variant"] if arm=="reference" else slug
            for pod in ("aristo","artifact"):
                for rot in range(4):
                    entries,source=observed[arm,keyslug,pod,rot]
                    dest=out/slug/arm/pod/("rot"+str(rot))
                    dest.mkdir(parents=True,exist_ok=True)
                    (dest/"games.json").write_bytes(source.read_bytes())
                    for row in entries:
                        src=source.parent/Path(row["log"]).name
                        shutil.copyfile(src,dest/src.name)
    return {"variants":len(plan["variants"]),
            "shared_reference_games":8*plan["repeats"],
            "candidate_games":8*plan["repeats"]*len(plan["variants"]),
            "new_real_games":plan["scheduled"],
            "reports_expected":len(plan["variants"])}

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    prep=sub.add_parser("prepare")
    for flag in ("--base","--commander","--recipe","--opponents","--root","--repo-root"):
        prep.add_argument(flag,required=True)
    prep.add_argument("--seed-base",type=int,required=True)
    prep.add_argument("--repeats",type=int,default=1)
    assem=sub.add_parser("assemble")
    assem.add_argument("--plan",required=True)
    assem.add_argument("--game-root",required=True)
    assem.add_argument("--output",required=True)
    a=p.parse_args()
    if a.command=="prepare":
        result=prepare_tournament(base=a.base,commander=a.commander,recipe=a.recipe,
                                  opponents=a.opponents,root=a.root,repo_root=a.repo_root,
                                  seed_base=a.seed_base,repeats=a.repeats)
        print("TOURNAMENT_PREPARED",json.dumps({k:result[k] for k in
              ("scheduled","reference_fingerprint","variants")},ensure_ascii=False))
    else:
        result=assemble(plan=a.plan,game_root=a.game_root,output=a.output)
        print("TOURNAMENT_REAL_LOGS_ASSEMBLED",json.dumps(result))

if __name__=="__main__":
    main()
