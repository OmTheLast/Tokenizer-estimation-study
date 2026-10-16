"""Fetch public official UD candidates at immutable commits; never print text."""
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/2026-10-16-cjk-preflight/acquisition'
LOCK=OUT/'sources.json'

def save(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    plan=json.loads((ROOT/'config/cjk-experiment-v1.json').read_text())
    state=json.loads(LOCK.read_text()) if LOCK.exists() else {'plan_sha256':sha(ROOT/'config/cjk-experiment-v1.json'),'sources':{}}
    assert state['plan_sha256']==sha(ROOT/'config/cjk-experiment-v1.json')
    for source in plan['sources']:
        code=source['code']; repo=source['repository']
        if code not in state['sources']:
            line=subprocess.check_output(['git','ls-remote',repo+'.git','HEAD'],text=True).strip()
            commit=line.split()[0];assert len(commit)==40
            state['sources'][code]={'repository':repo,'revision':commit,'pinned_utc':datetime.now(timezone.utc).isoformat(),'role':source['role'],'files':{}}
            save(LOCK,state)
        entry=state['sources'][code];cache=ROOT/'.cache/cjk_ud'/code/entry['revision'];cache.mkdir(parents=True,exist_ok=True)
        splits=['train','dev','test'] if source['role']=='primary_development_and_test' else ['test']
        names=['README.md','LICENSE.txt']+[code+'-ud-'+split+'.conllu' for split in splits]
        for name in names:
            p=cache/name
            if name in entry['files'] and p.exists():assert sha(p)==entry['files'][name]['sha256'];continue
            url=repo.replace('https://github.com/','https://raw.githubusercontent.com/')+'/'+entry['revision']+'/'+name
            temp=p.with_suffix(p.suffix+'.download')
            subprocess.run(['curl','--fail','--silent','--show-error','--location','--retry','2','--max-time','90',url,'-o',str(temp)],check=True)
            temp.replace(p)
            entry['files'][name]={'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'cache_path':str(p.relative_to(ROOT))}
            save(LOCK,state)
        print(f"Pinned {code} at {entry['revision'][:12]}: {len(entry['files'])} files; text stays in ignored cache",flush=True)
    print('All requested candidate files fetched; no tokenizer counts or fitting.',flush=True)

if __name__=='__main__':main()
