"""Qualification ladder: assemble existing results into one matched-null/compact-baseline view.

No model is refitted. Every value is read from accepted run outputs:
- human rungs and paired step intervals: runs/m2-human-r2-<dataset>-primary/
- CCLE compact-baseline step: results/primary-comparisons.csv
- CCLE matched-null step: archived property-matched null ensemble (earlier estimator; labelled).
"""
import hashlib
import json
import os
from pathlib import Path

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures'
RES = ROOT / 'results'
ARCHIVE = ROOT / 'inputs/central-package/reproducible-release/artifacts/pathway-score-ccle-property-matched-null/report.md'
if not ARCHIVE.exists():  # public archive layout
    ARCHIVE = ROOT / 'evidence/archived-ccle-property-matched-null/report.md'
RUNS = ROOT / 'runs' if (ROOT / 'runs').exists() else ROOT / 'evidence/new'

BIO, COMPACT = '#2a78d6', '#eb6834'          # validated categorical pair (dataviz validator: all checks pass)
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': INK, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})

HUMAN = {'st002081': 'ST002081 · 112 participants', 'st000818': 'ST000818 · 15 groups'}
RUNGS = [('population_mean', 'Training mean', 'no structure'),
         ('degree_preserving_null', 'Matched null', 'same shape, random membership'),
         ('structural_median', 'Biochemical descriptors', 'declared membership, median'),
         ('pca_matched_dimension', 'Compact statistics', 'PCA, same dimension'),
         ('all_visible_ridge', 'All-visible ridge', 'full panel, reference')]


def human_tables():
    metrics = pd.read_csv(RES / 'all-model-metrics.csv')
    metrics = metrics[metrics['mode'].eq('primary')]
    ladder, steps = [], []
    for ds in HUMAN:
        m = metrics[metrics.dataset.eq(ds)].set_index('model').primary_rmse
        for key, label, note in RUNGS:
            ladder.append({'dataset': ds, 'rung': key, 'label': label, 'note': note, 'rmse': m[key]})
        pc = pd.read_csv(RUNS / f'm2-human-r2-{ds}-primary/paired-comparisons.csv').set_index('reference')
        null = pc.loc['degree_preserving_null']          # improvement = null RMSE - structural RMSE
        pca = pc.loc['pca_matched_dimension']            # improvement = PCA RMSE - structural RMSE
        steps.append({'dataset': ds, 'step': 'biochemistry_vs_matched_null', 'estimate': null.rmse_improvement,
                      'ci95_lower': null.ci95_lower, 'ci95_upper': null.ci95_upper, 'estimator': 'primary equal-group RMSE'})
        steps.append({'dataset': ds, 'step': 'compact_vs_biochemistry', 'estimate': -pca.rmse_improvement,
                      'ci95_lower': -pca.ci95_upper, 'ci95_upper': -pca.ci95_lower, 'estimator': 'primary equal-group RMSE'})
        mean, nul, bio, cmp_ = (m[k] for k in ('population_mean', 'degree_preserving_null', 'structural_median',
                                               'pca_matched_dimension'))
        gap = mean - cmp_
        for share, value in (('matched_null_share', (mean - nul) / gap), ('biochemistry_share', (nul - bio) / gap),
                             ('compact_share', (bio - cmp_) / gap)):
            steps.append({'dataset': ds, 'step': share, 'estimate': value, 'ci95_lower': None, 'ci95_upper': None,
                          'estimator': 'descriptive share of training-mean-to-PCA gap'})
    return pd.DataFrame(ladder), steps


def ccle_steps():
    text = ARCHIVE.read_text()
    line = next(l for l in text.splitlines() if l.startswith('Across 20 random feature realizations'))
    nums = [float(x) for x in __import__('re').findall(r'-?\d+\.\d+', line)]
    est, lo, hi = nums[0], nums[1], nums[2]
    pc = pd.read_csv(RES / 'primary-comparisons.csv').set_index('dataset').loc['ccle']
    return [{'dataset': 'ccle', 'step': 'biochemistry_vs_matched_null', 'estimate': est, 'ci95_lower': lo,
             'ci95_upper': hi, 'estimator': 'archived property-matched 20-seed ensemble (earlier estimator)'},
            {'dataset': 'ccle', 'step': 'compact_vs_biochemistry', 'estimate': -pc.improvement,
             'ci95_lower': -pc.ci95_upper, 'ci95_upper': -pc.ci95_lower, 'estimator': 'primary equal-lineage RMSE'}]


def schematic(ax, title, edges):
    lip_x = [0, 1, 2, 3, 4, 5]
    des_x = {'D1': 0.75, 'D2': 2.5, 'D3': 4.25}
    for d, members in edges.items():
        for l in members:
            ax.plot([lip_x[l], des_x[d]], [1, 0], color=MUTED, lw=1.2, zorder=1)
    for i, x in enumerate(lip_x):
        ax.scatter(x, 1, s=110, marker='o' if i < 3 else 's', color='white', edgecolor=INK, lw=1.4, zorder=3)
        ax.text(x, 1.17, f'L{i + 1}', ha='center', va='bottom', fontsize=8, color=INK)
    for d, x in des_x.items():
        ax.scatter(x, 0, s=150, marker='D', color=INK, zorder=3)
        ax.text(x, -0.2, f'{d}  ({len(edges[d])} lipids)', ha='center', va='top', fontsize=7, color=INK)
    ax.set_xlim(-0.5, 5.5); ax.set_ylim(-0.55, 1.5); ax.axis('off')
    ax.set_title(title, fontsize=9, color=INK, loc='left')


