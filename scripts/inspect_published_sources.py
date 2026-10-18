#!/usr/bin/env python3
"""Reproduce path-only inventories from pinned Git trees; never tokenize text.

Run from project root. --fetch downloads only commit/tree metadata, root licenses and
translation README evidence through curl with TLS verification enabled.
Default reads the existing ignored cache. Refuses to overwrite evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f'Refusing to overwrite {args.output}')
    config_path = Path('config/published-text-sources-v1.json')
    cfg = json.loads(config_path.read_text())
    for name in ('protocol', 'tokenizer_config'):
        assert sha256(Path(cfg[name]).read_bytes()) == cfg[name + '_sha256'], name
    cache = Path('.cache/natural-source-planning')
    cache.mkdir(parents=True, exist_ok=True)
    excluded = set(cfg['excluded_path_components'])
    rows, summaries = [], []
    for src in cfg['sources']:
        repo, rev = src['repo'], src['revision']
        assert re.fullmatch('[0-9a-f]{40}', rev)
        key = repo.replace('/', '__')
        head_path = cache / (key + '-head.json')
        tree_path = cache / (key + '-tree.json')
        license_path = cache / (key + '-license.txt')
        requests = [(head_path, src['commit_api_url']), (tree_path, src['tree_api_url']),
                    (license_path, f'https://raw.githubusercontent.com/{repo}/{rev}/{src["license_path"]}')]
        if 'translation_provenance' in src:
            requests.append((cache / (key + '-readme.md'),
                             f'https://raw.githubusercontent.com/{repo}/{rev}/README.md'))
        if args.fetch:
            for dest, url in requests:
                data = subprocess.check_output(['curl', '--fail', '--silent',
                    '--show-error', '--location', '--retry', '2', '--max-time', '60', url])
                temp = dest.with_suffix(dest.suffix + '.tmp')
                temp.write_bytes(data)
                temp.replace(dest)
        tree = json.loads(tree_path.read_bytes())
        head = json.loads(head_path.read_bytes())
        assert head['sha'] == rev, repo
        assert head['commit']['tree']['sha'] == src['git_tree_sha'], repo
        assert tree['sha'] == src['git_tree_sha'], repo
        assert tree.get('truncated') is False, repo
        assert sha256(license_path.read_bytes()) == src['license_sha256'], repo
        if 'translation_provenance' in src:
            assert sha256((cache / (key + '-readme.md')).read_bytes()) == src['translation_provenance']['readme_sha256']
        for pool in src['pools']:
            candidates = []
            for blob in tree['tree']:
                path = blob['path']
                if blob['type'] != 'blob' or blob.get('mode') not in ('100644', '100755'):
                    continue
                if not re.fullmatch(pool['path_regex'], path):
                    continue
                if excluded.intersection(x.lower() for x in path.split('/')):
                    continue
                rank = sha256(json.dumps([cfg['seed'], repo, rev, path],
                    ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
                candidates.append({'repo': repo, 'revision': rev,
                    'category': pool['category'], 'stratum': pool['stratum'],
                    'path': path, 'git_blob_sha': blob['sha'],
                    'byte_size': blob['size'], 'file_rank': rank})
            candidates.sort(key=lambda r: (r['file_rank'], r['path']))
            rows.extend(candidates)
            summaries.append({'stratum': pool['stratum'], 'category': pool['category'],
                'repo': repo, 'target': pool['target'],
                'path_candidate_count': len(candidates)})
    for category in cfg['category_order']:
        assert sum(r['target'] for r in summaries if r['category'] == category) == cfg['target_per_category']
    assert sum(r['target'] for r in summaries) == cfg['target_original_samples']
    assert len({(r['stratum'], r['path']) for r in rows}) == len(rows)
    output = {'status': 'metadata_inventory_only_not_selected_samples',
              'config_sha256': sha256(config_path.read_bytes()),
              'script_sha256': sha256(Path(__file__).read_bytes()),
              'summaries': summaries, 'candidates': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        f.write(json.dumps(output, indent=2) + '\n')
    print(json.dumps({'status': output['status'], 'path_candidates': len(rows),
                      'summaries': summaries, 'output_sha256': sha256(args.output.read_bytes())}, indent=2))


if __name__ == '__main__':
    main()
