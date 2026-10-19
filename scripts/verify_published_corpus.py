#!/usr/bin/env python3
"""Independent byte/metadata and pairwise-duplicate audit; no tokenizer imports.

Does not import the collector or use its feature or duplicate functions.
Selection order is checked separately by an offline collector replay.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import itertools
import json
from pathlib import Path
import re
import statistics
import unicodedata


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(items):
    assert len({k for k, _ in items}) == len(items), 'duplicate JSON keys'
    return dict(items)


def invalid_constant(value):
    raise AssertionError('Nonstandard JSON constant: ' + value)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--reviews', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    cfg_path = Path('config/published-text-sources-v1.json')
    cfg = json.loads(cfg_path.read_text())
    manifest = json.loads(args.manifest.read_text())
    reviews = json.loads(args.reviews.read_text())
    assert manifest['status'] == 'reviewed_pending_independent_validation'
    assert manifest['config_sha256'] == sha(cfg_path.read_bytes())
    assert manifest['reviews_sha256'] == sha(args.reviews.read_bytes())
    assert manifest['collector_sha256'] == sha(Path('scripts/collect_published_text.py').read_bytes())
    assert sha(Path(cfg['protocol']).read_bytes()) == cfg['protocol_sha256']
    inventory_path = Path(cfg['candidate_inventory'])
    metadata_check = json.loads(Path('results/2026-10-18-source-design/metadata-check.json').read_text())
    assert sha(inventory_path.read_bytes()) == metadata_check['output_sha256']
    candidates = {(r['repo'], r['revision'], r['path'], r['stratum']): r
                  for r in json.loads(inventory_path.read_text())['candidates']}
    sources = {s['repo']: s for s in cfg['sources']}
    samples = manifest['samples']
    counts = Counter(r['stratum'] for r in samples)
    categories = Counter(r['category'] for r in samples)
    assert counts == manifest['counts']
    assert len(samples) == 100 and all(n == 10 for n in counts.values())
    assert len(categories) == 5 and all(n == 20 for n in categories.values())
    assert not manifest['shortfalls']
    assert len({r['sample_id'] for r in samples}) == 100
    assert len({(r['repo'], r['path']) for r in samples}) == 100
    mixed = [r for r in samples if r['category'] == 'mixed']
    assert len({'/'.join(r['path'].split('/')[2:]) for r in mixed}) == len(mixed) == 20
    screens, summaries, notices, source_bytes, selected_bytes = [], {}, set(), 0, 0
    lengths = defaultdict(list)
    for r in samples:
        key = (r['repo'], r['revision'], r['path'], r['stratum'])
        original = candidates[key]
        for k, v in original.items():
            assert r[k] == v, (r['sample_id'], k)
        raw_path = Path('data/raw/published-text-v1') / r['repo'] / r['revision'] / r['path']
        raw = raw_path.read_bytes()
        assert len(raw) == r['byte_size']
        assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == r['git_blob_sha']
        assert sha(raw) == r['full_file_sha256']
        start, end = r['start_byte'], r['end_byte']
        assert 0 <= start < end <= len(raw)
        segment = raw[start:end]
        text = segment.decode('utf-8')
        assert sha(segment) == r['sample_sha256']
        actual = {'codepoints': len(text), 'utf8_bytes': len(segment),
                  'utf16_units': len(text.encode('utf-16-le')) // 2,
                  'whitespace_words': len(text.split()),
                  'ascii_letters': len(re.findall('[A-Za-z]', text)),
                  'devanagari_letters': sum(c.isalpha() and 0x900 <= ord(c) <= 0x97f for c in text),
                  'tamil_letters': sum(c.isalpha() and 0xb80 <= ord(c) <= 0xbff for c in text)}
        assert actual == r['lengths_and_scripts'], r['sample_id']
        is_passage = r['category'] in ('prose', 'mixed')
        assert 200 <= len(text) <= (2000 if is_passage else 12000)
        if is_passage:
            # Independently find maximal nonblank line runs with byte offsets.
            offset, begin, runs = 0, None, []
            for line in raw.splitlines(keepends=True):
                blank = not line.decode('utf-8').strip()
                if not blank and begin is None:
                    begin = offset
                if blank and begin is not None:
                    runs.append((begin, offset))
                    begin = None
                offset += len(line)
            if begin is not None:
                runs.append((begin, offset))
            assert (start, end) in runs, 'Not an intact maximal paragraph'
        else:
            assert (start, end) == (0, len(raw))
        if r['category'] == 'mixed':
            script = 'devanagari_letters' if r['stratum'] == 'hindi_english' else 'tamil_letters'
            assert actual[script] >= 20 and actual['ascii_letters'] >= 20
            visible = re.sub(r'\]\([^)]*\)', ']', text)
            visible = re.sub(r'https?://[^\s<>]+|<[^>]*>', '', visible)
            assert re.search('[A-Za-z]', visible), 'No visible English/identifier candidate'
            assert 'Co-op Translator' not in text
        if r['category'] == 'json':
            obj = json.loads(text, object_pairs_hook=unique_object,
                             parse_float=Decimal, parse_constant=invalid_constant)
            assert isinstance(obj, dict)
        assert r['file_review'] == reviews['files'][r['file_id']]
        assert r['sample_review'] == reviews['samples'][r['sample_id']]
        assert r['file_review']['decision'] == r['sample_review']['decision'] == 'accept'
        assert r['file_review']['reason'] and r['sample_review']['reason']
        src = sources[r['repo']]
        assert src['license_path'] in [n['path'] for n in r['terms_evidence']]
        for n in r['terms_evidence']:
            b = (Path('data/raw/published-text-v1') / r['repo'] / r['revision'] / n['path']).read_bytes()
            assert sha(b) == n['sha256']
            if n['path'] == src['license_path']:
                assert sha(b) == src['license_sha256']
            notices.add((r['repo'], n['path']))
        normal = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()
        screen = set(zip(*(normal[i:] for i in range(5))))
        screens.append((r['sample_id'], normal, screen))
        lengths[r['category']].append(len(text))
        source_bytes += len(raw)
        selected_bytes += len(segment)
    maximum, closest, pairs = -1, None, 0
    for a, b in itertools.combinations(screens, 2):
        assert a[1] != b[1]
        similarity = len(a[2].intersection(b[2])) / len(a[2].union(b[2]))
        assert similarity < .90, (a[0], b[0], similarity)
        if similarity > maximum:
            maximum, closest = similarity, [a[0], b[0]]
        pairs += 1
    for category in cfg['category_order']:
        values = lengths[category]
        summaries[category] = {'n': len(values), 'min_codepoints': min(values),
            'median_codepoints': statistics.median(values), 'max_codepoints': max(values),
            'length_bands': {f'{lo}-{hi}': sum(lo <= n <= hi for n in values)
                             for lo, hi in cfg['length_bands_inclusive']}}
    output = {'status': 'passed_independent_corpus_integrity_checks',
        'manifest_sha256': sha(args.manifest.read_bytes()),
        'reviews_sha256': sha(args.reviews.read_bytes()),
        'verifier_sha256': sha(Path(__file__).read_bytes()),
        'sample_count': 100, 'stratum_counts': dict(counts), 'category_summaries': summaries,
        'distinct_translation_lessons': len(mixed), 'unique_notice_files': len(notices),
        'full_source_bytes_for_selected_files': source_bytes, 'selected_input_bytes': selected_bytes,
        'duplicate_pairs_checked': pairs, 'max_jaccard': maximum, 'closest_sample_ids': closest,
        'checks': ['Git blob/SHA256 identity and inventory membership',
                   'Original UTF-8 boundaries and whole-file/paragraph rules',
                   'Lengths, script thresholds, strict JSON and review labels',
                   'Notice hashes and root-license coverage references',
                   'All 4950 unordered sample pairs below duplicate threshold',
                   '100 distinct source files; 20 distinct translated lesson families'],
        'limitations': ['Independent calculations by a separate script, not independent human review',
                       'Semantic eligibility and terms applicability depend on recorded Codex review',
                       'No translation quality certification or claim of representative web sampling'],
        'tokenization_performed': False}
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
