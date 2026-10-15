"""Run from the project root with its .venv; verify saved pilot without network."""
import hashlib
import json
from pathlib import Path
import statistics
import pyarrow.parquet as pq

out = Path(__file__).resolve().parent
root = out.parents[2]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
manifest = json.loads((out / 'input-manifest.json').read_text())
assert all(sha(root / f) == h for f, h in manifest['file_sha256'].items())
shards = list(out.glob('*-complete.json'))
assert len(shards) == 5
for path in shards:
    saved = json.loads(path.read_text())
    assert sha(out / (saved['model_key'] + '.parquet')) == saved['sha256']
rows = pq.read_table(out / 'ground-truth.parquet').to_pylist()
assert len(rows) == 9000
assert len({(r['model_key'], r['language'], r['sentence_id']) for r in rows}) == 9000
assert all('text' not in r and 'ids' not in r for r in rows)
for r in rows:
    assert abs(r['error_percent'] - 100 * (r['estimate'] - r['token_count']) / r['token_count']) < 1e-10
stats = {}
for model in dict.fromkeys(r['model_key'] for r in rows):
    selected = [r for r in rows if r['model_key'] == model]
    worst = min(selected, key=lambda r: r['error_percent'])
    stats[model] = {
        'median_absolute_error_percent': statistics.median(abs(r['error_percent']) for r in selected),
        'old_median_absolute_error_percent': statistics.median(abs(r['old_error_percent']) for r in selected),
        'worst_under': {k: worst[k] for k in ['language', 'sentence_id', 'estimate', 'token_count', 'error_percent']},
    }
result = {'rows': 9000, 'source_config_hashes_match': True, 'five_shard_checksums_match': True,
          'error_formula_checked_all_rows': True, 'raw_text_and_ids_absent': True, 'statistics': stats}
(out / 'independent-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print('Independent checks passed: 9000 unique rows, 5 shard checksums, source/config hashes and every error calculation.')
