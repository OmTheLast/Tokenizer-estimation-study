"""Reproduce the post-measurement BOM diagnostic without publishing source text."""
import json
from pathlib import Path
from tokenizers import Tokenizer
from prepare_published_inputs import ROOT, sha


def main():
    base = ROOT/'results/2026-10-19-published-experiment'
    plan = json.loads((ROOT/'config/published-text-experiment-v1.json').read_text())
    assert sha(ROOT/plan['private_corpus']) == plan['private_corpus_sha256']
    fixtures = json.loads((ROOT/plan['private_corpus']).read_text())['inputs']
    by_id = {f['id']: f for f in fixtures}
    rows = json.loads((base/'run-01/measurements.json').read_text())
    xlm = [r for r in rows if r['model_key'] == 'xlm-roberta-base']
    originals = [r for r in xlm if r['role'] == 'original']
    remaining = [r for r in originals if not r['decode_equal_without_whitespace']]
    assert len(remaining) == 1
    r = remaining[0]; text = by_id[r['id']]['text']
    lock = json.loads((ROOT/'config/xlm-roberta-base-tokenizer.lock.json').read_text())
    for a in lock['assets']:
        assert sha(ROOT/lock['cache_directory']/a['filename']) == a['sha256']
    tok = Tokenizer.from_file(str(ROOT/lock['cache_directory']/'tokenizer.json'))
    decoded = tok.decode(tok.encode(text, add_special_tokens=False).ids, skip_special_tokens=False)
    record = {
        'xlm_original_decode_mismatches': sum(not r['decode_exact'] for r in originals),
        'original_whitespace_only_mismatches': sum(not r['decode_exact'] and r['decode_equal_without_whitespace'] for r in originals),
        'remaining_original_case': {
            'input_id': r['id'], 'starts_with_utf8_bom': text.startswith('\ufeff'),
            'removing_initial_bom_and_whitespace_from_input_matches_decoded_without_whitespace':
                ''.join(text.removeprefix('\ufeff').split()) == ''.join(decoded.split())},
        'xlm_json_compact_exact': sum(r['decode_exact'] for r in xlm if r['format'] == 'json_compact'),
        'xlm_json_pretty_exact': sum(r['decode_exact'] for r in xlm if r['format'] == 'json_pretty'),
        'all_input_unknown_token_rows': sum(r['unknown_tokens'] > 0 for r in rows),
        'all_originals_end_in_newline': all(f['text'].endswith('\n') for f in fixtures if f['role'] == 'original'),
        'semantic_equivalence_claimed': False,
    }
    # Preserve the earlier exploratory diagnostic; check that this saved script reproduces it.
    assert record == json.loads((base/'reconstruction-diagnostics.json').read_text())
    print(json.dumps({'status': 'passed', 'diagnostic_reproduced': True, 'script_sha256': sha(Path(__file__))}, indent=2))


if __name__ == '__main__':
    main()
