"""Summarize post-review R1-H: membership effect (rewired minus declared) for each aggregation."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import human_extension as base

ROOT = base.ROOT
PAIRS = {'median': ('degree_preserving_null', 'structural_median'),
         'mean': ('null_mean', 'descriptor_mean'),
         'local_svd': ('null_local_svd', 'descriptor_local_svd')}


def load(ds):
    frames = []
    for k in range(20):
        g = pd.read_csv(ROOT / f'work/m2-human/r1-human-crossing-{ds}-k{k:02d}/group-losses.csv')
        g['k'] = k
        frames.append(g)
    return pd.concat(frames)


def main():
    rows, per_seed = [], []
    for ds in ('st002081', 'st000818'):
        g = load(ds)
        declared = [m for _, m in PAIRS.values()]
        spread = g[g.model.isin(declared)].groupby(['model', 'group_id']).mse.agg(['min', 'max'])
        assert ((spread['max'] - spread['min']).abs() < 1e-12).all(), 'declared models must not vary by realization'
        base_k = g[g.k.eq(0)]
        for agg, (null, decl) in PAIRS.items():
            for k in range(20):
                gk = g[g.k.eq(k) & g.model.isin([null, decl])]
                r = base.paired_inference(gk[['group_id', 'model', 'mse']], null, decl)
                per_seed.append({'dataset': ds, 'aggregation': agg, 'k': k, 'improvement': r['rmse_improvement'],
                                 'ci95_lower': r['ci95_lower'], 'ci95_upper': r['ci95_upper']})
            expected = g[g.model.eq(null)].groupby('group_id', as_index=False).mse.mean().assign(model=null)
            frame = pd.concat([expected, base_k[base_k.model.eq(decl)][['group_id', 'model', 'mse']]])
            r = base.paired_inference(frame, null, decl)
            seeds = pd.DataFrame([s for s in per_seed if s['dataset'] == ds and s['aggregation'] == agg])
            rows.append({'dataset': ds, 'aggregation': agg,
                         'declared_rmse': float(np.sqrt(base_k[base_k.model.eq(decl)].mse.mean())),
                         'expected_null_rmse': float(np.sqrt(expected.mse.mean())),
                         'improvement': r['rmse_improvement'], 'ci95_lower': r['ci95_lower'], 'ci95_upper': r['ci95_upper'],
                         'seeds_positive': int((seeds.improvement > 0).sum()),
                         'seeds_ci_above_zero': int((seeds.ci95_lower > 0).sum()),
                         'seed_min': float(seeds.improvement.min()), 'seed_max': float(seeds.improvement.max())})
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / 'results/r1-membership-by-aggregation.csv', index=False)
    pd.DataFrame(per_seed).to_csv(ROOT / 'results/r1-membership-by-aggregation-per-seed.csv', index=False)
    print(out.round(4).to_string(index=False))


if __name__ == '__main__':
    main()
