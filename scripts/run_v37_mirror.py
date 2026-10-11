#!/usr/bin/env python3
"""True real-JVM same-game EDH mirror. No simulated winners or changed card lists."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,math,os
from pathlib import Path
import re,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_local_four_ai import validate_decks,patch_jar,policy_flags,prepare_forge_shared_profile_paths,sha,CANONICAL_DECK_SHA256
from forge_seat_identity import resolve_ai_player
PODS={"aristo":("Kaal_9594008","Kaal_10347090"),
      "artifact":("Kaal_23328062","Kaal_11485202")}
MIRRORS=("Brimaz_Challenger","Brimaz_Reference")
FOUR_MIRRORS=("Brimaz_Challenger_A","Brimaz_Challenger_B",
              "Brimaz_Reference_A","Brimaz_Reference_B")

def category(name):
    if name is None:return "invalid"
    if name.startswith("Brimaz_Challenger"):return "challenger"
    if name.startswith("Brimaz_Reference"):return "reference"
    return "opponent"

def make_four_mirror_decks(canonical,target):
    """All FOUR participants have byte-identical Magic cards, different metadata."""
    target.mkdir(parents=True,exist_ok=False)
    original=(canonical/"Brimaz_V3.dck").read_bytes()
    header=b"Name=Brimaz V3\n"
    if original.count(header)!=1:raise ValueError("Canonical original metadata changed")
    for name in FOUR_MIRRORS:
        disp=name.replace("_"," ")
        renamed=original.replace(header,("Name="+disp+"\n").encode(),1)
        if renamed.replace(("Name="+disp+"\n").encode(),header,1)!=original:
            raise AssertionError("All-Brimaz source cardlist differs")
        (target/(name+".dck")).write_bytes(renamed)
    return FOUR_MIRRORS

WIN=re.compile(r"Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*Ai\((\d+)\)-(.+?) has won!")
ERRORS=("java.lang.NullPointerException","Exception in thread","java.lang.IllegalStateException",
        "StackOverflowError","OutOfMemoryError","Simulation: Couldn't play land")
V41_WINDOW=re.compile(
    r"^FOUR_AI_V41_SAC_WINDOW player=(.*?) turn=\d+ pilotAuthorized=(true|false)\b",
    re.M)

def verify_v41_pilot_identity(raw,seats):
    """Verify V41 controller actually reaches the named seats in REAL logs.

    Forge telemetry uses underscore deck IDs; winner banners may use the
    deck's Name= label instead. Match exact seats only, never substrings.
    """
    bad=[]
    challenger_windows=0
    windows=V41_WINDOW.findall(raw)
    for name,flag in windows:
        try:
            key=resolve_ai_player(name,seats,ROOT/"forge_decks",mirror=True)
        except ValueError:
            bad.append({"player":name,"reason":"seat_name_mismatch"})
            continue
        challenger=category(key)=="challenger"
        if challenger:challenger_windows+=1
        if challenger!=(flag=="true"):
            bad.append({"player":name,"reason":"incorrect_pilot_authorization"})
    return {"windows":len(windows),"challenger_windows":challenger_windows,
            "bad_windows":bad}

def make_mirror_decks(canonical,target,pod):
    target.mkdir(parents=True,exist_ok=False)
    raw=(canonical/"Brimaz_V3.dck").read_text(encoding="utf-8")
    if raw.count("Name=Brimaz V3\n")!=1:raise ValueError("Canonical source mismatch")
    for name,display in zip(MIRRORS,("Brimaz Challenger","Brimaz Reference")):
        clone=raw.replace("Name=Brimaz V3\n","Name="+display+"\n",1)
        if clone.replace("Name="+display+"\n","Name=Brimaz V3\n",1)!=raw:
            raise AssertionError("Mirror cards changed")
        (target/(name+".dck")).write_text(clone,encoding="utf-8")
    for name in PODS[pod]:
        dst=target/(name+".dck")
        dst.write_bytes((canonical/(name+".dck")).read_bytes())
        if sha(dst)!=sha(canonical/(name+".dck")):raise AssertionError("Opponent changed")
    return (*MIRRORS,*PODS[pod])

def expected_display_name(deck_id):
    if deck_id.startswith("Brimaz_Challenger") or deck_id.startswith("Brimaz_Reference"):
        return deck_id.replace("_"," ")
    return None  # Original Kaal decks may have unrelated display titles.

def classify(raw,stderr,returncode,timed_out,clock,seats):
    wins=WIN.findall(raw)
    alltext=raw+"\n"+stderr
    multiple=sum("has won because all opponents have lost" in x for x in
                 re.findall(r"^Game Outcome: (.+)$",raw,re.M))>1
    if any(x in alltext for x in ERRORS):status="engine_fault"
    elif timed_out:status="process_timeout"
    elif returncode!=0:status="engine_failed"
    elif multiple or "Stopping slow match as draw" in raw or \
         any(int(x[0])>=clock*1000-2500 for x in wins):status="clock_censored"
    elif len(wins)!=1:status="unparsed"
    else:status="complete"
    winner=None
    if status=="complete":
        seat=int(wins[0][1])
        if not 1<=seat<=4:raise ValueError("Not a four-player result")
        winner=seats[seat-1]
        expected=expected_display_name(winner)
        if expected is not None and wins[0][2].strip()!=expected:
            # Never attribute a win to a supposed controller when Forge
            # does not confirm the same seat's actual player display name.
            status="name_mismatch"
            winner=None
    return status,winner

def binomial_two_sided(a,b):
    n=a+b
    if not n:return 1.
    return min(1.,2*sum(math.comb(n,k) for k in range(min(a,b)+1))/(2**n))

def summarize(records):
    finished=[x for x in records if x["status"]=="complete"]
    wins=Counter(category(x["winner"]) for x in finished)
    a,b=wins["challenger"],wins["reference"]
    return {
        "kind":"ACTUAL Forge same-JVM direct same-cardlist Brimaz mirror",
        "real_jvm_games":len(records),"natural_finishes":len(finished),
        "censored_or_faulted":len(records)-len(finished),
        "challenger_brimaz_wins":a,"reference_brimaz_wins":b,
        "opponent_wins":len(finished)-a-b,
        "all_brimaz_same_deck_games":sum(
            x.get("mode")=="all-brimaz" for x in records),
        "all_brimaz_natural_games":sum(
            x["status"]=="complete" and x.get("mode")=="all-brimaz"
            for x in records),
        "same_deck_2vs2_required_winner_integrity":all(
            x["status"]!="complete" or x.get("mode")!="all-brimaz"
            or category(x["winner"]) in ("challenger","reference")
            for x in records),
        "direct_duel_decisive_wins":a+b,
        "two_sided_conditional_binomial_p":round(binomial_two_sided(a,b),6),
        "statistically_proven_general_AI_superiority":False,
        "predeclared_strong_evidence_on_mirror":bool(
            a+b>=16 and binomial_two_sided(a,b)<0.01 and a>b),
        "note":"A mirror-only difference needs confirmation across dissimilar pods and independent seeds.",
        "limits":["The same Brimaz 99+commander cards are used by both players.",
          "Both receive identical technical engine patches, NOT byte-identical original Forge.",
          "Other Kaal wins are neither a win nor a loss for this same-deck comparison.",
          "A small real-game sample cannot establish broader Commander skill."],
        "games":records,
    }

def game(task,jar,run_dir,deck_dirs,out,seed_base,clock,mode):
    pod,rotation,repeat=task
    seats=FOUR_MIRRORS if mode=="all-brimaz" else (*MIRRORS,*PODS[pod])
    seats=seats[rotation:]+seats[:rotation]
    seed=seed_base+10000*rotation+repeat+(0 if pod=="aristo" else 100000)
    target=out/pod/f"rotation{rotation}_rep{repeat}"
    target.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    for name in ("_JAVA_OPTIONS","JDK_JAVA_OPTIONS","JAVA_TOOL_OPTIONS"):env.pop(name,None)
    env["JAVA_TOOL_OPTIONS"]=policy_flags("v41_brimaz_challenger")+" -Dbrimaz.v37MirrorDuel=true"
    command=["java","-Xmx4g","-jar",str(jar),"sim","-d",
             *[name+".dck" for name in seats],"-D",str(deck_dirs[pod]),
             "-f","Commander","-n","1","-c",str(clock),"-s",str(seed),
             "-a","Default","Default","Default","Default"]
    timed_out=False
    try:
        proc=subprocess.run(command,cwd=run_dir,capture_output=True,text=True,
                            errors="replace",env=env,timeout=clock+85)
        stdout,stderr,rc=proc.stdout,proc.stderr,proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out=True
        stdout=(exc.stdout or b"").decode("utf-8",errors="replace") if isinstance(exc.stdout,bytes) else (exc.stdout or "")
        stderr=(exc.stderr or b"").decode("utf-8",errors="replace") if isinstance(exc.stderr,bytes) else (exc.stderr or "")
        rc=None
    (target/"game.log").write_text(stdout+"\n[STDERR]\n"+stderr,encoding="utf-8")
    status,winner=classify(stdout,stderr,rc,timed_out,clock,seats)
    identity=verify_v41_pilot_identity(stdout,seats)
    if identity["bad_windows"]:
        # A winner does not validate a match where its policy was disabled.
        status,winner="policy_fault",None
    record={"pod":pod,"rotation":rotation,"repeat":repeat,"seed":seed,
            "mode":mode,
            "seats":seats,"status":status,"winner":winner,"exit":rc,
            "V37_strategic_approvals":stdout.count("FOUR_AI_V35_STOCK_APPROVED"),
            "V37_positive_sacrifice_approvals":stdout.count("FOUR_AI_V37_POSITIVE_SAC_FORGE_APPROVED"),
            "V38_transformation_approvals":stdout.count("FOUR_AI_V38_TRANSFORM_STOCK_APPROVED"),
            "V38_transformation_proposals":stdout.count("FOUR_AI_V38_TRANSFORM_PROPOSAL"),
            "V39_visible_counter_engine_proposals":len(re.findall(
                r"FOUR_AI_V38_TRANSFORM_PROPOSAL[^\n]*source=KNOWN_COUNTER_ENGINE",
                stdout)),
            "V40_per_seat_approved":stdout.count(
                "FOUR_AI_V40_TRANSFORM_APPROVED_BY_SEAT"),
            "V40_sac_diagnostic_windows":stdout.count("BRIMAZ_WINDOW: V7"),
            "V41_sac_diagnostic_windows":stdout.count("FOUR_AI_V41_SAC_WINDOW"),
            "V41_pilot_identity":identity,
            "log":str((target/"game.log").relative_to(out))}
    (target/"result.json").write_text(json.dumps(record,indent=2)+"\n")
    print("V37_ACTUAL_MIRROR_MATCH",json.dumps(record,ensure_ascii=False),flush=True)
    return record

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--jar",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--repeats",type=int,default=2)
    ap.add_argument("--parallel",type=int,default=2)
    ap.add_argument("--clock",type=int,default=420)
    ap.add_argument("--seed-base",type=int,default=20270503)
    ap.add_argument("--mode",choices=("kaal-mirror","all-brimaz"),
                    default="kaal-mirror")
    ap.add_argument("--pod",choices=("both","aristo","artifact"),
                    default="both")
    a=ap.parse_args()
    if not 1<=a.repeats<=5 or not 1<=a.parallel<=2:ap.error("repeat 1..5 parallel 1..2")
    pinned=validate_decks(ROOT/"forge_decks",ROOT/"canonical/results/forge_normalization/report.json")
    if pinned!=CANONICAL_DECK_SHA256:raise AssertionError("Canonical source mutated")
    dest=a.out.resolve()
    dest.mkdir(parents=True,exist_ok=True)
    prepare_forge_shared_profile_paths(Path.home())
    with tempfile.TemporaryDirectory(prefix="forge_v37_mirror_") as folder:
        scratch=Path(folder)
        prepared=scratch/"v37-patched.jar"
        digest,patches=patch_jar(a.jar.resolve(),prepared,"v37_brimaz_challenger")
        selected=PODS if a.pod=="both" else {a.pod:PODS[a.pod]}
        dirs={pod:scratch/("mirror_"+pod) for pod in selected}
        for pod in selected:
            if a.mode=="all-brimaz":
                make_four_mirror_decks(ROOT/"forge_decks",dirs[pod])
            else:
                make_mirror_decks(ROOT/"forge_decks",dirs[pod],pod)
        provenance={"original_forge_sha256":sha(a.jar.resolve()),"patched_sha256":digest,
            "identical_patches_for_every_player":patches,
            "canonical_seven_source_hashes":pinned,
            "two_brimaz_card_lists_identical_except_metadata":True,
            "seed_base":a.seed_base,"clock_seconds":a.clock,
            "mode":a.mode,"pod":a.pod,
            "all_four_same_deck":a.mode=="all-brimaz"}
        (dest/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
        tasks=[(pod,r,k) for pod in selected for r in range(4)
               for k in range(a.repeats)]
        records=[]
        with ThreadPoolExecutor(max_workers=a.parallel) as pool:
            futures=[pool.submit(game,t,prepared,a.jar.resolve().parent,dirs,
                                 dest,a.seed_base,a.clock,a.mode) for t in tasks]
            for future in as_completed(futures):
                records.append(future.result())
                (dest/"progress.json").write_text(
                    json.dumps(summarize(records),indent=2,ensure_ascii=False)+"\n")
        records.sort(key=lambda x:(x["pod"],x["rotation"],x["repeat"]))
        result=summarize(records)
        if a.mode=="all-brimaz" and not result["same_deck_2vs2_required_winner_integrity"]:
            raise AssertionError("A natural all-Brimaz game had a non-Brimaz winner")
        (dest/"summary.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
        if any(x["status"]=="policy_fault" for x in records):
            raise AssertionError("V41 mirror identity mismatch: comparison invalid; inspect raw logs")
        if not any(x["V41_pilot_identity"]["challenger_windows"] for x in records):
            raise AssertionError("V41 ran without an observable challenger turn: result unverified")
        print("V37_TRUE_MIRROR_SUMMARY",json.dumps({k:v for k,v in result.items()
           if k in ("real_jvm_games","natural_finishes","censored_or_faulted",
                    "challenger_brimaz_wins","reference_brimaz_wins",
                    "opponent_wins","two_sided_conditional_binomial_p")}),flush=True)
if __name__=="__main__":main()
