"""Add reproducible rejection labels for URL-only English and translation boilerplate.

This screens cached mixed-script documents only, never selects a sample or
approves a passage. Acceptance still requires the recorded text review.
"""
import argparse
import json
from pathlib import Path
import re
from collect_published_text import RAW, paragraphs, rank, save


def outside_links(text):
    # Retain link labels, remove image labels and Markdown destinations.
    text = re.sub(r'(!?)\[([^\]]*)\]\([^)]*\)',
                  lambda m: '' if m[1] else m[2], text)
    text = re.sub(r'https?://[^\s<>]+', '', text)
    return re.sub(r'<[^>]*>', '', text)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists()
    reviews = json.loads(args.input.read_text())
    cfg = json.loads(Path('config/published-text-sources-v1.json').read_text())
    rows = json.loads(Path(cfg['candidate_inventory']).read_text())['candidates']
    added = 0
    for row in rows:
        if row['category'] != 'mixed':
            continue
        path = RAW / row['repo'] / row['revision'] / row['path']
        if not path.exists():
            continue
        raw = path.read_bytes()
        for a, b, reason in paragraphs(raw):
            if reason:
                continue
            text = raw[a:b].decode('utf-8')
            if not 200 <= len(text) <= 2000:
                continue
            reject = None
            if 'Co-op Translator' in text:
                reject = 'Translation-service boilerplate in this pinned source, excluded by protocol.'
            elif not re.search('[A-Za-z]', outside_links(text)):
                reject = 'No ASCII letters outside link destinations, images and HTML tags.'
            if reject:
                sid = rank([row['repo'], row['revision'], row['path'], str(a), str(b)])[:24]
                if sid not in reviews['samples']:
                    reviews['samples'][sid] = {'decision': 'reject', 'reason': reject,
                        'review_kind': 'automated_conservative_screen'}
                    added += 1
    save(args.output, reviews)
    print(f'Added {added} rejection labels; no acceptances generated.')


if __name__ == '__main__':
    main()
