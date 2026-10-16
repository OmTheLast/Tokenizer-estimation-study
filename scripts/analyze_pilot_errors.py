"""Offline exploratory diagnostics for the frozen pilot; never fits an estimator."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'config/pilot-diagnostics-v1.json'
FIELDS = ['undercount_fraction', 'under_by_more_than_20_percent_fraction',
          'p95_absolute_percent_error', 'median_absolute_percent_error',
          'signed_percent_error_p05', 'signed_percent_error_p95',
          'min_signed_percent_error', 'max_signed_percent_error',
          'within_20_percent_fraction', 'mean_token_shortfall_all_rows',
          'p95_token_shortfall_all_rows', 'max_token_shortfall', 'mean_absolute_token_error']
LABELS = {'qwen35-4b':'Qwen', 'bonsai-ternary-4b':'Bonsai', 'lfm2-1.2b':'LFM',
          'gemma4-e2b':'Gemma', 'minicpm5-2b-gguf':'MiniCPM*'}
BANDS = ['[0,50)', '[50,100)', '[100,200)', '[200,infinity)']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, obj):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
    temp.replace(path)

def band(n):
    return BANDS[0 if n < 50 else 1 if n < 100 else 2 if n < 200 else 3]

def metrics(rows, field):
    if not rows:
        return {'n': 0, **dict.fromkeys(FIELDS)}
    actual = np.array([r['token_count'] for r in rows], dtype=np.int64)
    pred = np.array([r[field] for r in rows], dtype=np.int64)
    if np.any(actual <= 0):
        raise ValueError('Nonpositive actual count')
    error = 100 * (pred - actual) / actual
    absolute = np.abs(error)
    short = np.maximum(actual - pred, 0)
    q = lambda values, p: float(np.quantile(values, p, method='linear'))
    # Integer comparisons keep strict/inclusive 20% boundaries exact.
    return {'n': len(rows),
        'undercount_fraction': float(np.mean(pred < actual)),
        'under_by_more_than_20_percent_fraction': float(np.mean(5 * pred < 4 * actual)),
        'p95_absolute_percent_error': q(absolute, .95),
        'median_absolute_percent_error': q(absolute, .5),
        'signed_percent_error_p05': q(error, .05), 'signed_percent_error_p95': q(error, .95),
        'min_signed_percent_error': float(error.min()), 'max_signed_percent_error': float(error.max()),
        'within_20_percent_fraction': float(np.mean(5 * np.abs(pred - actual) <= actual)),
        'mean_token_shortfall_all_rows': float(np.mean(short)), 'p95_token_shortfall_all_rows': q(short, .95),
        'max_token_shortfall': int(short.max()), 'mean_absolute_token_error': float(np.mean(np.abs(pred-actual)))}

def group_result(rows, estimators, **keys):
    stats = {name: metrics(rows, field) for name, field in estimators.items()}
    difference = {k: None if not rows else stats['localmind'][k]-stats['legacy_utf16_div_3_5'][k] for k in FIELDS}
    return {**keys, 'n': len(rows), 'language_count': len({r['language'] for r in rows}),
            'estimators': stats, 'localmind_minus_legacy': difference}

def outliers(rows, field, k=5):
    def details(r):
        numeric = {key: value for key, value in r.items() if isinstance(value, (int, float, bool))}
        return {'language':r['language'], 'sentence_id':r['sentence_id'], **numeric,
                'prediction':r[field], 'signed_percent_error':100*(r[field]-r['token_count'])/r['token_count'],
                'token_shortfall': max(r['token_count']-r[field], 0)}
    under = [r for r in rows if r[field] < r['token_count']]
    percent = sorted(under, key=lambda r: ((r[field]-r['token_count'])/r['token_count'], r['language'], r['sentence_id']))[:k]
    tokens = sorted(under, key=lambda r: (r[field]-r['token_count'], r['language'], r['sentence_id']))[:k]
    return {'largest_percentage_undercounts':list(map(details, percent)), 'largest_token_shortfalls':list(map(details, tokens))}

def write_report(out, result):
    lines = ['# Frozen-pilot error analysis', '',
        'Exploratory diagnostics of 9,000 measurements from 100 aligned sentence IDs, 18 language varieties and five tokenizer profiles. Both estimators remain unchanged. No model inference, fitting, new data access or devtest access occurred.', '',
        'Every rate uses all rows in the stated cell. Shortfall means max(actual − predicted, 0), including zeros. The 20% cutoff is descriptive, not a safety target. Quantiles use linear interpolation. Empty cells have null metrics.', '',
        '## Overall results', '',
        '| Tokenizer | Estimator | N | Undercount | Under by >20% | Median abs. error | P95 abs. error | Mean shortfall (tokens) | Max shortfall |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for cell in result['tokenizers']:
        for name, m in cell['estimators'].items():
            lines.append(f"| {LABELS[cell['model_key']]} | {name} | {m['n']} | {100*m['undercount_fraction']:.2f}% | {100*m['under_by_more_than_20_percent_fraction']:.2f}% | {m['median_absolute_percent_error']:.2f}% | {m['p95_absolute_percent_error']:.2f}% | {m['mean_token_shortfall_all_rows']:.2f} | {m['max_token_shortfall']} |")
    lines += ['', '## Where the older heuristic does better', '',
        'Counts below compare all 90 cells separately for each metric, on the same texts. A method can win on one metric and lose on another; lower undercount alone can result from excessive overestimation.', '',
        '| Metric | LocalMind lower | Equal | Legacy lower |', '| --- | ---: | ---: | ---: |']
    for metric in ['median_absolute_percent_error','p95_absolute_percent_error','under_by_more_than_20_percent_fraction','mean_absolute_token_error']:
        ds = [c['localmind_minus_legacy'][metric] for c in result['cells']]
        lines.append(f"| {metric} | {sum(d < -1e-12 for d in ds)} | {sum(abs(d)<=1e-12 for d in ds)} | {sum(d > 1e-12 for d in ds)} |")
    lines += ['', 'Cells where legacy has lower median absolute error:', '']
    for c in result['cells']:
        if c['localmind_minus_legacy']['median_absolute_percent_error'] > 1e-12:
            lm=c['estimators']['localmind']; old=c['estimators']['legacy_utf16_div_3_5']
            lines.append(f"- {LABELS[c['model_key']]} / {c['language']}: LocalMind {lm['median_absolute_percent_error']:.2f}%, legacy {old['median_absolute_percent_error']:.2f}%.")
    lines += ['', 'Paired signed-error differences are directional, not generic better/worse scores. A more negative signed error means more underestimation. Lower undercount rates must be read alongside absolute error and overestimation.', '']
    lines += ['', '## All tokenizer-language cells', '',
        'Each cell contains 100 texts. Percentages below summarize its unchanged LocalMind predictions. JSON includes every metric for both estimators and paired differences.', '',
        '| Tokenizer | Language | Undercount | Under by >20% | Median abs. error | P95 abs. error | Mean token shortfall | Legacy median abs. error |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for c in result['cells']:
        m=c['estimators']['localmind']; old=c['estimators']['legacy_utf16_div_3_5']
        lines.append(f"| {LABELS[c['model_key']]} | {c['language']} | {100*m['undercount_fraction']:.0f}% | {100*m['under_by_more_than_20_percent_fraction']:.0f}% | {m['median_absolute_percent_error']:.2f}% | {m['p95_absolute_percent_error']:.2f}% | {m['mean_token_shortfall_all_rows']:.2f} | {old['median_absolute_percent_error']:.2f}% |")
    lines += ['', '## Language groups', '', '| Tokenizer | Group | Languages | N | LocalMind under by >20% | Legacy under by >20% |', '| --- | --- | ---: | ---: | ---: | ---: |']
    for c in result['groups']:
        lines.append(f"| {LABELS[c['model_key']]} | {c['group']} | {c['language_count']} | {c['n']} | {100*c['estimators']['localmind']['under_by_more_than_20_percent_fraction']:.2f}% | {100*c['estimators']['legacy_utf16_div_3_5']['under_by_more_than_20_percent_fraction']:.2f}% |")
    lines += ['', '## Largest LocalMind misses', '',
        'One example per ranking and tokenizer is shown; diagnostics.json preserves the planned top five for each estimator. Source text and token sequences are not included.', '',
        '| Tokenizer | Ranking | Language | ID | Predicted | Actual | Signed error | Missing tokens |', '| --- | --- | --- | --- | ---: | ---: | ---: | ---: |']
    for model, methods in result['outliers'].items():
        for ranking, selected in methods['localmind'].items():
            if selected:
                r=selected[0]
                lines.append(f"| {LABELS[model]} | {ranking} | {r['language']} | {r['sentence_id']} | {r['prediction']} | {r['token_count']} | {r['signed_percent_error']:.2f}% | {r['token_shortfall']} |")
    lines += ['', '## Length and script diagnostics', '',
        'diagnostics.json contains all 360 tokenizer-language-length cells, including empty cells, for the fixed Unicode-character bands [0,50), [50,100), [100,200), and [200,infinity). It also contains script feature totals divided by total Unicode characters for all 90 cells, and numeric features for selected outliers. Extra script diagnostics overlap the baseline classes and must not be summed as disjoint categories.', '',
        'Compare lengths within a language and tokenizer before interpreting pooled patterns. Text length, script and content vary together; descriptive differences do not prove a causal effect. No new classifier, coefficient or safety margin was fitted.', '',
        '## Interpretation limits', '',
        'These repeated measurements are not 9,000 independent examples. No significance tests or confidence intervals are reported. The pilot summaries were inspected before the diagnostic plan was specified. Any hypotheses prompted by these results need independent tests. The shared CJK weight is a possible mechanism, not an established explanation.', '',
        'Small median errors do not bound individual undercounts. A large percentage error and a large absolute token shortfall need not select the same example. Count errors alone do not measure browser speed, model quality, or actual context-overflow frequency.', '',
        '*MiniCPM uses its HF JSON tokenizer; GGUF/browser equivalence remains unverified. Upstream fitting/training overlap is unknown. Raw FLORES+ data remain local and evaluation-only. No final devtest data were read.', '',
        'Reproduce from the project root: `.venv/bin/python scripts/analyze_pilot_errors.py --output results/pilot-diagnostics-new`. This requires the existing local pilot Parquet. Inputs, specification, source hashes and runtime versions are in validation.json.']
    length_lines=['# Fixed length-band diagnostics', '', 'All 360 prespecified tokenizer-language-length cells. Each band uses Unicode code points. Rates are within that band; empty cells are shown explicitly. LM = LocalMind; legacy = UTF-16 units / 3.5. These descriptive comparisons do not isolate a causal effect of length.', '', '| Tokenizer | Language | Band | N | LM under by >20% | Legacy under by >20% | LM median abs. error | Legacy median abs. error | LM mean shortfall |', '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for c in result['length_cells']:
        m=c['estimators']['localmind']; old=c['estimators']['legacy_utf16_div_3_5']
        values='— | — | — | — | —' if not c['n'] else f"{100*m['under_by_more_than_20_percent_fraction']:.2f}% | {100*old['under_by_more_than_20_percent_fraction']:.2f}% | {m['median_absolute_percent_error']:.2f}% | {old['median_absolute_percent_error']:.2f}% | {m['mean_token_shortfall_all_rows']:.2f}"
        length_lines.append(f"| {LABELS[c['model_key']]} | {c['language']} | {c['length_band']} | {c['n']} | {values} |")
    (out/'LENGTH_REPORT.md').write_text('\n'.join(length_lines)+'\n')
    lines += ['', 'All fixed length-band results: [LENGTH_REPORT.md](LENGTH_REPORT.md).', '', '## Script composition across the five CJK varieties', '', 'The same texts have the same character composition across tokenizers, so composition is shown once. Shares use totals over each variety’s 100 texts; categories shown here overlap and are not a partition.', '', '| Variety | Han | Kana | Hangul syllables | CJK punctuation | Baseline other class |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    first_model=result['tokenizers'][0]['model_key']
    for c in result['script_composition']:
        if c['model_key']==first_model and c['language'] in ['cmn_Hans','cmn_Hant','yue_Hant','jpn_Jpan','kor_Hang']:
            f=c['feature_per_character']; values=' | '.join(f"{100*f[k]:.2f}%" for k in ['han_named_characters','kana_block_characters','hangul_syllable_characters','cjk_punctuation_block_characters','class_other'])
            lines.append(f"| {c['language']} | {values} |")
    lines += ['', 'These different script mixtures are collapsed into one baseline CJK weight (plus other character classes). This motivates a controlled follow-up using separate development data; it does not establish that splitting the class would resolve the observed errors.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')

def run(output):
    plan=json.loads(PLAN.read_text()); source=ROOT/plan['input']
    if sha(source)!=plan['input_sha256']: raise ValueError('Frozen input hash mismatch')
    if plan['length_bands']['edges'] != [0,50,100,200,None] or plan['quantiles']['method']!='linear': raise ValueError('Unsupported plan')
    rows=pq.read_table(source).to_pylist(); est=plan['estimators']
    models=sorted({r['model_key'] for r in rows}); langs=sorted({r['language'] for r in rows}); ids={r['sentence_id'] for r in rows}
    assert len(rows)==plan['expected_rows'] and len(models)==5 and len(langs)==18 and len(ids)==100
    assert len({(r['model_key'],r['language'],r['sentence_id']) for r in rows})==len(rows)
    bycell=defaultdict(list)
    for r in rows:
        assert r['split']=='dev' and 'text' not in r and 'ids' not in r
        assert r['characters']>0 and r['token_count']>0
        bycell[r['model_key'],r['language']].append(r)
    result={'plan':plan['name'],'evidence_status':plan['evidence_status'],'cells':[], 'tokenizers':[], 'groups':[], 'length_cells':[], 'script_composition':[], 'outliers':{}}
    features=[k for k in rows[0] if k.startswith('class_') or (k.endswith('_characters') and k!='normalized_characters')]
    for model in models:
        modelrows=[r for r in rows if r['model_key']==model]
        result['tokenizers'].append(group_result(modelrows,est,model_key=model))
        result['outliers'][model]={name:outliers(modelrows,field,plan['outliers']['per_tokenizer_per_estimator']) for name,field in est.items()}
        for group in sorted({r['group'] for r in modelrows}):
            result['groups'].append(group_result([r for r in modelrows if r['group']==group],est,model_key=model,group=group))
        for lang in langs:
            selected=bycell[model,lang]; assert len(selected)==100 and {r['sentence_id'] for r in selected}==ids
            result['cells'].append(group_result(selected,est,model_key=model,language=lang))
            for label in BANDS:
                result['length_cells'].append(group_result([r for r in selected if band(r['characters'])==label],est,model_key=model,language=lang,length_band=label))
            denominator=sum(r['characters'] for r in selected)
            result['script_composition'].append({'model_key':model,'language':lang,'n':len(selected),'total_characters':denominator,'feature_per_character':{f:sum(r[f] for r in selected)/denominator for f in features}})
    output.mkdir(parents=True,exist_ok=False)
    save(output/'diagnostics.json',result); write_report(output,result)
    save(output/'validation.json',{'completed_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':sha(source),'plan_sha256':sha(PLAN),'script_sha256':sha(Path(__file__)),'python':platform.python_version(),'numpy':np.__version__,'rows':len(rows),'aligned_ids':len(ids),'cells':len(result['cells']),'length_cells':len(result['length_cells']),'empty_length_cells':sum(c['n']==0 for c in result['length_cells']),'groups':len(result['groups']),'no_fitting':True,'no_new_data_access':True,'all_cells_have_same_100_ids':True,'quantile_method':'linear','null_empty_cells':True})
    (output/'terminal-output.txt').write_text(f'Analyzed {len(rows)} saved rows: 90 language/tokenizer cells, 360 length cells, two frozen estimators.\nNo fitting, model inference or dataset access.\nExit code: 0\n')
    print(f"Analyzed {len(rows)} saved rows: 90 language/tokenizer cells, 360 length cells, two frozen estimators.")
    print('No fitting, model inference or dataset access. Output: '+str(output.relative_to(ROOT)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);args=parser.parse_args()
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to(ROOT/'results'):parser.error('Output must be under results/')
    run(output)
