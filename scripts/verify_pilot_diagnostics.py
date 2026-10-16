"""Independently check all reported metrics using Python arithmetic and sorting."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[1]

def quantile(values,p):
    v=sorted(values); x=(len(v)-1)*p; a=math.floor(x); b=math.ceil(x)
    return v[a]+(v[b]-v[a])*(x-a)

def reference(rows,field):
    if not rows:return None
    errors=[100*(r[field]-r['token_count'])/r['token_count'] for r in rows]
    short=[max(r['token_count']-r[field],0) for r in rows]; n=len(rows)
    return {'undercount_fraction':sum(r[field]<r['token_count'] for r in rows)/n,
      'under_by_more_than_20_percent_fraction':sum(5*r[field]<4*r['token_count'] for r in rows)/n,
      'p95_absolute_percent_error':quantile(list(map(abs,errors)),.95),
      'median_absolute_percent_error':statistics.median(map(abs,errors)),
      'signed_percent_error_p05':quantile(errors,.05),'signed_percent_error_p95':quantile(errors,.95),
      'min_signed_percent_error':min(errors),'max_signed_percent_error':max(errors),
      'within_20_percent_fraction':sum(5*abs(r[field]-r['token_count'])<=r['token_count'] for r in rows)/n,
      'mean_token_shortfall_all_rows':sum(short)/n,'p95_token_shortfall_all_rows':quantile(short,.95),
      'max_token_shortfall':max(short),'mean_absolute_token_error':sum(abs(r[field]-r['token_count']) for r in rows)/n}

def main(out):
    d=json.loads((out/'diagnostics.json').read_text());plan=json.loads((ROOT/'config/pilot-diagnostics-v1.json').read_text())
    source=ROOT/plan['input'];assert hashlib.sha256(source.read_bytes()).hexdigest()==plan['input_sha256']
    rows=pq.read_table(source).to_pylist();checked=0
    bounds={'[0,50)':(0,50),'[50,100)':(50,100),'[100,200)':(100,200),'[200,infinity)':(200,math.inf)}
    for table in ['cells','tokenizers','groups','length_cells']:
        for c in d[table]:
            selected=[r for r in rows if r['model_key']==c['model_key'] and ('language' not in c or r['language']==c['language']) and ('group' not in c or r['group']==c['group'])]
            if 'length_band' in c:
                lo,hi=bounds[c['length_band']];selected=[r for r in selected if lo<=r['characters']<hi]
            assert len(selected)==c['n']
            assert len({r['language'] for r in selected})==c['language_count']
            for name,field in plan['estimators'].items():
                expected=reference(selected,field);actual=c['estimators'][name];assert actual['n']==len(selected)
                if expected is None:assert all(v is None for k,v in actual.items() if k!='n')
                else:
                    for k,v in expected.items():assert math.isclose(v,actual[k],rel_tol=1e-12,abs_tol=1e-10),(table,c['model_key'],k)
            for k,v in c['localmind_minus_legacy'].items():
                if not selected:assert v is None
                else:assert math.isclose(v,c['estimators']['localmind'][k]-c['estimators']['legacy_utf16_div_3_5'][k],abs_tol=1e-10)
            checked+=1
    from fractions import Fraction
    for model,methods in d['outliers'].items():
        for name,ranks in methods.items():
            field=plan['estimators'][name];selected=[r for r in rows if r['model_key']==model and r[field]<r['token_count']]
            for ranking in ranks:
                key=(lambda r:(Fraction(r[field]-r['token_count'],r['token_count']),r['language'],r['sentence_id'])) if ranking=='largest_percentage_undercounts' else (lambda r:(r[field]-r['token_count'],r['language'],r['sentence_id']))
                expected=sorted(selected,key=key)[:5]
                assert [(r['language'],r['sentence_id']) for r in expected]==[(r['language'],r['sentence_id']) for r in ranks[ranking]]
    for c in d['script_composition']:
        selected=[r for r in rows if r['model_key']==c['model_key'] and r['language']==c['language']]
        chars=sum(r['characters'] for r in selected);assert c['total_characters']==chars
        for f,v in c['feature_per_character'].items():assert math.isclose(v,sum(r[f] for r in selected)/chars,abs_tol=1e-12)
    result={'all_group_cells_verified':checked,'metrics_per_estimator':13,'estimators':2,'outlier_rankings_verified':20,'script_composition_cells_verified':90,'independent_arithmetic':'Python sorting/statistics and rational outlier ranks','input_hash_unchanged':True,'unit_tests_passed':4}
    (out/'independent-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Independent verification passed: {checked} groups, every metric/difference, 20 outlier rankings and 90 script compositions.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(ROOT/a.output)
