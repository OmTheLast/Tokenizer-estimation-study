"""Verify ID parity, corpus preservation, per-row metadata and independent arithmetic."""
import argparse,hashlib,json,math
from fractions import Fraction
from pathlib import Path
from tokenizers import Tokenizer
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def shastr(s):return hashlib.sha256(s.encode()).hexdigest()
def quantile(values,p):
    x=sorted(Fraction(v) for v in values);pos=(len(x)-1)*p;lo=pos.numerator//pos.denominator;hi=min(lo+1,len(x)-1)
    return float(x[lo]+(pos-lo)*(x[hi]-x[lo]))
def check(actual,expected):
    for k,v in expected.items():
        if v is None:assert actual[k] is None,(k,actual)
        else:assert math.isclose(actual[k],v,rel_tol=1e-12,abs_tol=1e-12),(k,actual[k],v)
def ratio(a,b):
    pairs=list(zip(a,b,strict=True));values=[Fraction(x['token_count'],y['token_count']) for x,y in pairs]
    clean=[v for v,(x,y) in zip(values,pairs) if not x['unknown_tokens'] and not y['unknown_tokens']]
    gm=lambda vs:math.exp(math.fsum(math.log(float(v)) for v in vs)/len(vs))
    return {'n':len(values),'geometric_mean':gm(values),'median':quantile(values,Fraction(1,2)),'p10':quantile(values,Fraction(1,10)),'p90':quantile(values,Fraction(9,10)),'min':float(min(values)),'max':float(max(values)),'unknown_free_n':len(clean),'unknown_free_geometric_mean':gm(clean) if clean else None}