def main():
    ladder, steps = human_tables()
    steps = pd.DataFrame(steps + ccle_steps())
    ladder.to_csv(RES / 'qualification-ladder.csv', index=False)
    steps.to_csv(RES / 'qualification-steps.csv', index=False)

    fig = plt.figure(figsize=(7.0, 8.4))
    real = {'D1': [0, 1, 2], 'D2': [1, 2], 'D3': [3, 4, 5]}
    rewired = {'D1': [1, 3, 5], 'D2': [0, 2], 'D3': [1, 2, 4]}
    from collections import Counter
    assert {d: len(m) for d, m in real.items()} == {d: len(m) for d, m in rewired.items()}
    assert Counter(sum(real.values(), [])) == Counter(sum(rewired.values(), [])), 'schematic null must preserve degrees'
    fig.text(0.02, 0.975, 'A', fontsize=12, fontweight='bold', color=INK)
    schematic(fig.add_axes([0.05, 0.80, 0.42, 0.16]), 'Declared biochemical membership', real)
    schematic(fig.add_axes([0.55, 0.80, 0.42, 0.16]), 'Matched null: same shape, rewired membership', rewired)
    fig.text(0.05, 0.775, 'The null keeps every descriptor\'s size and every lipid\'s number of descriptors; only which lipids '
             'share a descriptor is randomized.\nCircles and squares mark two lipid classes: declared descriptors group '
             'like with like, the null mixes them.', fontsize=7, color=MUTED, va='top')

    style = {'population_mean': ('o', 'white', MUTED), 'degree_preserving_null': ('o', 'white', INK),
             'structural_median': ('o', BIO, BIO), 'pca_matched_dimension': ('o', COMPACT, COMPACT),
             'all_visible_ridge': ('s', MUTED, MUTED)}
    for col, (ds, title) in enumerate(HUMAN.items()):
        ax = fig.add_axes([0.30 + col * 0.36, 0.43, 0.30, 0.27])
        frame = ladder[ladder.dataset.eq(ds)].reset_index(drop=True)
        ys = list(range(len(frame)))[::-1]
        for y, row in zip(ys, frame.itertuples()):
            mk, face, edge = style[row.rung]
            ax.plot([0, row.rmse], [y, y], color=GRID, lw=1, zorder=1)
            ax.scatter(row.rmse, y, s=64, marker=mk, facecolor=face, edgecolor=edge, lw=1.5, zorder=3)
            ax.text(row.rmse + frame.rmse.max() * 0.04, y, f'{row.rmse:.3f}', va='center', fontsize=8, color=INK)
        ax.set_yticks(ys, [f'{r.label}\n{r.note}' for r in frame.itertuples()] if col == 0 else [''] * len(ys), fontsize=7)
        ax.set_ylim(-0.6, len(frame) - 0.4)
        ax.set_xlim(0, frame.rmse.max() * 1.25)
        ax.set_xlabel('Held-out RMSE (training-SD units)', fontsize=8)
        ax.xaxis.grid(True, color=GRID, lw=.8); ax.set_axisbelow(True)
        ax.set_title(f'{"BC"[col]}  {title}', loc='left', fontsize=9.5, fontweight='bold', color=INK)
    fig.text(0.05, 0.375, 'Lower is better. Matched null and biochemical descriptors share shape, so their gap isolates '
             'biochemical membership.', fontsize=7, color=MUTED)

    ax = fig.add_axes([0.42, 0.05, 0.54, 0.27])
    order = [('st002081', 'ST002081'), ('st000818', 'ST000818'), ('ccle', 'CCLE')]
    labels, ys, y = [], [], 0
    for ds, name in order:
        for step, color, text in (('biochemistry_vs_matched_null', BIO, 'biochemistry beats matched null'),
                                  ('compact_vs_biochemistry', COMPACT, 'compact statistics beat biochemistry')):
            r = steps[(steps.dataset == ds) & (steps.step == step)].iloc[0]
            archived = 'archived' in r.estimator
            ax.plot([r.ci95_lower, r.ci95_upper], [y, y], color=color, lw=3, solid_capstyle='butt', zorder=2)
            ax.scatter(r.estimate, y, s=56, facecolor='white' if archived else color, edgecolor=color, lw=1.6, zorder=3)
            labels.append(f'{name}: {text}' + ('\n(archived property-matched null,\nearlier estimator)' if archived else ''))
            ys.append(y); y -= 1
        y -= 0.6
    ax.set_yticks(ys, labels, fontsize=7)
    ax.axvline(0, color=MUTED, lw=1, ls='--')
    ax.set_xlim(-0.05, 1.1)
    ax.set_xlabel('Error reduction from the step (training-SD units; 95% interval)', fontsize=8)
    ax.xaxis.grid(True, color=GRID, lw=.8); ax.set_axisbelow(True)
    ax.set_title('D  Both steps hold in every dataset', loc='left', fontsize=9.5, fontweight='bold', color=INK)

    for suffix in ('png', 'pdf', 'svg'):
        fig.savefig(OUT / f'figure1-qualification-ladder.{suffix}', dpi=220)
    plt.close(fig)
    manifest = OUT / 'manifest.json'
    data = json.loads(manifest.read_text()) if manifest.exists() else {'files': {}}
    data['ladder_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for p in sorted(OUT.glob('figure1-qualification-ladder.*')) + [RES / 'qualification-ladder.csv', RES / 'qualification-steps.csv']:
        data['files'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(steps.round(4).to_string(index=False))


if __name__ == '__main__':
    main()
