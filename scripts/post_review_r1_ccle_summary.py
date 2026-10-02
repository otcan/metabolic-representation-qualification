"""Summarize post-review R1-C with the unchanged primary CCLE inference (lineage bootstrap, fixed targets).

primary_inference() compares the 'correlation_selected_ridge' slot (reference) with 'direct_neighbor_ridge';
null losses are placed in the reference slot, so improvement = RMSE(null) - RMSE(declared neighbours).
"""
import json
import numpy as np
import pandas as pd
import ccle_extension as ce

ROOT = ce.WORKSPACE
declared = pd.read_csv(ROOT / 'runs/m2-ccle/lineage-target-losses.csv')
declared = declared[declared.model.eq('direct_neighbor_ridge')]
rows, null_frames = [], []
for seed in range(20262100, 20262120):
    null = pd.read_csv(ROOT / f'runs/r1-ccle-null-s{seed}/lineage-target-losses.csv')
    null_frames.append(null.assign(seed=seed))
    frame = pd.concat([declared, null.assign(model='correlation_selected_ridge')])
    r = ce.primary_inference(frame)
    rows.append({'seed': seed, 'improvement': r['rmse_improvement_sd'], 'ci95_lower': r['ci95_lower'], 'ci95_upper': r['ci95_upper']})
per_seed = pd.DataFrame(rows)
expected = pd.concat(null_frames).groupby(['target', 'lineage'], as_index=False).mean_squared_error.mean()
frame = pd.concat([declared, expected.assign(model='correlation_selected_ridge')])
r = ce.primary_inference(frame)
summary = {'comparison': 'ccle_rewired_null_minus_declared_direct_neighbours (expected over 20 property-matched seeds)',
           'declared_rmse_sd': float(np.sqrt(declared.groupby('target').mean_squared_error.mean().mean())),
           'expected_null_rmse_sd': float(np.sqrt(expected.groupby('target').mean_squared_error.mean().mean())),
           'improvement_sd': r['rmse_improvement_sd'], 'ci95_lower': r['ci95_lower'], 'ci95_upper': r['ci95_upper'],
           'draws': r['draws'], 'biological_groups': r['biological_groups'], 'targets': r['targets'],
           'uncertainty_scope': r['uncertainty_scope']}
summary.update(seeds=len(per_seed), seeds_positive=int((per_seed.improvement > 0).sum()), seeds_ci_above_zero=int((per_seed.ci95_lower > 0).sum()),
               seed_min=float(per_seed.improvement.min()), seed_max=float(per_seed.improvement.max()))
per_seed.to_csv(ROOT / 'results/r1-ccle-null-per-seed.csv', index=False)
(ROOT / 'results/r1-ccle-null-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2)); print(per_seed.round(4).to_string(index=False))