def main(base):
    out=base/'verification.json';assert not out.exists(),'Do not overwrite verification'
    plan=json.loads((ROOT/'config/text-types-v1.json').read_text())
    for key in ['corpus','protocol','builder']:assert sha(ROOT/plan[key])==plan[key+'_sha256']
    corpus=json.loads((ROOT/plan['corpus']).read_text());fixtures={f['id']:f for f in corpus['inputs']};assert len(fixtures)==188
    rows=json.loads((base/'run-01/measurements.json').read_text());table={(r['model_key'],r['id']):r for r in rows};assert len(table)==len(rows)==1128
    assert set(table)=={(m,f) for m in plan['models'] for f in fixtures}
    assert sum(r['role']=='primary' for r in rows)==1080 and sum(r['role']=='probe' for r in rows)==48
    parity=0;metadata=0;assets=0
    for name,digest in plan['tokenizer_locks'].items():
        p=ROOT/'config'/name;assert sha(p)==digest;lock=json.loads(p.read_text());cache=ROOT/lock['cache_directory'];m=lock['model_key']
        for a in lock['assets']:assert sha(cache/a['filename'])==a['sha256'];assets+=1
        native=Tokenizer.from_file(str(cache/'tokenizer.json'));definition=json.loads(native.to_str());unk=definition['model'].get('unk_id')
        if unk is None and definition['model'].get('unk_token') is not None:unk=native.token_to_id(definition['model']['unk_token'])
        js=json.loads((base/'js-01'/f'{m}.json').read_text());assert js['status']=='encoded';jrows={r['id']:r for r in js['rows']};assert set(jrows)==set(fixtures)
        for fid,f in fixtures.items():
            r=table[m,fid];s=jrows[fid];text=f['text'];assert shastr(text)==r['text_sha256']==s['text_sha256']==f['text_sha256']
            for key in ['scenario','condition','format','item_count','role']:assert r[key]==f[key]
            assert r['tokenizer_revision']==lock['revision']
            assert r['token_count']==s['token_count'] and r['id_sequence_sha256']==s['id_sequence_sha256'];parity+=1
            ids=native.encode(text,add_special_tokens=False).ids;decoded=native.decode(ids,skip_special_tokens=False);normalized=native.normalizer.normalize_str(text) if native.normalizer else text
            assert r['token_count']==len(ids) and shastr(','.join(map(str,ids)))==r['id_sequence_sha256']
            assert r['unknown_tokens']==(ids.count(unk) if unk is not None else 0)
            assert r['normalization_changed']==(normalized!=text) and r['decode_exact']==(decoded==text)
            assert r['decoded_sha256']==shastr(decoded) and r['normalized_characters']==len(normalized)
            assert r['characters']==len(text) and r['utf8_bytes']==len(text.encode())
            assert r['with_special_count']==len(native.encode(text,add_special_tokens=True).ids)
            assert r['special_delta']==r['with_special_count']-len(ids);metadata+=1
    primary=[r for r in rows if r['role']=='primary'];lookup={(r['model_key'],r['condition'],r['format'],r['scenario']):r for r in primary}
    get=lambda m,c,f:[lookup[m,c,f,f's{i:02d}'] for i in range(1,13)]
    result=json.loads((base/'analysis-02/summary.json').read_text());numeric=0
    assert [len(result[k]) for k in ['cells','tokenizer_ratios','format_to_prose_ratios','pretty_to_compact_json_ratios']]==[90,540,90,18]
    assert {(r['model_key'],r['condition'],r['format']) for r in result['cells']}=={(m,c,f) for m in plan['models'] for c in plan['conditions'] for f in plan['formats']}
    assert {(r['numerator'],r['denominator'],r['condition'],r['format']) for r in result['tokenizer_ratios']}=={(a,b,c,f) for a in plan['models'] for b in plan['models'] for c in plan['conditions'] for f in plan['formats']}
    assert {(r['model_key'],r['condition'],r['numerator_format']) for r in result['format_to_prose_ratios']}=={(m,c,f) for m in plan['models'] for c in plan['conditions'] for f in plan['formats']}
    assert {(r['model_key'],r['condition']) for r in result['pretty_to_compact_json_ratios']}=={(m,c) for m in plan['models'] for c in plan['conditions']}
    for r in result['cells']:
        rr=get(r['model_key'],r['condition'],r['format']);counts=[x['token_count'] for x in rr]
        expected={'n':12,'median_count':quantile(counts,Fraction(1,2)),'p10_count':quantile(counts,Fraction(1,10)),'p90_count':quantile(counts,Fraction(9,10)),'median_tokens_per_100_codepoints':quantile([Fraction(100*x['token_count'],x['characters']) for x in rr],Fraction(1,2)),'unknown_input_rate':sum(x['unknown_tokens']>0 for x in rr)/12,'normalization_change_rate':sum(x['normalization_changed'] for x in rr)/12,'decode_mismatch_rate':sum(not x['decode_exact'] for x in rr)/12};check(r,expected);numeric+=len(expected)
    for r in result['tokenizer_ratios']:
        expected=ratio(get(r['numerator'],r['condition'],r['format']),get(r['denominator'],r['condition'],r['format']));check(r,expected);numeric+=len(expected)
    for r in result['format_to_prose_ratios']:
        assert r['denominator_format']=='prose';expected=ratio(get(r['model_key'],r['condition'],r['numerator_format']),get(r['model_key'],r['condition'],'prose'));check(r,expected);numeric+=len(expected)
    for r in result['pretty_to_compact_json_ratios']:
        expected=ratio(get(r['model_key'],r['condition'],'json_pretty'),get(r['model_key'],r['condition'],'json_compact'));check(r,expected);numeric+=len(expected)
    assert (base/'analysis-01/summary.json').read_bytes()==(base/'analysis-02/summary.json').read_bytes()
    report={'status':'passed','js_python_id_sequence_hash_matches':parity,'row_metadata_and_special_counts_recomputed':metadata,'source_asset_files_verified':assets,'summary_groups_verified':738,'summary_numeric_values_verified':numeric,'primary_unknown_input_count':sum(r['unknown_tokens']>0 for r in primary),'probe_unknown_input_count':sum(r['role']=='probe' and r['unknown_tokens']>0 for r in rows),'all_expected_cells_present':True,'failed_plot_attempt_numeric_summaries_unchanged':True,'arithmetic':'Independent math.fsum/log and exact Fraction quantile interpolation; does not import analysis or NumPy.','verifier_sha256':sha(Path(__file__)),'plan_sha256':sha(ROOT/'config/text-types-v1.json'),'measurements_sha256':sha(base/'run-01/measurements.json'),'summary_sha256':sha(base/'analysis-02/summary.json'),'limits':'ID sequence hashes verify agreement between two runtimes, not representativeness or algorithm causality. Decode metadata independently recomputed in Python, not cross-runtime decoding parity.'}
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);a=p.parse_args();base=(ROOT/a.base).resolve();assert base.is_relative_to(ROOT/'results');main(base)
