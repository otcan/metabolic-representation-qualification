"""Qualification ladder: assemble existing results into one matched-null/compact-baseline view.

No model is refitted. Every value is read from accepted run outputs:
- human rungs and paired step intervals: runs/m2-human-r2-<dataset>-primary/
- CCLE compact-baseline step: results/primary-comparisons.csv
- CCLE matched-null step: archived property-matched null ensemble (earlier estimator; labelled).
"""
import hashlib
import re
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

HUMAN = {'st002081': 'ST002081', 'st000818': 'ST000818'}
DATASETS = {**HUMAN, 'ccle': 'CCLE'}
RUNGS = {
    'human': [('population_mean', 'Training mean', 'no structure'),
              ('expected_null', 'Matched null', 'same shape, rewired membership'),
              ('structural_median', 'Biochemical descriptors', 'declared membership, median'),
              ('pca_matched_dimension', 'Compact statistics', 'PCA, same dimension'),
              ('all_visible_ridge', 'Full-panel ridge', 'all visible inputs')],
    'ccle': [('population_mean', 'Training mean', 'no structure'),
             ('expected_null', 'Matched null', 'property-matched random neighbours'),
             ('direct_neighbor_ridge', 'Reaction neighbours', 'declared neighbours'),
             ('correlation_selected_ridge', 'Compact statistics', 'correlation-selected, same count'),
             ('all_other_metabolites_ridge', 'Full-panel ridge', 'all other metabolites')]}


