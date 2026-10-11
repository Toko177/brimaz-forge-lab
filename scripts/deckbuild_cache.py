#!/usr/bin/env python3
"""Fail-closed reusable reference games for fast Commander A/B deckbuilding.

A saved reference can replace eight or more real Forge JVMs only when ALL
inputs affecting those games match exactly. The raw old game transcripts are
still re-certified by deckbuild_certify.py using current strict rules. No
partial or manifest-only results are promoted to valid wins.

Do NOT use reference games from a different Forge binary/patch/deck, pod,
seat, seed, profile, clock, or runner. No implied deterministic replay.
"""
import argparse
import hashlib
import json
from pathlib import Path

from deckbuild_run import OPPONENTS

VERSION = 1
FILES = (
    "scripts/patch_forge_charm_context.py",
    "scripts/patch_forge_brimaz_v13.py",
    "scripts/deckbuild_run.py",
    "scripts/forge_result_evidence.py",
)
FORGE_RELEASE = "2.0.15"
INSTALLER_SHA256 = "4468f182b60f6ca62d89697baa208981085af744f116781af751c611826db600"
POLICY = "V13-incubate-adaptive"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp(root, decks, manifest, *, seed_base, repeats, clock=360, profile="Default"):
    root=Path(root)
    decks=Path(decks)
    m=json.loads(Path(manifest).read_text(encoding="utf-8"))
    ref=m["decks"]["reference"]
    if ref["label"]!="Deck_Reference" or repeats not in (1,2,4,6):
        raise ValueError("Unsupported reference or benchmark depth")
    if clock!=360 or profile!="Default":
        raise ValueError("Current A/B workflow supports only the audited clock/profile")
    if not isinstance(seed_base,int) or seed_base<0:
        raise ValueError("Invalid predeclared RNG seed base")
    runtime={}
    for rel in FILES:
        f=root/rel
        if not f.is_file():
            raise FileNotFoundError(f)
        runtime[rel]=digest(f)
    if digest(decks/"Deck_Reference.dck")!=ref["forge_sha256"]:
        raise ValueError("Reference .dck does not match candidate manifest")
    opponents={}
    for pod, names in sorted(OPPONENTS.items()):
        for name in names:
            f=decks/(name+".dck")
            if not f.is_file():
                raise FileNotFoundError(f)
            opponents[name]=digest(f)
    fields={
        "version":VERSION,"forge_release":FORGE_RELEASE,
        "installer_sha256":INSTALLER_SHA256,"policy":POLICY,
        "reference_deck_sha256":ref["forge_sha256"],
        "reference_commander":ref["commander"],
        "reference_source_sha256":ref["source_sha256"],
        "opponent_sha256":dict(sorted(opponents.items())),
        "runtime_source_sha256":runtime,
        "seat_rotations":[0,1,2,3],
        "pods":sorted(OPPONENTS),
        "seeds":{pod:[seed_base+(100000 if pod=="artifact" else 0)
                       +10000*rotation+repeat
                       for rotation in range(4) for repeat in range(repeats)]
                 for pod in sorted(OPPONENTS)},
        "seed_base":seed_base,"repeats":repeats,
        "clock_seconds":clock,"process_timeout_seconds":445,
        "ai_profile":profile,
    }
    canonical=json.dumps(fields,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    return {"fingerprint":hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "inputs":fields,
            "warning":"Reusable only with all matching inputs and original transcript hashes. Cached results are not deterministic or expert AI evidence."}


def require_match(expected, previous):
    if expected.get("fingerprint")!=previous.get("fingerprint") or expected.get("inputs")!=previous.get("inputs"):
        raise ValueError("REFERENCE_CACHE_INCOMPATIBLE: deck, engine, opponents, seeds, profile or clock changed")
    return expected["fingerprint"]


def validate_reference_logs(root, expected, *, expected_games=None):
    root=Path(root)
    inp=expected["inputs"]
    n=expected_games or 2*4*inp["repeats"]
    games=[]
    for manifest in sorted(root.rglob("games.json")):
        entries=json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(entries,list):
            raise ValueError("Malformed cached Forge games manifest")
        for g in entries:
            if g.get("arm")!="reference" or g.get("candidate_deck")!="Deck_Reference":
                raise ValueError("Cached archive contains a foreign candidate arm")
            pod=g.get("pod");rotation=g.get("rotation");rep=g.get("repeat")
            if pod not in OPPONENTS or type(rotation) is not int or rotation not in range(4) or type(rep) is not int or rep not in range(inp["repeats"]):
                raise ValueError("Unknown cached pod/seat/repeat")
            deck_order=["Deck_Reference"]+OPPONENTS[pod]
            deck_order=deck_order[rotation:]+deck_order[:rotation]
            seed=inp["seed_base"]+(100000 if pod=="artifact" else 0)+10000*rotation+rep
            if (g.get("seats")!=deck_order or g.get("candidate_seat")!=deck_order.index("Deck_Reference")+1
                or g.get("seed")!=seed or g.get("clock_seconds")!=inp["clock_seconds"]
                or g.get("policy")!=inp["policy"]
                or g.get("profiles")!=[inp["ai_profile"]]*4
                or g.get("candidate_deck_sha256")!=inp["reference_deck_sha256"]):
                raise ValueError("Cached game manifest does not match immutable reference configuration")
            logfile=manifest.parent/Path(g["log"]).name
            if not logfile.is_file():
                raise FileNotFoundError(logfile)
            if digest(logfile)!=g.get("log_sha256"):
                raise ValueError("Raw reference Forge transcript was tampered with")
            games.append(g)
    keys=[(g["pod"],g["rotation"],g["repeat"]) for g in games]
    if len(keys)!=n or len(set(keys))!=n:
        raise ValueError(f"Expected exactly {n} uniquely paired saved reference games, found {len(keys)} / {len(set(keys))}")
    expected_keys={(pod,rot,rep) for pod in OPPONENTS for rot in range(4) for rep in range(inp["repeats"])}
    if set(keys)!=expected_keys:
        raise ValueError("Some pod/rotation/repeat cached reference games are absent")
    return {"reference_games":n,
            "statuses":{status:sum(g["status"]==status for g in games)
                        for status in sorted({g["status"] for g in games})},
            "note":"All archived original matches still need independent Scryfall and raw four-player outcome re-certification."}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["create","verify","audit-archive"],required=True)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--decks",type=Path,default=Path("forge_decks"))
    p.add_argument("--manifest",type=Path,default=Path("forge_decks/candidate-manifest.json"))
    p.add_argument("--seed-base",type=int,default=21410000)
    p.add_argument("--repeats",type=int,default=1)
    p.add_argument("--output",type=Path,default=Path("forge_decks/reference-cache-key.json"))
    p.add_argument("--previous",type=Path)
    p.add_argument("--archive",type=Path)
    a=p.parse_args()
    current=stamp(a.root,a.decks,a.manifest,seed_base=a.seed_base,repeats=a.repeats)
    if a.mode=="create":
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(current,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print("REFERENCE_CACHE_CREATED",current["fingerprint"])
    else:
        if not a.previous:raise ValueError("--previous reference-cache-key.json required")
        require_match(current,json.loads(a.previous.read_text(encoding="utf-8")))
        print("REFERENCE_CACHE_IDENTICAL_INPUTS",current["fingerprint"])
        if a.mode=="audit-archive":
            if not a.archive:raise ValueError("--archive required to audit previous real matches")
            audit=validate_reference_logs(a.archive,current)
            print("REFERENCE_CACHE_RAW_TRANSCRIPTS_VERIFIED",json.dumps(audit))
if __name__=="__main__":
    main()
