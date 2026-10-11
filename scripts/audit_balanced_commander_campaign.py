#!/usr/bin/env python3
"""Independent result-centric audit of a balanced real Forge Commander campaign.

Uses certificates, *not* the more permissive manifest status, for winrates.
Preserves every failed/censored game, rotates Brimaz through all four seats,
and never treats warning-free or certified outcomes as proof of expert play.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from math import sqrt
from pathlib import Path

PODS = ("aristo", "artifact")
ROTATIONS = (0, 1, 2, 3)
EXPECTED_POLICY = "V12-incubate"


def wilson(wins, games, z=1.959963984540054):
    if games == 0:
        return None
    if not (0 <= wins <= games):
        raise ValueError("Wins outside denominator")
    p = wins / games
    den = 1 + z*z/games
    center = (p + z*z/(2*games))/den
    half = z*sqrt(p*(1-p)/games + z*z/(4*games*games))/den
    return [round(max(0, center-half), 4), round(min(1, center+half), 4)]


def game_key(row):
    return (row["pod"], row["seed"], row.get("brimaz_seat", row.get("seat")), row["policy"])


def summarize(manifests, certificate, *, games_per_rotation=4,
              expected_policy=EXPECTED_POLICY):
    """Reconcile the declared matrix with the independently certified outcomes.

    The summary can describe an incomplete campaign, but fails closed in CI
    whenever the requested 2 pods x 4 rotations x games_per_rotation is absent.
    """
    if games_per_rotation <= 0:
        raise ValueError("games_per_rotation must be positive")
    expected = len(PODS) * len(ROTATIONS) * games_per_rotation
    if len(manifests) != expected:
        raise ValueError(f"Missing/duplicate campaigns: expected {expected}, got {len(manifests)}")
    manifest_by_key = {}
    counts = Counter()
    seeds = set()
    for g in manifests:
        k = game_key(g)
        if k in manifest_by_key:
            raise ValueError(f"Duplicate pod/seed/seat/policy key {k}")
        if g["pod"] not in PODS or g["rotation"] not in ROTATIONS:
            raise ValueError(f"Unknown pod or rotation {k}")
        if g["policy"] != expected_policy:
            raise ValueError(f"Mixed AI variant in one campaign: {g['policy']}")
        if len(g["seats"]) != 4 or sorted(g["seats"]).count("Brimaz_V3") != 1:
            raise ValueError(f"Invalid four-seat deck declaration {k}")
        if g["brimaz_seat"] != g["seats"].index("Brimaz_V3")+1:
            raise ValueError(f"Brimaz player seat mismatch {k}")
        counts[g["pod"], g["rotation"]] += 1
        if g["seed"] in seeds:
            raise ValueError(f"Duplicated global seed {g['seed']} contaminates table rotations")
        seeds.add(g["seed"])
        manifest_by_key[k] = g
    if set(counts) != {(p, r) for p in PODS for r in ROTATIONS}:
        raise ValueError("Not all two-pod four-seat combinations represented")
    if any(n != games_per_rotation for n in counts.values()):
        raise ValueError("Unbalanced seed cohort per pod and seat")

    certificates = certificate["games"]
    if len(certificates) != len(manifests):
        raise ValueError("Independent certificate count mismatches raw games")
    cert_by_key = {}
    for g in certificates:
        k = game_key(g)
        if k in cert_by_key:
            raise ValueError(f"Duplicate certified game {k}")
        cert_by_key[k] = g
    if set(cert_by_key) != set(manifest_by_key):
        raise ValueError("Certification missing a match or contains unrelated games")
    certified = []
    full = []
    for k in sorted(manifest_by_key):
        g, c = manifest_by_key[k], cert_by_key[k]
        valid = c["engine_natural_and_consistent"]
        if c["status"] != g["status"] or c["winner_deck"] != g["winner_deck"] or c["brimaz_win"] != g["brimaz_win"]:
            raise ValueError(f"Raw game and certificate disagree on result {k}")
        if valid and (not c["legal_deck_gate"] or c["status"] != "complete"):
            raise ValueError(f"Certificate wrongly marked illegal/censored game as valid {k}")
        if valid and (g["brimaz_win"] is True) != (g["winner_deck"] == "Brimaz_V3"):
            raise ValueError(f"Contradictory Brimaz result {k}")
        q = c.get("ai_quality_signatures", {})
        warning_free = all(q.get(field, -1) == 0 for field in
                           ("evaluation_timeouts", "invalid_attack_fallbacks",
                            "incubate_handler_warnings", "decision_thread_timeout_samples"))
        if valid and warning_free != c.get("ai_warning_free"):
            raise ValueError(f"Certificate warning-free classification inconsistent {k}")
        row = {"pod":g["pod"],"seed":g["seed"],"rotation":g["rotation"],
               "seat":g["brimaz_seat"],"status":g["status"],
               "certified":valid,"won":g["brimaz_win"] if valid else None,
               "winner_deck":g["winner_deck"] if valid else None,
               "warning_free":warning_free if valid else None,
               "ai_timeouts":q.get("evaluation_timeouts",0),
               "attack_fallbacks":q.get("invalid_attack_fallbacks",0),
               "rejection_reasons":c["rejection_reasons"]}
        full.append(row)
        if valid:
            certified.append(row)
    def tally(rows):
        return {"scheduled":len(rows),
                "certified":sum(r["certified"] for r in rows),
                "wins":sum(r["won"] is True for r in rows),
                "censored_or_rejected":sum(not r["certified"] for r in rows),
                "warning_free":sum(r["warning_free"] is True for r in rows),
                "warning_free_wins":sum(r["warning_free"] is True and r["won"] is True for r in rows),
                "ai_timeouts":sum(r["ai_timeouts"] for r in rows),
                "attack_fallbacks":sum(r["attack_fallbacks"] for r in rows),
                "wilson_95":wilson(sum(r["won"] is True for r in rows),
                                   sum(r["certified"] for r in rows))}
    by_pod = {p:tally([g for g in full if g["pod"]==p]) for p in PODS}
    by_seat = {str(seat):tally([g for g in full if g["seat"]==seat])
               for seat in range(1,5)}
    summary=tally(full)
    summary.update({"expected_games":expected,
                    "groups_pod_rotation":len(counts),
                    "winner_distribution":dict(Counter(x["winner_deck"] for x in certified)),
                    "statuses":dict(Counter(x["status"] for x in full)),
                    "rejections":dict(Counter(reason for x in full for reason in x["rejection_reasons"])),
                    "policy":expected_policy,
                    "fundamental_limitation":"Forge same seed may diverge across JVM runs. Certified outcome is not proof of expert AI. Sparse/censored game outcomes may bias conditional winrate.",
                    "statistical_limitation":"Wilson 95% interval describes sampling uncertainty conditional on these opponents/seats and certified matches; no 20% threshold is assumed."})
    return {"summary":summary,"by_pod":by_pod,"by_brimaz_seat":by_seat,"games":full}


def from_files(root, cert_path, expected_per_rotation, policy):
    manifest = []
    transcript_sha = {}
    for path in sorted(root.rglob("games.json")):
        for g in json.loads(path.read_text(encoding="utf-8")):
            # Always verify original transcript bytes match certification SHA.
            transcript = path.parent/Path(g["log"]).name
            if not transcript.is_file():
                raise FileNotFoundError(transcript)
            k = game_key(g)
            if k in transcript_sha:
                raise ValueError(f"Duplicate transcript key {k}")
            raw = transcript.read_text(encoding="utf-8", errors="replace")
            transcript_sha[k] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            manifest.append(g)
    if not manifest:
        raise ValueError("No real Forge games found")
    c = json.loads(cert_path.read_text(encoding="utf-8"))
    for record in c["games"]:
        key = game_key(record)
        if key not in transcript_sha or transcript_sha[key] != record["transcript_sha256"]:
            raise ValueError(f"Certificate transcript SHA256 does not match original log: {key}")
    return summarize(manifest,c,games_per_rotation=expected_per_rotation,expected_policy=policy)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--certificate",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--per-pod-rotation",type=int,default=4)
    p.add_argument("--policy",default=EXPECTED_POLICY)
    a=p.parse_args()
    report=from_files(a.input,a.certificate,a.per_pod_rotation,a.policy)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("REAL_EDH_BALANCED_CAMPAIGN",json.dumps(report["summary"],ensure_ascii=False),flush=True)
    print("REAL_EDH_PODS",json.dumps(report["by_pod"],ensure_ascii=False),flush=True)
    print("REAL_EDH_SEATS",json.dumps(report["by_brimaz_seat"],ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
