"""Measure frozen published inputs, publishing counts/hashes only; resume per profile."""
import argparse
import json
import platform
from pathlib import Path
import tokenizers
from tokenizers import Tokenizer
from prepare_published_inputs import ROOT, sha, text_sha


def save(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2)+'\n'); tmp.replace(path)


def main(out):
    plan_path = ROOT/'config/published-text-experiment-v1.json'
    plan = json.loads(plan_path.read_text())
    for p, expected in plan['files_sha256'].items():
        assert sha(ROOT/p) == expected, p
    assert tokenizers.__version__ == plan['python_tokenizers_version']
    inputs = json.loads((ROOT/plan['private_corpus']).read_text())['inputs']
    assert sha(ROOT/plan['private_corpus']) == plan['private_corpus_sha256']
    assert len(inputs) == 140
    out.mkdir(parents=True, exist_ok=True)
    signature = {'plan_sha256': sha(plan_path), 'script_sha256': sha(Path(__file__)),
                 'corpus_sha256': plan['private_corpus_sha256'],
                 'python_version': platform.python_version(), 'tokenizers_version': tokenizers.__version__}
    marker = out/'input-manifest.json'
    if marker.exists(): assert json.loads(marker.read_text()) == signature, 'Changed resume inputs'
    else: save(marker, signature)
    locks = {}
    for name, h in plan['tokenizer_locks'].items():
        p = ROOT/'config'/name; assert sha(p) == h
        lock = json.loads(p.read_text()); locks[lock['model_key']] = lock
    all_rows, inventory = [], []
    for model in plan['models']:
        lock = locks[model]; cache = ROOT/lock['cache_directory']
        for a in lock['assets']: assert sha(cache/a['filename']) == a['sha256']
        native = Tokenizer.from_file(str(cache/'tokenizer.json'))
        definition = json.loads(native.to_str())
        assert not definition.get('truncation') and not definition.get('padding')
        assert not definition['model'].get('dropout')
        native.no_truncation(); native.no_padding()
        derived = None
        if 'derived_asset' in lock:
            p = cache/lock['derived_asset']['filename']; assert sha(p) == lock['derived_asset']['sha256']
            derived = Tokenizer.from_file(str(p))
        unk = definition['model'].get('unk_id')
        if unk is None and definition['model'].get('unk_token') is not None:
            unk = native.token_to_id(definition['model']['unk_token'])
        inventory.append({'model_key': model, 'algorithm': type(native.model).__name__,
                          'revision': lock['revision'], 'unknown_id': unk,
                          'base_vocab_entries': native.get_vocab_size(False),
                          'effective_vocab_entries': native.get_vocab_size(True)})
        shard = out/(model+'.json')
        if shard.exists():
            old = json.loads(shard.read_text()); assert old['signature'] == signature
            assert old['model_key'] == model and len(old['rows']) == 140
            assert old['rows_sha256'] == text_sha(json.dumps(old['rows'], sort_keys=True))
            all_rows += old['rows']; print('Resumed', model, flush=True); continue
        rows = []
        for f in inputs:
            text = f['text']; assert text_sha(text) == f['text_sha256']
            ids = native.encode(text, add_special_tokens=False).ids
            special = native.encode(text, add_special_tokens=True).ids
            if derived is not None: assert ids == derived.encode(text, add_special_tokens=False).ids
            normalized = native.normalizer.normalize_str(text) if native.normalizer else text
            decoded = native.decode(ids, skip_special_tokens=False)
            r = {k:v for k,v in f.items() if k != 'text'}
            r.update(model_key=model, algorithm=type(native.model).__name__,
                tokenizer_revision=lock['revision'], token_count=len(ids),
                with_special_count=len(special), special_delta=len(special)-len(ids),
                unknown_tokens=ids.count(unk) if unk is not None else 0,
                normalized_characters=len(normalized), normalization_changed=normalized != text,
                decode_exact=decoded == text,
                decode_equal_without_whitespace=''.join(decoded.split()) == ''.join(text.split()),
                decoded_sha256=text_sha(decoded), id_sequence_sha256=text_sha(','.join(map(str, ids))))
            assert r['token_count'] > 0
            rows.append(r)
        save(shard, {'signature': signature, 'model_key': model, 'rows': rows,
                     'rows_sha256': text_sha(json.dumps(rows, sort_keys=True)),
                     'original_vs_serialized_parity_inputs': 140 if derived else None})
        all_rows += rows
        originals = [r for r in rows if r['role'] == 'original']
        print(f"{model}: 140 inputs; originals: {sum(r['unknown_tokens']>0 for r in originals)}/100 with unknown IDs, {sum(not r['decode_exact'] for r in originals)}/100 decode mismatches.", flush=True)
    assert len(all_rows) == 840 and len({(r['model_key'],r['id']) for r in all_rows}) == 840
    save(out/'measurements.json', all_rows); save(out/'inventory.json', inventory)
    save(out/'measurement-validation.json', {'rows': 840, 'original_rows': 600,
         'variant_rows': 240, 'unigram_original_serialized_parity': 140,
         'no_truncation_or_padding': True, 'raw_text_or_ids_published': False})


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    main(p.parse_args().output)
