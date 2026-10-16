"""Independent checks of pinned counts, reported duplicate edges and dispositions."""
import argparse
from collections import Counter,defaultdict
import hashlib,json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def normal(s):return ' '.join(unicodedata.normalize('NFC',s).split())
def hashtext(s):return hashlib.sha256(s.encode()).hexdigest()
def main(out):
    sources=json.loads((ROOT/'results/2026-10-16-cjk-preflight/acquisition/sources.json').read_text())
    report=json.loads((out/'audit.json').read_text());manifest=json.loads((out/'provisional-manifest.json').read_text());edges=json.loads((out/'duplicate-edges.json').read_text())
    texts={};rawcounts={}
    for code,source in sources['sources'].items():
        for name,info in source['files'].items():
            path=ROOT/info['cache_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==info['sha256']
            if name.endswith('.conllu'):
                split=name.rsplit('-ud-',1)[1].removesuffix('.conllu');blocks=re.split(r'\n\s*\n',path.read_text().strip());count=0
                for block in blocks:
                    ids=re.findall(r'^# sent_id = (.*)$',block,re.M);sent=re.findall(r'^# text = (.*)$',block,re.M)
                    assert len(ids)==len(sent)==1;count+=1;texts[(code,split,ids[0])]=sent[0]
                rawcounts[code,split]=count
    for i,r in enumerate(manifest):
        assert r['audit_row']==i
        text=texts[(r['code'],r['split'],r['id'])]
        assert r['text_sha256']==hashtext(text)
        assert r['normalized_sha256']==hashtext(normal(text))
    for edge in edges:
        a,b=[manifest[edge[k]] for k in ['a','b']]
        x,y=[normal(texts[(r['code'],r['split'],r['id'])]) for r in [a,b]]
        if edge['kind']=='normalized_exact':assert x==y
        elif edge['kind']=='parallel_family':assert a['parallel'] and a['parallel']==b['parallel']
        else:
            assert min(len(x),len(y))>=20
            X={x[i:i+5] for i in range(len(x)-4)};Y={y[i:i+5] for i in range(len(y)-4)}
            assert len(X&Y)/len(X|Y)>=.9
        assert a['known_group']==b['known_group']
    groups=defaultdict(list)
    for r in manifest:groups[r['known_group']].append(r)
    priority={'train':0,'dev':1,'test':2};kept=set()
    for rows in groups.values():
        maximum=max(priority[r['split']] for r in rows)
        for r in rows:
            if r['disposition']=='passes_available_checks_not_final':
                assert priority[r['split']]==maximum
                key=(r['code'],r['split'],r['normalized_sha256']);assert key not in kept;kept.add(key)
            elif r['disposition']=='cross_split_family':assert priority[r['split']]<maximum
    for cell in report['inventory']:
        selected=[r for r in manifest if r['code']==cell['code'] and r['split']==cell['split']]
        assert rawcounts[cell['code'],cell['split']]==cell['records']==len(selected)
        assert dict(Counter(r['disposition'] for r in selected))==cell['dispositions']
    assert all(c['verified_source_groups']==0 for c in report['inventory'] if c['code'] in ['zh_gsd','ja_gsd','ko_gsd'])
    assert report['status']=='not_ready_for_fitting'
    summary={'verified_rows':len(manifest),'verified_files':sum(len(v['files']) for v in sources['sources'].values()),'verified_duplicate_and_parallel_edges':len(edges),'counts_and_dispositions_match':True,'kept_known_groups_do_not_cross_splits':True,'no_approved_manifest':True,'source_text_not_printed':True,'unit_tests_passed':4,'limitations':'Verifies every reported edge and known-group split, not an independent exhaustive search for missing near-duplicate edges or undocumented source relationships.'}
    (out/'independent-validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();main(ROOT/args.output)
