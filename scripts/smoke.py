#!/usr/bin/env python3
"""Create a Forge .dck from a commander decklist; four-seat smoke test."""
import argparse, pathlib, re, subprocess, json, os, sys, time
p=argparse.ArgumentParser()
p.add_argument('--deck', default='decks/Brimaz_V3.txt')
p.add_argument('--jar', required=True)
p.add_argument('--games',type=int,default=1)
args=p.parse_args()
lines=pathlib.Path(args.deck).read_text().splitlines()
cards=[]
for x in lines:
    if not x.strip(): continue
    m=re.fullmatch(r'(\d+)\s+(.+)',x.strip())
    if not m: raise ValueError(x)
    cards.append((int(m[1]),m[2]))
assert sum(q for q,_ in cards)==100, 'Commander list must have 100 cards'
assert sum(q for q,n in cards if n=='Brimaz, Blight of Oreskos')==1
out=pathlib.Path('forge_decks');out.mkdir(exist_ok=True)
dck=out/'Brimaz_V3.dck'
dck.write_text('[metadata]\nName=Brimaz V3\n[Main]\n'+''.join(f'{q} {n}\n' for q,n in cards if n!='Brimaz, Blight of Oreskos')+'[Commander]\n1 Brimaz, Blight of Oreskos\n')
cmd=['java','-Xmx4g','-jar',str(pathlib.Path(args.jar).resolve()),'sim','-d','Brimaz_V3','Brimaz_V3','Brimaz_V3','Brimaz_V3','-f','commander','-n',str(args.games)]
pathlib.Path('results').mkdir(exist_ok=True)
print('Command:',cmd,flush=True)
print('Deck:',dck,flush=True)
env=dict(os.environ)
t=time.time()
try:
    res=subprocess.run(cmd,cwd=str(pathlib.Path(args.jar).resolve().parent),capture_output=True,text=True,timeout=480,env=env)
    raw=res.stdout+'\n[STDERR]\n'+res.stderr
    pathlib.Path('results/forge-smoke.log').write_text(raw)
    result={'returncode':res.returncode,'seconds':round(time.time()-t,1),'command':cmd,'output_tail':raw[-16000:]}
except subprocess.TimeoutExpired as exc:
    raw=str(exc.stdout)+'\n'+str(exc.stderr)
    pathlib.Path('results/forge-smoke.log').write_text(raw)
    result={'status':'timeout','seconds':round(time.time()-t,1),'output_tail':raw[-16000:]}
pathlib.Path('results/smoke.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2),flush=True)
if result.get('returncode')!=0: sys.exit(1)
