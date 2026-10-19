#!/usr/bin/env python3
"""Collect pinned text without executing source or loading tokenizers.

Raw bytes stay under ignored data/raw; public outputs contain metadata only.
Review decisions are supplied separately. Reruns reuse SHA-verified downloads.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import unicodedata
from urllib.parse import quote

CONFIG = Path('config/published-text-sources-v1.json')
RAW = Path('data/raw/published-text-v1')


def digest(b):
    return hashlib.sha256(b).hexdigest()


def git_blob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()


def rank(parts):
    return digest(json.dumps(parts, ensure_ascii=False, separators=(',', ':')).encode())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def strict_json(text):
    def pairs(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise ValueError('duplicate JSON key')
            obj[k] = v
        return obj
    def invalid(value):
        raise ValueError('nonstandard JSON constant')
    value = json.loads(text, object_pairs_hook=pairs, parse_float=Decimal,
                       parse_constant=invalid)
    if not isinstance(value, dict):
        raise ValueError('JSON root must be object')
    return value


def features(text):
    return {'codepoints': len(text), 'utf8_bytes': len(text.encode('utf-8')),
            'utf16_units': len(text.encode('utf-16-le')) // 2,
            'whitespace_words': len(text.split()),
            'ascii_letters': sum(c.isascii() and c.isalpha() for c in text),
            'devanagari_letters': sum('\u0900' <= c <= '\u097f' and c.isalpha() for c in text),
            'tamil_letters': sum('\u0b80' <= c <= '\u0bff' and c.isalpha() for c in text)}


def screening(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def grams(text):
    return {text[i:i+5] for i in range(max(0, len(text)-4))}


def paragraphs(raw, rst=False):
    """Maximal nonblank blocks with original offsets and context exclusions.

    Keep line terminators belonging to the last nonblank line. Blank separators
    are excluded. Fences/frontmatter/RST directive bodies are tracked across gaps.
    """
    lines = raw.splitlines(keepends=True)
    blocks, current = [], []
    offset, fence, frontmatter = 0, None, False
    rst_indent, literal_pending = None, False
    for i, line in enumerate(lines):
        text = line.decode('utf-8').rstrip('\r\n')
        stripped = text.strip()
        indent = len(text) - len(text.lstrip())
        reason = None
        if i == 0 and stripped == '---' and not rst:
            frontmatter = True
            reason = 'frontmatter'
        elif frontmatter:
            reason = 'frontmatter'
            if stripped in ('---', '...'):
                frontmatter = False
        elif fence:
            reason = 'fenced_code'
            if re.fullmatch(re.escape(fence[0]) + '{' + str(fence[1]) + r',}\s*', stripped):
                fence = None
        else:
            marker = re.match(r'^ {0,3}(`{3,}|~{3,})', text)
            if marker and not rst:
                fence = (marker[1][0], len(marker[1]))
                reason = 'fenced_code'
            elif rst:
                if rst_indent is not None and stripped and indent <= rst_indent:
                    rst_indent = None
                if literal_pending and stripped:
                    if indent:
                        rst_indent = 0
                    literal_pending = False
                if re.match(r'^\s*\.\.\s', text):
                    rst_indent = indent
                    reason = 'rst_directive_or_comment'
                elif rst_indent is not None and stripped:
                    reason = 'rst_directive_or_literal_body'
                if not reason and stripped.endswith('::'):
                    literal_pending = True
        if stripped:
            if reason is None and indent:
                reason = 'indented_block'
            current.append((offset, offset + len(line), text, reason))
        elif current:
            blocks.append(current)
            current = []
        offset += len(line)
    if current:
        blocks.append(current)
    output = []
    for block in blocks:
        start, end = block[0][0], block[-1][1]
        text = raw[start:end].decode('utf-8')
        reason = next((x[3] for x in block if x[3]), None)
        contents = [x[2].strip() for x in block]
        if reason is None:
            if any(re.match(r'^(#{1,6}\s|[=-]{3,}$|[~^*]{3,}$)', x) for x in contents):
                reason = 'heading'
            elif all(re.match(r'^(?:[-*+]\s|\d+[.)]\s|\|)', x) for x in contents):
                reason = 'list_or_table'
            elif any(x.startswith('|') or re.match(r'^\+[-=]+\+', x) for x in contents):
                reason = 'table'
            elif contents[0].startswith(('>', '<', '[![')) or re.match(r'^\[[^]]+\]:', contents[0]):
                reason = 'quote_html_or_reference_block'
            elif re.search(r'(?:\*\*)?(?:disclaimer|translation disclaimer)(?:\*\*)?\s*:', text, re.I):
                reason = 'disclaimer'
        output.append((start, end, reason))
    return output


class Collector:
    def __init__(self, cfg, reviews, fetch, out):
        self.cfg, self.reviews, self.fetch, self.out = cfg, reviews, fetch, out
        self.sources = {s['repo']: s for s in cfg['sources']}
        self.trees = {}
        for repo, src in self.sources.items():
            cache = Path('.cache/natural-source-planning') / (repo.replace('/', '__') + '-tree.json')
            tree = json.loads(cache.read_text())
            assert tree['sha'] == src['git_tree_sha'] and not tree['truncated']
            self.trees[repo] = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
        self.selected, self.seen, self.families = [], [], set()
        self.events = (out / 'decisions.jsonl').open('w')

    def event(self, **item):
        self.events.write(json.dumps(item, ensure_ascii=False) + '\n')
        self.events.flush()

    def download(self, repo, path):
        src = self.sources[repo]
        dest = RAW / repo / src['revision'] / path
        expected = self.trees[repo][path]['sha']
        if not dest.exists():
            if not self.fetch:
                raise RuntimeError(f'Missing cached file: {dest}; rerun with --fetch')
            url = f'https://raw.githubusercontent.com/{repo}/{src["revision"]}/{quote(path, safe="/")}'
            raw = subprocess.check_output(['curl', '--fail', '--silent', '--show-error',
                '--location', '--retry', '2', '--max-time', '60', url])
            assert git_blob(raw) == expected, f'Blob mismatch: {repo}/{path}'
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(dest.suffix + '.download')
            tmp.write_bytes(raw)
            tmp.replace(dest)
        raw = dest.read_bytes()
        assert git_blob(raw) == expected, f'Cache mismatch: {repo}/{path}'
        return raw

    def terms(self, repo, path):
        src = self.sources[repo]
        ancestors = set(PurePosixPath(path).parents)
        names = []
        for p in self.trees[repo]:
            pp = PurePosixPath(p)
            if pp.parent in ancestors and re.search(r'license|licence|copying|copyright|notice', pp.name, re.I):
                # Select notice documents, not executable files that mention licenses.
                if pp.suffix.lower() in ('', '.md', '.rst', '.txt'):
                    names.append(p)
        refs = []
        for p in sorted(set(names + [src['license_path']])):
            raw = self.download(repo, p)
            if p == src['license_path']:
                assert digest(raw) == src['license_sha256']
            refs.append({'path': p, 'sha256': digest(raw),
                'url': f'https://github.com/{repo}/blob/{src["revision"]}/{quote(p, safe="/")}'})
        return refs

    def try_file(self, row):
        repo, path = row['repo'], row['path']
        family = (repo + '/' + '/'.join(path.split('/')[2:])) if row['category'] == 'mixed' else repo + '/' + path
        file_id = rank([repo, row['revision'], path])[:24]
        if family in self.families:
            self.event(file_id=file_id, path=path, stratum=row['stratum'], decision='reject', reason='known_family_already_selected')
            return False
        raw = self.download(repo, path)
        base = {'file_id': file_id, 'repo': repo, 'path': path, 'stratum': row['stratum'], 'full_file_sha256': digest(raw)}
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            self.event(**base, decision='reject', reason='invalid_utf8')
            return False
        if re.search(r'(?:auto[- ]?generated|generated (?:by|from)|do not edit)', text[:2500], re.I) and row['category'] != 'mixed':
            self.event(**base, decision='reject', reason='generated_header')
            return False
        if '.min.' in path.lower():
            self.event(**base, decision='reject', reason='minified_path')
            return False
        file_review = self.reviews.get('files', {}).get(file_id, {})
        if file_review.get('decision') == 'reject':
            self.event(**base, decision='reject', reason='review:' + file_review['reason'])
            return False
        passage = row['category'] in ('prose', 'mixed')
        if not passage and not 200 <= len(text) <= 12000:
            self.event(**base, decision='reject', reason='whole_file_length', codepoints=len(text))
            return False
        if row['category'] == 'json':
            try:
                strict_json(text)
            except (ValueError, RecursionError):
                self.event(**base, decision='reject', reason='not_strict_json_object')
                return False
        spans = paragraphs(raw, path.endswith('.rst')) if passage else [(0, len(raw), None)]
        spans.sort(key=lambda x: (rank([self.cfg['seed'], repo, row['revision'], path, str(x[0]), str(x[1])]), x[0]))
        for start, end, reason in spans:
            fragment = raw[start:end]
            t = fragment.decode('utf-8')
            sid = rank([repo, row['revision'], path, str(start), str(end)])[:24]
            info = features(t)
            if reason is None and passage and not 200 <= len(t) <= 2000:
                reason = 'paragraph_length'
            if reason is None and row['category'] == 'mixed':
                target = 'devanagari_letters' if row['stratum'] == 'hindi_english' else 'tamil_letters'
                if info[target] < 20 or info['ascii_letters'] < 20:
                    reason = 'mixed_script_threshold'
            review = self.reviews.get('samples', {}).get(sid, {})
            if reason is None and review.get('decision') == 'reject':
                reason = 'review:' + review['reason']
            duplicate = None
            clean, g = screening(t), None
            if reason is None:
                g = grams(clean)
                for prior_id, prior_text, prior_grams in self.seen:
                    if clean == prior_text or len(g & prior_grams) / len(g | prior_grams) >= 0.90:
                        reason, duplicate = 'duplicate_or_near_duplicate', prior_id
                        break
            if reason:
                self.event(**base, sample_id=sid, start_byte=start, end_byte=end,
                           decision='reject', reason=reason, duplicate_of=duplicate)
                continue
            refs = self.terms(repo, path)
            item = {**row, 'sample_id': sid, 'file_id': file_id,
                'family_id': family, 'full_file_sha256': digest(raw),
                'sample_sha256': digest(fragment), 'start_byte': start, 'end_byte': end,
                'sample_rank': rank([self.cfg['seed'], repo, row['revision'], path, str(start), str(end)]) if passage else row['file_rank'],
                'lengths_and_scripts': info, 'source_url': f'https://github.com/{repo}/blob/{row["revision"]}/{quote(path, safe="/")}',
                'attribution': f'{repo} contributors; see file header and referenced notices',
                'change_notice': 'Unmodified contiguous paragraph excerpt' if passage else 'Unmodified complete source file',
                'terms_evidence': refs,
                'file_review': file_review or {'decision': 'pending'},
                'sample_review': review or {'decision': 'pending'}}
            if row['category'] == 'html':
                item['html_inline_script'] = bool(re.search(r'<script\b(?![^>]*\bsrc\s*=)[^>]*>\s*\S', t, re.I))
                item['html_inline_css'] = bool(re.search(r'<style\b|\bstyle\s*=', t, re.I))
            self.selected.append(item)
            self.seen.append((sid, clean, g))
            self.families.add(family)
            self.event(**base, sample_id=sid, decision='selected_provisionally', start_byte=start, end_byte=end)
            save(self.out / 'manifest.json', self.manifest('provisional_running'))
            print(f'Selected {len(self.selected):3}: {row["stratum"]}: {path}', flush=True)
            return True
        self.event(**base, decision='reject', reason='no_eligible_paragraph')
        return False

    def manifest(self, status):
        return {'status': status, 'config_sha256': digest(CONFIG.read_bytes()),
            'collector_sha256': digest(Path(__file__).read_bytes()),
            'samples': self.selected, 'counts': dict(Counter(r['stratum'] for r in self.selected)),
            'reviewer': 'Codex; no independent human review claimed',
            'raw_text_published': False, 'tokenization_performed': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--reviews', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cfg = json.loads(CONFIG.read_text())
    assert digest(Path(cfg['protocol']).read_bytes()) == cfg['protocol_sha256']
    inventory = json.loads(Path(cfg['candidate_inventory']).read_text())
    assert inventory['config_sha256'] == digest(CONFIG.read_bytes())
    reviews = json.loads(args.reviews.read_text()) if args.reviews else {}
    collector = Collector(cfg, reviews, args.fetch, args.output)
    pools = defaultdict(list)
    for row in inventory['candidates']:
        pools[row['stratum']].append(row)
    for pool in pools.values():
        pool.sort(key=lambda r: (r['file_rank'], r['path']))
    positions, counts = Counter(), Counter()
    for pair in cfg['stratum_order']:
        for _ in range(10):
            for stratum in pair:
                while counts[stratum] < 10 and positions[stratum] < len(pools[stratum]):
                    row = pools[stratum][positions[stratum]]
                    positions[stratum] += 1
                    if collector.try_file(row):
                        counts[stratum] += 1
                        break
    manifest = collector.manifest('collected_pending_review')
    manifest['shortfalls'] = {s: 10-counts[s] for pair in cfg['stratum_order'] for s in pair if counts[s] < 10}
    manifest['reviews_sha256'] = digest(args.reviews.read_bytes()) if args.reviews else None
    if all(r['file_review'].get('decision') == 'accept' and r['sample_review'].get('decision') == 'accept' for r in collector.selected):
        manifest['status'] = 'reviewed_pending_independent_validation'
    save(args.output / 'manifest.json', manifest)
    collector.events.close()
    print(json.dumps({'status': manifest['status'], 'counts': manifest['counts'], 'shortfalls': manifest['shortfalls']}))


if __name__ == '__main__':
    main()
