"""Check observed V3/R1 agreement and separately verify marker probes."""
import argparse
import json
from pathlib import Path
from tokenizers import Tokenizer
from prepare_published_inputs import ROOT, sha, text_sha


def main(base):
    plan = json.loads((ROOT/'config/deepseek-extension-v1.json').read_text())
    for path, digest in plan['files_sha256'].items():
        assert sha(ROOT/path) == digest, path
    probes = json.loads((ROOT/plan['probes']).read_text())['inputs']
    result = []
    for model in plan['new_models']:
        lock = json.loads((ROOT/'config'/f'{model}-tokenizer.lock.json').read_text())
        for a in lock['assets']:
            assert sha(ROOT/lock['cache_directory']/a['filename']) == a['sha256']
        tok = Tokenizer.from_file(str(ROOT/lock['cache_directory']/'tokenizer.json'))
        js = {r['id']: r for r in json.loads((base/'js-01'/f'{model}-probes.json').read_text())}
        assert set(js) == {f['id'] for f in probes}
        for f in probes:
            ids = tok.encode(f['text'], add_special_tokens=False).ids
            row = {'id': f['id'], 'text_sha256': text_sha(f['text']), 'token_count': len(ids),
                   'id_sequence_sha256': text_sha(','.join(map(str, ids)))}
            assert row == js[f['id']]
            row.update(model_key=model, decode_exact=tok.decode(ids, skip_special_tokens=False) == f['text'])
            result.append(row)
    rows = json.loads((base/'run-01/measurements.json').read_text())
    tables = {m: {r['id']: r for r in rows if r['model_key'] == m} for m in plan['new_models']}
    a, b = [tables[m] for m in plan['new_models']]
    assert set(a) == set(b) and len(a) == 140
    report = {'status': 'passed', 'corpus_inputs': 140,
              'v3_r1_matching_corpus_id_hashes': sum(a[i]['id_sequence_sha256'] == b[i]['id_sequence_sha256'] for i in a),
              'v3_r1_matching_corpus_counts': sum(a[i]['token_count'] == b[i]['token_count'] for i in a),
              'marker_probe_python_js_matches': len(result), 'probe_rows': result,
              'script_sha256': sha(Path(__file__)),
              'limits': 'Probes target known added-token differences and are excluded from primary results. Content parity is not chat-template equivalence.'}
    out = base/'identity-checks.json'; assert not out.exists()
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'probe_rows'}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--base', type=Path, required=True)
    main(p.parse_args().base)
