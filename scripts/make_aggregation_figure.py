"""Figure 4: declared versus rewired membership under median, mean and local-SVD aggregation (post-review R1-H)."""
import hashlib
import json
import os
from pathlib import Path

os.environ['MPLBACKEND'] = 'Agg'
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / 'results', ROOT / 'figures'
BIO, COMPACT, INK, MUTED, GRID = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': MUTED, 'xtick.color': MUTED, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
AGG = [('median', 'Median'), ('mean', 'Mean*'), ('local_svd', 'Local SVD')]


def main():
    crossing = pd.read_csv(RES / 'r1-membership-by-aggregation.csv').set_index(['dataset', 'aggregation'])
    metrics = pd.read_csv(RES / 'all-model-metrics.csv')
    pca = metrics[metrics['mode'].eq('primary') & metrics.model.eq('pca_matched_dimension')].set_index('dataset').primary_rmse
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    for ax, (ds, title) in zip(axes, [('st002081', 'A  ST002081'), ('st000818', 'B  ST000818')]):
        top = max(crossing.loc[(ds, a)].expected_null_rmse for a, _ in AGG)
        for y, (agg, label) in zip([2, 1, 0], AGG):
            r = crossing.loc[(ds, agg)]
            ax.plot([r.declared_rmse, r.expected_null_rmse], [y, y], color=GRID, lw=2, zorder=1)
            ax.scatter(r.expected_null_rmse, y, s=46, facecolor='white', edgecolor=INK, lw=1.4, zorder=3)
            ax.scatter(r.declared_rmse, y, s=46, facecolor=BIO, edgecolor=BIO, zorder=3)
            ax.text(top * 1.06, y, f'Δ {r.improvement:+.3f}\n[{r.ci95_lower:.3f}, {r.ci95_upper:.3f}]',
                    va='center', fontsize=7, color=INK)
        ax.axvline(pca[ds], color=COMPACT, ls='--', lw=1.2)
        ax.text(pca[ds], 2.55, 'PCA', color=INK, fontsize=7, ha='center')
        ax.set_yticks([2, 1, 0], [label for _, label in AGG])
        ax.set_ylim(-0.6, 2.8)
        ax.set_xlim(0, top * 1.45)
        ax.set_xlabel('Held-out RMSE (training SD)')
        ax.xaxis.grid(True, color=GRID, lw=.8); ax.set_axisbelow(True)
        ax.set_title(title, loc='left', fontweight='bold', fontsize=9)
    handles = [plt.Line2D([], [], marker='o', ls='', color=BIO, label='Declared membership'),
               plt.Line2D([], [], marker='o', ls='', markerfacecolor='white', markeredgecolor=INK, label='Matched null (expected, 20 realizations)'),
               plt.Line2D([], [], ls='--', color=COMPACT, label='Dimension-matched PCA'),
               plt.Line2D([], [], ls='', label='* secondary, outcome-aware aggregator')]
    fig.legend(handles=handles, loc='lower center', ncol=2, frameon=False, fontsize=7)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.88, bottom=0.33, wspace=0.42)
    for suffix in ('png', 'pdf', 'svg'):
        fig.savefig(OUT / f'figure4-membership-aggregation.{suffix}', dpi=220)
    plt.close(fig)
    manifest = OUT / 'manifest.json'
    data = json.loads(manifest.read_text())
    data['aggregation_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for p in sorted(OUT.glob('figure4-membership-aggregation.*')):
        data['files'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(data, indent=2) + '\n')


if __name__ == '__main__':
    main()
