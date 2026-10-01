"""The qualification-ladder text and figure data must agree with accepted run outputs."""
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _steps():
    return pd.read_csv(ROOT / 'results/qualification-steps.csv')


def test_ladder_rungs_match_primary_metrics():
    ladder = pd.read_csv(ROOT / 'results/qualification-ladder.csv')
    metrics = pd.read_csv(ROOT / 'results/all-model-metrics.csv')
    metrics = metrics[metrics['mode'].eq('primary')].set_index(['dataset', 'model']).primary_rmse
    for row in ladder.itertuples():
        assert abs(metrics[(row.dataset, row.rung)] - row.rmse) < 1e-12


def test_steps_are_positive_and_shares_sum_to_one():
    steps = _steps()
    for row in steps[~steps.step.str.endswith('share')].itertuples():
        assert row.estimate > 0 and row.ci95_lower > 0, row
    shares = steps[steps.step.str.endswith('share')].groupby('dataset').estimate.sum()
    assert ((shares - 1).abs() < 1e-12).all()


def test_ccle_primary_step_matches_locked_contrast():
    steps = _steps().set_index(['dataset', 'step'])
    locked = pd.read_csv(ROOT / 'results/primary-comparisons.csv').set_index('dataset').loc['ccle']
    assert abs(steps.loc[('ccle', 'compact_vs_biochemistry')].estimate + locked.improvement) < 1e-12


def test_every_number_in_ladder_section_is_backed():
    text = (ROOT / 'manuscript/main.md').read_text()
    section = text.split('### A qualification ladder', 1)[1].split('### Historical', 1)[0]
    section = re.sub(r'\{width=\d+%\}', '', section)  # image layout attributes are not claims
    backed = set()
    for row in _steps().itertuples():
        if row.step.endswith('share'):
            backed.add(f'{round(row.estimate * 100):d}%')
        else:
            backed.update(f'{v:.3f}' for v in (row.estimate, row.ci95_lower, row.ci95_upper))
    quoted = [x for x in re.findall(r'\d+\.\d{3}|\d+%', section) if x != '95%']
    assert quoted and all(x in backed for x in quoted), [x for x in quoted if x not in backed]


def test_toy_null_preserves_degrees():
    real = {'D1': [0, 1, 2], 'D2': [1, 2], 'D3': [3, 4, 5]}
    rewired = {'D1': [1, 3, 5], 'D2': [0, 2], 'D3': [1, 2, 4]}
    assert {k: len(v) for k, v in real.items()} == {k: len(v) for k, v in rewired.items()}
    assert Counter(sum(real.values(), [])) == Counter(sum(rewired.values(), []))
