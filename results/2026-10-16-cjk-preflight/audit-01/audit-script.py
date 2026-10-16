"""Offline preflight: schema, provenance, duplicate screening; no tokenization."""
from collections import Counter, defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/2026-10-16-cjk-preflight/audit-01'
LOCK=ROOT/'results/2026-10-16-cjk-preflight/acquisition/sources.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s).split())
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def save(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def parse_conllu(path):
    records=[];meta={};newdoc=None
    for line in path.read_text().splitlines()+['']:
        if line.startswith('# '):
            key,sep,value=line[2:].partition(' = ')
            if sep:
                if key in meta:raise ValueError('Duplicate metadata key')
                meta[key]=value
                if key=='newdoc id':newdoc=value
        elif not line.strip() and meta:
            records.append({'id':meta.get('sent_id'),'text':meta.get('text'),'doc':newdoc,'parallel':meta.get('parallel_id'),'keys':sorted(meta)})
            meta={}
    return records
class Union:
    def __init__(self,n):self.parent=list(range(n))
    def find(self,x):
        while self.parent[x]!=x:self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
        return x
    def join(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b:self.parent[max(a,b)]=min(a,b)
def grams(s):return set(s[i:i+5] for i in range(len(s)-4))
def near(a,b):
    if a==b:return True
    if min(len(a),len(b))<20:return False
    x,y=grams(a),grams(b);return 19*len(x&y)>=9*(len(x)+len(y))
def source_group(row):
    if row['code']=='yue_hk':
        match=re.fullmatch(r'(\d+)',row['id'])
        if match:
            n=int(match[1])
            for lo,hi,label in [(1,410,'film1'),(411,547,'film2'),(548,650,'film3'),(651,1004,'legislative')]:
                if lo<=n<=hi:return 'yue_hk:'+label
    # Other sources have no verified original-document mapping. Never
    # equate one sentence or a duplicate component with one source document.
    return None

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    lock=json.loads(LOCK.read_text());plan=json.loads((ROOT/'config/cjk-experiment-v1.json').read_text())
    rows=[];inventory=[];licences=[]
    for code,entry in lock['sources'].items():
        for f in entry['files'].values():assert sha(ROOT/f['cache_path'])==f['sha256']
        readme=(ROOT/entry['files']['README.md']['cache_path']).read_text()
        license_text=(ROOT/entry['files']['LICENSE.txt']['cache_path']).read_text()
        caveat=('underlying content' in readme or 'underlying text' in readme)
        licences.append({'code':code,'metadata_license':'CC BY-SA 4.0' if 'License: CC BY-SA 4.0' in readme else 'review_required','license_file_mentions_by_sa_4':bool(re.search(r'(Attribution.ShareAlike 4\.0|by-sa/4.0)',license_text,re.I)),'underlying_text_caveat_in_readme':caveat,'raw_text_training_permission_status':'unresolved_due_to_source_text_caveat' if caveat else 'not_independently_cleared; repository terms recorded','readme_url':entry['files']['README.md']['url'],'license_url':entry['files']['LICENSE.txt']['url'],'attribution_metadata':[line for line in readme.splitlines() if line.startswith('Contributors:')]})
        for name,f in entry['files'].items():
            if not name.endswith('.conllu'):continue
            split=name.rsplit('-ud-',1)[1].removesuffix('.conllu');records=parse_conllu(ROOT/f['cache_path'])
            assert len({r['id'] for r in records})==len(records) and all(r['id'] for r in records)
            missing=sum(not isinstance(r['text'],str) or not r['text'].strip() for r in records)
            metadata=Counter(k for r in records for k in r['keys'])
            usable=[r for r in records if isinstance(r['text'],str) and r['text'].strip()]
            inv={'code':code,'split':split,'records':len(records),'missing_or_empty_text':missing,'metadata_key_counts':dict(metadata),'newdoc_equal_sentence_id':sum(r['doc']==r['id'] for r in usable),'verified_source_groups':0}
            start=len(rows)
            for r in usable:
                normalized=norm(r['text']);counts=[sum(0x3400<=ord(c)<=0x4DBF or 0x4E00<=ord(c)<=0x9FFF for c in r['text']),sum(0x3040<=ord(c)<=0x30FF for c in r['text']),sum(0xAC00<=ord(c)<=0xD7AF for c in r['text'])]
                row={'code':code,'split':split,'id':r['id'],'parallel':r['parallel'],'text_sha256':digest(r['text']),'normalized_sha256':digest(normalized),'characters':len(r['text']),'features':counts,'normalized':normalized,'upstream_doc_id':r['doc']}
                row['verified_source_group']=source_group(row);rows.append(row)
            inv['verified_source_groups']=len({r['verified_source_group'] for r in rows[start:] if r['verified_source_group']})
            inventory.append(inv)
    print(f'Parsed {len(rows)} candidate sentences without displaying text.',flush=True)
    ext=[]
    for p in sorted((ROOT/'.cache/flores_plus').rglob('dev/*.jsonl')):
        for line in p.read_text().splitlines():
            if line.strip():ext.append(norm(json.loads(line)['text']))
    fixture=ROOT/'results/2026-10-07-all-profiles/run-01/estimator-cases.json'
    ext.extend(norm(r['text']) for r in json.loads(fixture.read_text())['fixtures'])
    external=set(ext); u=Union(len(rows));edges=[];bad=set();exact={};parallel={};sourcegroups={}
    for i,r in enumerate(rows):
        s=r['normalized']
        if s in external:bad.add(i)
        if s in exact:u.join(i,exact[s]);edges.append({'a':exact[s],'b':i,'kind':'normalized_exact'})
        else:exact[s]=i
        if r['parallel']:
            if r['parallel'] in parallel:u.join(i,parallel[r['parallel']]);edges.append({'a':parallel[r['parallel']],'b':i,'kind':'parallel_family'})
            else:parallel[r['parallel']]=i
        if r['verified_source_group']:
            g=r['verified_source_group']
            if g in sourcegroups:u.join(i,sourcegroups[g])
            else:sourcegroups[g]=i
    # Deduplicated text nodes; scan candidate against all external and previous
    # candidate nodes. Sharing a gram is necessary for Jaccard >= .9.
    unique=list(dict.fromkeys(ext+[r['normalized'] for r in rows]));idx={s:i for i,s in enumerate(unique)}
    n_ext=len(set(ext));gsets=[];posts=defaultdict(list);near_edges=0;comparisons=0
    text_rows=defaultdict(list)
    for i,r in enumerate(rows):text_rows[r['normalized']].append(i)
    for i,s in enumerate(unique):
        gs=grams(s) if len(s)>=20 else set();gsets.append(gs)
        if s in text_rows and gs:
            candidates=set()
            for g in gs:
                for j in posts[g]:
                    if 10*min(len(gs),len(gsets[j]))>=9*max(len(gs),len(gsets[j])):candidates.add(j)
            for j in candidates:
                comparisons+=1
                if 19*len(gs&gsets[j])>=9*(len(gs)+len(gsets[j])):
                    near_edges+=1;a=text_rows[s][0];other=unique[j]
                    if j<n_ext:bad.add(a)
                    if other in text_rows:
                        b=text_rows[other][0];u.join(a,b);edges.append({'a':a,'b':b,'kind':'near_duplicate'})
        for g in gs:posts[g].append(i)
        if i and i%10000==0:print(f'Duplicate check: {i} normalized text records indexed; no prediction scores computed.',flush=True)
    # If a candidate identical to an external text preceded another candidate,
    # shared exact/near edges propagate exclusion to the entire known family.
    groups=defaultdict(list)
    for i in range(len(rows)):groups[u.find(i)].append(i)
    bad_roots={u.find(i) for i in bad};priority={'train':0,'dev':1,'test':2}
    dispositions={};within_seen=set()
    for root,indices in groups.items():
        best=max(priority[rows[i]['split']] for i in indices)
        for i in sorted(indices,key=lambda i:(rows[i]['code'],rows[i]['split'],rows[i]['id'])):
            r=rows[i];key=(r['code'],r['split'],r['normalized_sha256'])
            if root in bad_roots:reason='prior_evaluation_overlap_family'
            elif priority[r['split']]<best:reason='cross_split_family'
            elif key in within_seen:reason='within_split_exact_duplicate'
            else:reason='passes_available_checks_not_final';within_seen.add(key)
            dispositions[i]=reason
    for inv in inventory:
        inds=[i for i,r in enumerate(rows) if r['code']==inv['code'] and r['split']==inv['split']]
        inv['dispositions']=dict(Counter(dispositions[i] for i in inds))
        inv['passes_available_checks']=sum(dispositions[i]=='passes_available_checks_not_final' for i in inds)
        inv['distinct_duplicate_or_parallel_components']=len({u.find(i) for i in inds})
    primary=[r for i,r in enumerate(rows) if r['code'] in ['zh_gsd','ja_gsd','ko_gsd'] and r['split']=='train' and dispositions[i]=='passes_available_checks_not_final']
    matrix=np.array([r['features'] for r in primary],dtype=float)
    feature_check={'primary_train_rows_after_available_checks':len(primary),'sentences_with_feature':dict(zip(['han','kana','hangul'],map(int,(matrix>0).sum(axis=0)))),'rank':int(np.linalg.matrix_rank(matrix))}
    zh={r['parallel'] for r in rows if r['code']=='zh_gsd' and r['split']=='test'};simp={r['parallel'] for r in rows if r['code']=='zh_gsdsimp'}
    result={'status':'not_ready_for_fitting','created_utc':datetime.now(timezone.utc).isoformat(),'sources_lock_sha256':sha(LOCK),'plan_sha256':sha(ROOT/'config/cjk-experiment-v1.json'),'script_sha256':sha(Path(__file__)),'inventory':inventory,'licenses':licences,'script_feature_check':feature_check,'simplified_traditional_test_alignment':{'zh_parallel_ids':len(zh),'simp_parallel_ids':len(simp),'same_nonempty_ids':zh==simp and None not in zh},'duplicate_screen':{'normalized_external_records':n_ext,'candidate_rows':len(rows),'candidate_exact_edges':sum(e['kind']=='normalized_exact' for e in edges),'candidate_near_edges':sum(e['kind']=='near_duplicate' for e in edges),'near_text_pairs_including_external':near_edges,'pair_comparisons':comparisons,'candidate_rows_in_external_overlap_families':sum(dispositions[i]=='prior_evaluation_overlap_family' for i in range(len(rows))),'cross_split_excluded_rows':sum(dispositions[i]=='cross_split_family' for i in range(len(rows)))},'blockers':['Original document IDs are absent for Chinese and Korean; Japanese newdoc IDs equal sentence IDs and are not verified source-document identities. The planned document-group isolation and minimum groups cannot be established.','GSD source documentation distinguishes annotation licensing from underlying-text rights; the design source-text licensing requirement is not cleared.'],'not_executed':['tokenizer encoding','fitting','test prediction/error scoring','FLORES devtest access'],'manifest_status':'Provisional audit manifest only; not an approved or frozen training/test manifest'}
    manifest=[]
    for i,r in enumerate(rows):manifest.append({k:v for k,v in r.items() if k not in ['normalized']}|{'audit_row':i,'known_group':u.find(i),'disposition':dispositions[i]})
    save(OUT/'audit.json',result);save(OUT/'provisional-manifest.json',manifest);save(OUT/'duplicate-edges.json',edges)
    lines=['# CJK practice/exam data check','','**Not ready for fitting.** This is an input audit, not an experiment result. No token counts, predictions, fitting or test errors were computed.','','## What passed','','All requested files were pinned and their checksums verified. Sentence text was extracted directly, without joining annotated words. Exact and near-duplicate checks used the prespecified normalization and 5-gram rule. Simplified/traditional test families were checked by shared parallel IDs.','','| Candidate | Upstream set | Sentences | Pass available checks* | Verified original-source groups |','| --- | --- | ---: | ---: | ---: |']
    for inv in inventory:lines.append(f"| {inv['code']} | {inv['split']} | {inv['records']} | {inv['passes_available_checks']} | {inv['verified_source_groups']} |")
    lines+=['','*Passing available checks does not make a row approved for fitting. The document and text-rights gaps below still apply. Duplicate components are not substitutes for original documents.','','## What prevents approval','']+[f'- {b}' for b in result['blockers']]
    lines+=['','Japanese newdoc metadata are sentence labels, not evidence of distinct articles. Cantonese has four documented source ranges and remains secondary, never practice data. Readme and licence links for every pinned source are in audit.json; the repository licence label alone does not resolve its source-text caveat.','','## Next step','','Find recoverable original-document mappings and clarify text provenance, or replace these primary sources with collections that provide those details. Keep the current plan unchanged until a dated amendment is written. Do not weaken the rules merely because the downloaded data fail them. No approved split manifest is created in this round.','','## Reproduction','','Run `.venv/bin/python scripts/fetch_cjk_candidates.py` to retrieve the pinned acquisition files, then the audit script in a new output directory (the script intentionally refuses to overwrite audit-01). Raw files stay in ignored .cache/cjk_ud; reports contain IDs, hashes and counts only.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'status':result['status'],'duplicate_screen':result['duplicate_screen'],'feature_check':feature_check},indent=2),flush=True)
if __name__=='__main__':main()
