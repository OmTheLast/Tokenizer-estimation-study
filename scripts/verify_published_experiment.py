"""Independent runtime/metadata and arithmetic audit; does not import analysis or NumPy."""
import argparse
from collections import defaultdict, Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from tokenizers import Tokenizer
from verify_text_types import quantile, check, ratio
from prepare_published_inputs import ROOT, sha, text_sha


def without_json_whitespace(text):
    inside=escape=False;out=[]
    for c in text:
        if inside or c not in ' \t\r\n':out.append(c)
        if escape:escape=False
        elif inside and c=='\\':escape=True
        elif c=='"':inside=not inside
    assert not inside
    return ''.join(out)


def main(base):
    dest=base/'verification.json';assert not dest.exists()
    plan_path=ROOT/'config/published-text-experiment-v1.json';plan=json.loads(plan_path.read_text())
    for path,h in plan['files_sha256'].items():assert sha(ROOT/path)==h,path
    lock=json.loads((ROOT/'config/published-text-corpus-v1.lock.json').read_text())
    for path,h in lock['files_sha256'].items():assert sha(ROOT/path)==h,path
    assert sha(ROOT/plan['private_corpus'])==plan['private_corpus_sha256']
    inputs=json.loads((ROOT/plan['private_corpus']).read_text())['inputs']
    fixtures={f['id']:f for f in inputs};assert len(fixtures)==140
    meta=json.loads((ROOT/plan['input_manifest']).read_text())['inputs']
    assert [{k:v for k,v in f.items() if k!='text'} for f in inputs]==meta
    samples=json.loads((ROOT/lock['manifest']).read_text())['samples']
    json_checks=0
    for sample in samples:
        raw=(ROOT/lock['raw_root']/sample['repo']/sample['revision']/sample['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==sample['full_file_sha256']
        segment=raw[sample['start_byte']:sample['end_byte']]
        f=fixtures[sample['sample_id']+'/original'];assert f['text'].encode()==segment
        if sample['category']=='json':
            compact=fixtures[sample['sample_id']+'/json_compact']['text']
            pretty=fixtures[sample['sample_id']+'/json_pretty']['text']
            assert without_json_whitespace(pretty)==compact
            # Independent ordered pairs representation (not the builder's fingerprint).
            parse=lambda t:json.loads(t,parse_int=Decimal,parse_float=Decimal,object_pairs_hook=lambda pairs:pairs)
            assert parse(compact)==parse(pretty)==parse(f['text'])
            assert not compact.endswith('\n') and not pretty.endswith('\n');json_checks+=1
    rows=json.loads((base/'run-01/measurements.json').read_text());table={(r['model_key'],r['id']):r for r in rows}
    assert len(table)==len(rows)==840
    assert set(table)=={(m,f) for m in plan['models'] for f in fixtures}
    assert Counter(r['role'] for r in rows)=={'original':600,'json_variant':240}
    parity=metadata=assets=derived_parity=0
    for name,h in plan['tokenizer_locks'].items():
        path=ROOT/'config'/name;assert sha(path)==h;source=json.loads(path.read_text());m=source['model_key'];cache=ROOT/source['cache_directory']
        for a in source['assets']:assert sha(cache/a['filename'])==a['sha256'];assets+=1
        native=Tokenizer.from_file(str(cache/'tokenizer.json'));definition=json.loads(native.to_str())
        assert not definition['truncation'] and not definition['padding'] and not definition['model'].get('dropout')
        unknown=definition['model'].get('unk_id')
        if unknown is None and definition['model'].get('unk_token') is not None:unknown=native.token_to_id(definition['model']['unk_token'])
        canonical=None
        if 'derived_asset' in source:
            a=source['derived_asset'];assert sha(cache/a['filename'])==a['sha256'];canonical=Tokenizer.from_file(str(cache/a['filename']))
        js=json.loads((base/'js-01'/f'{m}.json').read_text());assert js['status']=='encoded';jrows={r['id']:r for r in js['rows']};assert set(jrows)==set(fixtures)
        for fid,f in fixtures.items():
            r,s=table[m,fid],jrows[fid];text=f['text'];assert text_sha(text)==f['text_sha256']
            for k,v in f.items():
                if k!='text':assert r[k]==v,(m,fid,k)
            assert r['tokenizer_revision']==source['revision']
            for k in ('text_sha256','token_count','id_sequence_sha256'):assert r[k]==s[k]
            parity+=1
            ids=native.encode(text,add_special_tokens=False).ids
            if canonical is not None:assert canonical.encode(text,add_special_tokens=False).ids==ids;derived_parity+=1
            decoded=native.decode(ids,skip_special_tokens=False)
            normalized=native.normalizer.normalize_str(text) if native.normalizer else text
            expected={'token_count':len(ids),'with_special_count':len(native.encode(text,add_special_tokens=True).ids),
                'unknown_tokens':ids.count(unknown) if unknown is not None else 0,
                'characters':len(text),'utf8_bytes':len(text.encode()),'normalized_characters':len(normalized),
                'normalization_changed':normalized!=text,'decode_exact':decoded==text,
                'decode_equal_without_whitespace':''.join(decoded.split())==''.join(text.split()),
                'decoded_sha256':text_sha(decoded),'id_sequence_sha256':text_sha(','.join(map(str,ids))),
                'algorithm':type(native.model).__name__}
            for k,v in expected.items():assert r[k]==v,(m,fid,k)
            assert r['special_delta']==r['with_special_count']-r['token_count'];metadata+=1
    summary=json.loads((base/'analysis-01/summary.json').read_text())
    expected_groups=defaultdict(set)
    for f in inputs:
        if f['role']=='original':
            expected_groups['category',f['category']].add(f['id']);expected_groups['stratum',f['stratum']].add(f['id'])
            for lo,hi in plan['length_bands']:
                if lo<=f['characters']<=hi:expected_groups['category_length',f"{f['category']}/{lo}-{hi}"].add(f['id'])
        else:
            for s in ('all',f['stratum']):expected_groups['json_variant',f['format']+'/'+s].add(f['id'])
    groups={(g['scope'],g['key']):g for g in summary['groups']}
    assert len(groups)==len(summary['groups'])==len(expected_groups)
    for key,ids in expected_groups.items():assert groups[key]['input_ids']==sorted(ids)
    get=lambda m,scope,key:[table[m,i] for i in sorted(expected_groups[scope,key])]
    assert {(r['model_key'],r['scope'],r['key']) for r in summary['cells']}=={(m,s,k) for m in plan['models'] for s,k in groups}
    assert len(summary['cells'])==6*len(groups)
    original_groups=[k for k in groups if k[0]!='json_variant']
    assert len(summary['tokenizer_ratios'])==36*len(original_groups)
    assert {(r['numerator'],r['denominator'],r['scope'],r['key']) for r in summary['tokenizer_ratios']}=={(a,b,s,k) for a in plan['models'] for b in plan['models'] for s,k in original_groups}
    numeric=0
    for cell in summary['cells']:
        rr=get(cell['model_key'],cell['scope'],cell['key']);n=len(rr);counts=[r['token_count'] for r in rr]
        expected={'n':n,'median_count':quantile(counts,Fraction(1,2)),
            'p10_count':quantile(counts,Fraction(1,10)),'p90_count':quantile(counts,Fraction(9,10)),
            'median_tokens_per_100_codepoints':quantile([Fraction(100*r['token_count'],r['characters']) for r in rr],Fraction(1,2)),
            'unknown_inputs':sum(r['unknown_tokens']>0 for r in rr),'normalization_changed_inputs':sum(r['normalization_changed'] for r in rr),
            'decode_mismatches':sum(not r['decode_exact'] for r in rr)}
        expected.update(unknown_input_rate=expected['unknown_inputs']/n,normalization_change_rate=expected['normalization_changed_inputs']/n,decode_mismatch_rate=expected['decode_mismatches']/n)
        check(cell,expected);numeric+=len(expected)
    for cell in summary['tokenizer_ratios']:
        expected=ratio(get(cell['numerator'],cell['scope'],cell['key']),get(cell['denominator'],cell['scope'],cell['key']))
        check(cell,expected);numeric+=len(expected)
    jstrata=sorted({f['stratum'] for f in inputs if f['category']=='json'})
    assert len(summary['pretty_compact_ratios'])==18
    assert {(r['model_key'],r['stratum']) for r in summary['pretty_compact_ratios']}=={(m,s) for m in plan['models'] for s in ['all']+jstrata}
    for cell in summary['pretty_compact_ratios']:
        s=cell['stratum'];ids=sorted(f['sample_id'] for f in inputs if f['category']=='json' and f['role']=='original' and (s=='all' or f['stratum']==s))
        expected=ratio([table[cell['model_key'],i+'/json_pretty'] for i in ids],[table[cell['model_key'],i+'/json_compact'] for i in ids]);check(cell,expected);numeric+=len(expected)
    points=json.loads((base/'analysis-01/per-input-ratios.json').read_text());assert len(points)==3600
    assert len({(p['input_id'],p['numerator'],p['denominator']) for p in points})==3600
    for p in points:
        f=fixtures[p['input_id']];assert f['role']=='original' and f['category']==p['category'] and f['stratum']==p['stratum']
        a,b=table[p['numerator'],p['input_id']],table[p['denominator'],p['input_id']]
        assert p['ratio']==a['token_count']/b['token_count'] and p['unknown_free']==(not a['unknown_tokens'] and not b['unknown_tokens'])
    jp=json.loads((base/'analysis-01/per-json-ratios.json').read_text());assert len(jp)==120
    assert len({(p['model_key'],p['sample_id']) for p in jp})==120
    for p in jp:
        a,b=table[p['model_key'],p['sample_id']+'/json_pretty'],table[p['model_key'],p['sample_id']+'/json_compact']
        assert p['ratio']==a['token_count']/b['token_count'] and p['stratum']==a['stratum']
        assert p['unknown_free']==(not a['unknown_tokens'] and not b['unknown_tokens'])
    report={'status':'passed','python_js_id_hash_matches':parity,'row_metadata_recomputed':metadata,
            'tokenizer_asset_files_verified':assets,'unigram_canonical_parity':derived_parity,
            'json_value_and_whitespace_pairs_verified':json_checks,'summary_groups_verified':sum(len(summary[k]) for k in ('cells','tokenizer_ratios','pretty_compact_ratios')),
            'numeric_summary_values_verified':numeric,'per_input_ratios_verified':len(points)+len(jp),
            'arithmetic':'Separate math.fsum/log and exact Fraction quantile implementation; no analysis/NumPy imports.',
            'verifier_sha256':sha(Path(__file__)),'arithmetic_helpers_sha256':sha(ROOT/'scripts/verify_text_types.py'),
            'plan_sha256':sha(plan_path),'measurements_sha256':sha(base/'run-01/measurements.json'),
            'summary_sha256':sha(base/'analysis-01/summary.json'),
            'limits':'Cross-runtime ID/count parity; decoding metadata recomputed in Python, not independently decoded in JS. Not a human review.'}
    dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);main(p.parse_args().base)
