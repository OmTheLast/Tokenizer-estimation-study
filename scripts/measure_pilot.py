"""Measure pinned tokenizers on the FLORES+ pilot, or test on old fixtures.

Usage: .venv/bin/python scripts/measure_pilot.py --output results/pilot-01
Use --smoke for existing-fixture infrastructure checks, never novel evidence.
Use --resume to reuse verified complete per-model shards after interruption.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import traceback
import unicodedata

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.cache/matplotlib'))
import pyarrow as pa
import pyarrow.parquet as pq
import tokenizers
from fetch_tokenizer import ROOT, sha256
from flores_pilot_data import load_pilot
from localmind_estimator import LocalMindEstimator
from pilot_features import features, CLASSES
from pilot_report import write_report
from verify_all_profiles import LOCKS, fetch_locked, save


def smoke_texts():
    source = ROOT / 'results/2026-10-07-all-profiles/run-01/estimator-cases.json'
    data = json.loads(source.read_text())['fixtures']
    texts = []
    for s in data:
        texts.append({'sentence_id': s['name'], 'language': 'existing-fixtures', 'language_label': 'Existing fixtures',
                      'group': 'Smoke only', 'text': s['text'], 'dataset': 'LocalMind-frozen-fixtures',
                      'dataset_revision': 'b39f0bc145a0c0926ba22247ee31cd369e0445b6', 'split': 'smoke', 'domain': 'mixed'})
    return texts, {'smoke_only': True, 'source_sha256': sha256(source)}


def run(out, smoke, log):
    if tokenizers.__version__ != '0.23.2':
        raise ValueError('Expected Python tokenizers 0.23.2')
    texts, provenance = smoke_texts() if smoke else load_pilot(log)
    expected = 38 if smoke else 1800
    if len(texts) != expected:
        raise ValueError(f'Expected {expected} source texts, received {len(texts)}')
    known = {s['text'] for s in json.loads((ROOT / 'results/2026-10-07-all-profiles/run-01/estimator-cases.json').read_text())['fixtures']}
    overlap = sum(t['text'] in known for t in texts)
    if not smoke and overlap:
        raise ValueError('Published fixture overlap found; review before running pilot')
    profiles = json.loads((ROOT / 'config/localmind-profiles.json').read_text())
    frozen_estimator = LocalMindEstimator(profiles)
    paths = ['scripts/measure_pilot.py', 'scripts/flores_pilot_data.py', 'scripts/pilot_features.py', 'scripts/pilot_report.py',
             'scripts/localmind_estimator.py', 'scripts/verify_all_profiles.py', 'scripts/fetch_tokenizer.py',
             'config/localmind-profiles.json', 'config/phase1-pilot.json', 'requirements-phase1.lock.txt'] + ['config/' + p for p in LOCKS]
    signature = {'smoke_only': smoke, 'input_text_digest': hashlib.sha256(json.dumps(texts, ensure_ascii=True, sort_keys=True).encode()).hexdigest(),
                 'input_provenance': provenance, 'file_sha256': {p: sha256(ROOT / p) for p in paths},
                 'python_version': platform.python_version(), 'tokenizers_version': tokenizers.__version__, 'pyarrow_version': pa.__version__,
                 'unicode_version': unicodedata.unidata_version}
    signature_path = out / 'input-manifest.json'
    if signature_path.exists() and json.loads(signature_path.read_text()) != signature:
        raise ValueError('Resume input fingerprint changed; start a new run')
    save(signature_path, signature)
    text_features = [features(t['text']) for t in texts]
    all_rows = []
    for lock_name in LOCKS:
        lock = json.loads((ROOT / 'config' / lock_name).read_text())
        key = lock['model_key']
        shard = out / f'{key}.parquet'
        complete = out / f'{key}-complete.json'
        if shard.exists() and complete.exists():
            saved = json.loads(complete.read_text())
            if sha256(shard) != saved['sha256']:
                raise ValueError(f'Corrupt resume shard: {key}')
            rows = pq.read_table(shard).to_pylist()
            if len(rows) != expected:
                raise ValueError('Wrong resumed row count')
            log(f'Resumed verified {key}: {len(rows)} rows')
        else:
            assets = fetch_locked(lock)
            definition = json.loads((assets / 'tokenizer.json').read_text())
            if definition.get('truncation') or definition.get('padding') or definition['model'].get('dropout'):
                raise ValueError('Unexpected tokenizer truncation, padding or dropout')
            native = tokenizers.Tokenizer.from_file(str(assets / 'tokenizer.json'))
            native.no_truncation()
            native.no_padding()
            added_strings = [v['content'] for v in definition.get('added_tokens', []) if v.get('content')]
            rows = []
            for t, f in zip(texts, text_features, strict=True):
                text = t['text']
                content = native.encode(text, add_special_tokens=False)
                with_special = native.encode(text, add_special_tokens=True)
                count = len(content.ids)
                normalized = native.normalizer.normalize_str(text) if native.normalizer is not None else text
                pre_count = len(native.pre_tokenizer.pre_tokenize_str(normalized)) if native.pre_tokenizer is not None else None
                prediction = frozen_estimator.count_tokens(text, key)
                old = math.ceil(f['utf16_units'] / 3.5)
                row = {k: v for k, v in t.items() if k != 'text'}
                row.update(f)
                row.update(model_key=key, tokenizer_revision=lock['revision'], token_count=count,
                           with_special_token_count=len(with_special.ids), added_special_token_delta=len(with_special.ids)-count,
                           normalized_characters=len(normalized), pre_token_count_after_normalization=pre_count,
                           added_token_literal_present=any(s in text for s in added_strings),
                           estimate=prediction, old_estimate=old,
                           error_percent=100 * (prediction-count)/count if count else None,
                           old_error_percent=100 * (old-count)/count if count else None)
                rows.append(row)
            del native
            temp = shard.with_suffix('.parquet.tmp')
            pq.write_table(pa.Table.from_pylist(rows), temp, compression='zstd')
            temp.replace(shard)
            save(complete, {'model_key': key, 'rows': len(rows), 'sha256': sha256(shard)})
            log(f'Measured {key}: {len(rows)} rows')
        all_rows.extend(rows)
        save(out / 'progress.json', {'rows_completed': len(all_rows), 'rows_expected': expected * len(LOCKS), 'smoke_only': smoke})
    expected_rows = expected * 5
    if len(all_rows) != expected_rows or len({(r['model_key'], r['language'], r['sentence_id']) for r in all_rows}) != expected_rows:
        raise ValueError('Missing or duplicate measurement rows')
    for row in all_rows:
        if sum(row['class_' + c] for c in CLASSES) != row['characters']:
            raise ValueError('Class-count sum disagrees with Unicode length')
        if row['token_count'] <= 0 or row['added_special_token_delta'] < 0:
            raise ValueError('Unexpected empty content or negative special-token delta')
    validation = {'rows': len(all_rows), 'unique_keys': expected_rows, 'source_texts': len(texts), 'published_fixture_overlap': overlap,
                  'smoke_only': smoke, 'raw_text_saved_in_table': False, 'devtest_accessed': False,
                  'class_sums_match': True, 'estimator_weights_unchanged': sha256(ROOT / 'config/localmind-profiles.json') == signature['file_sha256']['config/localmind-profiles.json']}
    if smoke:
        prior = json.loads((ROOT / 'results/2026-10-07-all-profiles/run-01/summary.json').read_text())
        prior_rows = { (key, r['name']): r for key in prior['profiles'] for r in json.loads((ROOT / f'results/2026-10-07-all-profiles/run-01/{key}/comparison.json').read_text()) }
        for row in all_rows:
            ref = prior_rows[(row['model_key'], row['sentence_id'])]
            if row['token_count'] != ref['python_count'] or row['estimate'] != ref['python_estimate']:
                raise ValueError('Smoke counts disagree with phase 0')
        validation['phase0_count_estimate_agreement'] = expected_rows
    temp = out / 'ground-truth.parquet.tmp'
    pq.write_table(pa.Table.from_pylist(all_rows), temp, compression='zstd')
    temp.replace(out / 'ground-truth.parquet')
    if pq.read_table(out / 'ground-truth.parquet').to_pylist() != all_rows:
        raise ValueError('Parquet round-trip mismatch')
    validation['parquet_round_trip'] = True
    save(out / 'validation.json', validation)
    write_report(out, all_rows, smoke)
    save(out / 'run.json', {'completed_utc': datetime.now(timezone.utc).isoformat(), 'smoke_only': smoke,
         'rows': len(all_rows), 'input_manifest_sha256': sha256(signature_path), 'ground_truth_sha256': sha256(out / 'ground-truth.parquet'),
         'special_tokens_added_for_content_counts': False, 'pretokenizer_diagnostic_note': 'Normalizer then explicit pre-tokenizer; added-token extraction is not emulated.',
         'no_fitting': True, 'no_model_inference': True, 'platform': platform.platform()})
    log(f"{'SMOKE ONLY' if smoke else 'PILOT'}: saved and validated {len(all_rows)} rows; no weights fitted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / 'results'):
        parser.error('Output must be inside results/')
    out.mkdir(parents=True, exist_ok=args.resume)
    state = {'status': 'running', 'started_utc': datetime.now(timezone.utc).isoformat(), 'command': sys.argv, 'smoke_only': args.smoke}
    save(out / 'status.json', state)
    code = 0
    with (out / 'terminal-output.txt').open('a', buffering=1) as stream:
        def log(message):
            print(message, flush=True)
            print(message, file=stream, flush=True)
        try:
            run(out, args.smoke, log)
        except Exception:
            log(traceback.format_exc())
            code = 1
        log(f'Exit code: {code}')
    state.update(status='complete' if code == 0 else 'failed', exit_code=code, completed_utc=datetime.now(timezone.utc).isoformat())
    save(out / 'status.json', state)
    return code


if __name__ == '__main__':
    sys.exit(main())