def tables():
    """Ladder rungs and steps; every null is the 20-realization expected null under the current estimator."""
    metrics = pd.read_csv(RES / 'all-model-metrics.csv')
    metrics = metrics[metrics['mode'].eq('primary')]
    crossing = pd.read_csv(RES / 'r1-membership-by-aggregation.csv').set_index(['dataset', 'aggregation'])
    ccle_null = json.loads((RES / 'r1-ccle-null-summary.json').read_text())
    primary = pd.read_csv(RES / 'primary-comparisons.csv').set_index(['dataset', 'reference'])
    ladder, steps = [], []
    for ds in DATASETS:
        m = metrics[metrics.dataset.eq(ds)].set_index('model').primary_rmse.to_dict()
        if ds == 'ccle':
            m['expected_null'] = ccle_null['expected_null_rmse_sd']
            null_step = (ccle_null['improvement_sd'], ccle_null['ci95_lower'], ccle_null['ci95_upper'])
            bio, cmp_key, ref = 'direct_neighbor_ridge', 'correlation_selected_ridge', 'correlation_selected_ridge'
            rungs = RUNGS['ccle']
        else:
            row = crossing.loc[(ds, 'median')]
            m['expected_null'] = row.expected_null_rmse
            null_step = (row.improvement, row.ci95_lower, row.ci95_upper)
            bio, cmp_key, ref = 'structural_median', 'pca_matched_dimension', 'pca_matched_dimension'
            rungs = RUNGS['human']
        for key, label, note in rungs:
            ladder.append({'dataset': ds, 'rung': key, 'label': label, 'note': note, 'rmse': m[key]})
        c = primary.loc[(ds, ref)]
        steps.append({'dataset': ds, 'step': 'biochemistry_vs_matched_null', 'estimate': null_step[0],
                      'ci95_lower': null_step[1], 'ci95_upper': null_step[2],
                      'estimator': 'expected over 20 null realizations; current estimator; biological-group bootstrap'})
        steps.append({'dataset': ds, 'step': 'compact_vs_biochemistry', 'estimate': -c.improvement,
                      'ci95_lower': -c.ci95_upper, 'ci95_upper': -c.ci95_lower,
                      'estimator': 'locked primary contrast; biological-group bootstrap'})
        mean, nul, b, cm = m['population_mean'], m['expected_null'], m[bio], m[cmp_key]
        for scale, f in (('rmse', lambda v: v), ('mse', lambda v: v ** 2)):
            gap = f(mean) - f(cm)
            for share, value in (('matched_null_share', (f(mean) - f(nul)) / gap), ('biochemistry_share', (f(nul) - f(b)) / gap),
                                 ('compact_share', (f(b) - f(cm)) / gap)):
                steps.append({'dataset': ds, 'step': f'{share}_{scale}', 'estimate': value, 'ci95_lower': None,
                              'ci95_upper': None, 'estimator': f'descriptive share of training-mean-to-compact gap ({scale.upper()} scale)'})
    text = ARCHIVE.read_text()
    line = next(l for l in text.splitlines() if l.startswith('Across 20 random feature realizations'))
    est, lo, hi = [float(x) for x in re.findall(r'-?\d+\.\d+', line)][:3]
    steps.append({'dataset': 'ccle', 'step': 'archived_biochemistry_vs_matched_null', 'estimate': est, 'ci95_lower': lo,
                  'ci95_upper': hi, 'estimator': 'archived property-matched ensemble; released estimator; target bootstrap (supplement only)'})
    return pd.DataFrame(ladder), pd.DataFrame(steps)


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
    ladder, steps = tables()
    ladder.to_csv(RES / 'qualification-ladder.csv', index=False)
    steps.to_csv(RES / 'qualification-steps.csv', index=False)

    fig = plt.figure(figsize=(7.2, 9.0))
    real = {'D1': [0, 1, 2], 'D2': [1, 2], 'D3': [3, 4, 5]}
    rewired = {'D1': [1, 3, 5], 'D2': [0, 2], 'D3': [1, 2, 4]}
    from collections import Counter
    assert {d: len(m) for d, m in real.items()} == {d: len(m) for d, m in rewired.items()}
    assert Counter(sum(real.values(), [])) == Counter(sum(rewired.values(), [])), 'schematic null must preserve degrees'
    fig.text(0.02, 0.975, 'A', fontsize=12, fontweight='bold', color=INK)
    schematic(fig.add_axes([0.05, 0.815, 0.42, 0.15]), 'Declared biochemical membership', real)
    schematic(fig.add_axes([0.55, 0.815, 0.42, 0.15]), 'Matched null: same degrees, rewired membership', rewired)
    fig.text(0.05, 0.79, "The null keeps every descriptor's size and every lipid's number of descriptors; which lipids co-occur in a "
             "descriptor,\nand hence pairwise overlaps, are randomized. Circles and squares mark two lipid classes.",
             fontsize=7, color=MUTED, va='top')
    style = {'population_mean': ('o', 'white', MUTED), 'expected_null': ('o', 'white', INK),
             'structural_median': ('o', BIO, BIO), 'direct_neighbor_ridge': ('o', BIO, BIO),
             'pca_matched_dimension': ('o', COMPACT, COMPACT), 'correlation_selected_ridge': ('o', COMPACT, COMPACT),
             'all_visible_ridge': ('s', MUTED, MUTED), 'all_other_metabolites_ridge': ('s', MUTED, MUTED)}
    labels = ['Training mean', 'Matched null', 'Biochemical\nrepresentation', 'Compact\nstatistics', 'Full-panel\nridge']
    for col, (ds, title) in enumerate(DATASETS.items()):
        ax = fig.add_axes([0.20 + col * 0.27, 0.45, 0.22, 0.27])
        frame = ladder[ladder.dataset.eq(ds)].reset_index(drop=True)
        ys = list(range(len(frame)))[::-1]
        for y, row in zip(ys, frame.itertuples()):
            mk, face, edge = style[row.rung]
            ax.plot([0, row.rmse], [y, y], color=GRID, lw=1, zorder=1)
            ax.scatter(row.rmse, y, s=50, marker=mk, facecolor=face, edgecolor=edge, lw=1.4, zorder=3)
            ax.text(row.rmse + frame.rmse.max() * 0.05, y, f'{row.rmse:.3f}', va='center', fontsize=7, color=INK)
        ax.set_yticks(ys, labels if col == 0 else [''] * len(ys), fontsize=7.5)
        ax.set_ylim(-0.6, len(frame) - 0.4)
        ax.set_xlim(0, frame.rmse.max() * 1.35)
        ax.set_xlabel('Held-out RMSE (training SD)', fontsize=7.5)
        ax.tick_params(axis='x', labelsize=7)
        ax.xaxis.grid(True, color=GRID, lw=.8); ax.set_axisbelow(True)
        ax.set_title(f'{"BCD"[col]}  {title}', loc='left', fontsize=8, fontweight='bold', color=INK)
    fig.text(0.05, 0.372, 'Lower is better. CCLE rungs: reaction neighbours (biochemical), correlation-selected panel of the same size '
             '(compact),\nall other metabolites (full panel). Matched nulls are expected values over 20 realizations.',
             fontsize=7, color=MUTED)

    ax = fig.add_axes([0.42, 0.05, 0.54, 0.26])
    order = [('st002081', 'ST002081'), ('st000818', 'ST000818'), ('ccle', 'CCLE')]
    ticks, ys, y = [], [], 0
    for ds, name in order:
        for step, color, text in (('biochemistry_vs_matched_null', BIO, 'declared membership beats matched null'),
                                  ('compact_vs_biochemistry', COMPACT, 'compact statistics beat biochemistry')):
            r = steps[(steps.dataset == ds) & (steps.step == step)].iloc[0]
            ax.plot([r.ci95_lower, r.ci95_upper], [y, y], color=color, lw=3, solid_capstyle='butt', zorder=2)
            ax.scatter(r.estimate, y, s=50, facecolor=color, edgecolor=color, lw=1.4, zorder=3)
            ticks.append(f'{name}: {text}')
            ys.append(y); y -= 1
        y -= 0.6
    ax.set_yticks(ys, ticks, fontsize=7.5)
    ax.axvline(0, color=MUTED, lw=1, ls='--')
    ax.set_xlim(-0.05, 1.1)
    ax.set_xlabel('Error reduction from the step (training SD; 95% biological-group interval)', fontsize=7.5)
    ax.xaxis.grid(True, color=GRID, lw=.8); ax.set_axisbelow(True)
    ax.set_title('E  Both steps, median or fixed-neighbour aggregation', loc='left', fontsize=9, fontweight='bold', color=INK)

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
