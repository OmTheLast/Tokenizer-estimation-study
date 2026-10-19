"""Reconstruct frozen original inputs and exact-value JSON variants, without tokenization."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def exact_loads(text):
    def pairs(items):
        if len({k for k, _ in items}) != len(items):
            raise ValueError('Duplicate key')
        return dict(items)
    def invalid(x):
        raise ValueError('Nonstandard number')
    return json.loads(text, parse_int=Decimal, parse_float=Decimal,
                      parse_constant=invalid, object_pairs_hook=pairs)


def exact_dumps(value, pretty=False, level=0):
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError('Non-finite Decimal')
        return str(value)
    if isinstance(value, (list, dict)):
        opening, closing = ('[', ']') if isinstance(value, list) else ('{', '}')
        items = ([exact_dumps(v, pretty, level+1) for v in value] if isinstance(value, list)
                 else [exact_dumps(k) + (': ' if pretty else ':') + exact_dumps(v, pretty, level+1)
                       for k, v in value.items()])
        if not items:
            return opening + closing
        if not pretty:
            return opening + ','.join(items) + closing
        pad = '  ' * (level+1)
        return opening + '\n' + pad + (',\n' + pad).join(items) + '\n' + '  '*level + closing
    raise TypeError(type(value).__name__)


def fingerprint(value):
    # Includes ordered keys, numeric precision/exponent/sign, and scalar types.
    if isinstance(value, Decimal):
        return ('number', value.as_tuple())
    if isinstance(value, dict):
        return ('object', [(k, fingerprint(v)) for k, v in value.items()])
    if isinstance(value, list):
        return ('array', [fingerprint(v) for v in value])
    return (type(value).__name__, value)


def prepare(public_out):
    lock_path = ROOT/'config/published-text-corpus-v1.lock.json'
    lock = json.loads(lock_path.read_text())
    for path, expected in lock['files_sha256'].items():
        assert sha(ROOT/path) == expected, path
    source = json.loads((ROOT/lock['manifest']).read_text())
    inputs, json_checks = [], []
    for row in source['samples']:
        raw = (ROOT/lock['raw_root']/row['repo']/row['revision']/row['path']).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == row['git_blob_sha']
        assert hashlib.sha256(raw).hexdigest() == row['full_file_sha256']
        text = raw[row['start_byte']:row['end_byte']].decode('utf-8')
        assert text_sha(text) == row['sample_sha256']
        variants = [('original', text)]
        if row['category'] == 'json':
            value = exact_loads(text)
            assert isinstance(value, dict)
            compact, pretty = exact_dumps(value), exact_dumps(value, True)
            for v in (compact, pretty):
                assert fingerprint(exact_loads(v)) == fingerprint(value)
                assert not v.endswith('\n')
            variants += [('json_compact', compact), ('json_pretty', pretty)]
            json_checks.append({'sample_id': row['sample_id'], 'ordered_value_precision_sign_preserved': True})
        for form, t in variants:
            inputs.append({'id': row['sample_id']+'/'+form, 'sample_id': row['sample_id'],
                'category': row['category'], 'stratum': row['stratum'], 'format': form,
                'role': 'original' if form == 'original' else 'json_variant',
                'text_sha256': text_sha(t), 'characters': len(t),
                'utf8_bytes': len(t.encode()), 'text': t})
    assert len(inputs) == 140 and len(json_checks) == 20
    public_out.mkdir(parents=True, exist_ok=False)
    local = ROOT/'data/processed/published-text-inputs-v1.json'
    local.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps({'inputs': inputs}, ensure_ascii=False, indent=2)+'\n'
    if local.exists():
        assert local.read_bytes() == content.encode('utf-8'), 'Prepared input drift'
    else:
        tmp = local.with_suffix('.tmp'); tmp.write_text(content); tmp.replace(local)
    metadata = {'inputs': [{k:v for k,v in r.items() if k != 'text'} for r in inputs],
        'prepared_corpus_path': str(local.relative_to(ROOT)), 'prepared_corpus_sha256': sha(local),
        'source_lock_sha256': sha(lock_path), 'builder_sha256': sha(Path(__file__)),
        'original_inputs': 100, 'derived_json_inputs': 40, 'json_value_checks': json_checks,
        'tokenization_performed': False}
    (public_out/'input-manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print('Verified corpus lock; 100 originals + 40 JSON variants prepared. All 20 JSON value/order/precision checks passed.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    prepare(p.parse_args().output)
