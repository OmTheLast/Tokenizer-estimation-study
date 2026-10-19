"""Plot actual corpus lengths; this is not token-count evidence."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    samples = json.loads(args.manifest.read_text())['samples']
    categories = ['prose', 'mixed', 'html', 'json', 'code']
    labels = ['English passages', 'Mixed-script passages', 'HTML files', 'JSON files', 'Code files']
    colors = ['#3274A1', '#7657A6', '#3C8D78', '#C18A24', '#B55D64']
    rows = [{'sample_id': r['sample_id'], 'category': r['category'],
             'codepoints': r['lengths_and_scripts']['codepoints']} for r in samples]
    (args.output / 'plot-data.json').write_text(json.dumps(rows, indent=2) + '\n')
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for y, (category, color) in enumerate(zip(categories, colors)):
        data = [r['codepoints'] for r in rows if r['category'] == category]
        # Deterministic vertical spreading prevents complete overlap; no data jitter on x.
        offsets = [((i * 7) % len(data) - (len(data)-1)/2) / len(data) * .42 for i in range(len(data))]
        ax.scatter(data, [y+v for v in offsets], color=color, s=31, alpha=.83,
                   edgecolor='white', linewidth=.5)
    ax.set_yticks(range(len(categories)), [f'{label} (n=20)' for label in labels])
    ax.invert_yaxis()
    ax.set_xlim(0, 12000)
    ax.set_xticks(range(0, 12001, 2000))
    ax.set_xlabel('Text length in Unicode code points (not tokens)', labelpad=10)
    ax.grid(axis='x', color='#E3E7ED', linewidth=.7)
    ax.set_axisbelow(True)
    for side in ['top', 'right', 'left']:
        ax.spines[side].set_visible(False)
    ax.tick_params(axis='y', length=0, pad=8)
    fig.suptitle('Our 100 samples have different lengths', x=.03, ha='left', fontsize=16, fontweight='bold')
    fig.text(.03, .885, 'Each dot is one original passage or complete file. No tokenizer measurements yet.', fontsize=10)
    fig.text(.03, .025, 'Passages: allowed 200–2,000 code points. Complete files: 200–12,000. Published technical sources only.', fontsize=9)
    fig.subplots_adjust(left=.25, right=.97, top=.82, bottom=.18)
    for suffix in ('png', 'svg', 'pdf'):
        fig.savefig(args.output / f'sample-lengths.{suffix}', dpi=160)
    svg = args.output / 'sample-lengths.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    plt.close(fig)


if __name__ == '__main__':
    main()
