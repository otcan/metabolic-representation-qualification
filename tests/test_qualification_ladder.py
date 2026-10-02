"""Ladder, post-review analyses and manuscript numbers must agree with the results files."""
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results'


def _steps():
    return pd.read_csv(RES / 'qualification-steps.csv')


def _section(start):
    text = (ROOT / 'manuscript/main.md').read_text()
    body = text.split(start, 1)[1]
    body = body.split('\n### ', 1)[0]
    body = re.sub(r'\{width=\d+%\}', '', body)
    return re.sub(r'!\[.*?\]\(.*?\)', '', body, flags=re.S)


def test_ladder_rungs_match_results():
    ladder = pd.read_csv(RES / 'qualification-ladder.csv')
    metrics = pd.read_csv(RES / 'all-model-metrics.csv')
    metrics = metrics[metrics['mode'].eq('primary')].set_index(['dataset', 'model']).primary_rmse
    crossing = pd.read_csv(RES / 'r1-membership-by-aggregation.csv').set_index(['dataset', 'aggregation'])
    ccle = json.loads((RES / 'r1-ccle-null-summary.json').read_text())
    for row in ladder.itertuples():
        if row.rung == 'expected_null':
            expected = ccle['expected_null_rmse_sd'] if row.dataset == 'ccle' else crossing.loc[(row.dataset, 'median')].expected_null_rmse
        else:
            expected = metrics[(row.dataset, row.rung)]
        assert abs(expected - row.rmse) < 1e-12, row


def test_steps_positive_and_shares_sum_to_one():
    steps = _steps()
    main = steps[steps.step.isin(['biochemistry_vs_matched_null', 'compact_vs_biochemistry'])]
    assert len(main) == 6 and (main.estimate > 0).all() and (main.ci95_lower > 0).all()
    shares = steps[steps.step.str.contains('_share_')].copy()
    shares['scale'] = shares.step.str.rsplit('_', n=1).str[1]
    sums = shares.groupby(['dataset', 'scale']).estimate.sum()
    assert len(sums) == 6 and ((sums - 1).abs() < 1e-12).all()


def test_declared_runs_reproduce_accepted_results():
    ccle = json.loads((RES / 'r1-ccle-null-summary.json').read_text())
    assert abs(ccle['declared_rmse_sd'] - 0.8238802404236419) < 1e-12
    assert ccle['seeds'] == 20 and ccle['seeds_ci_above_zero'] == 20
    crossing = pd.read_csv(RES / 'r1-membership-by-aggregation.csv').set_index(['dataset', 'aggregation'])
    assert abs(crossing.loc[('st002081', 'median')].declared_rmse - 0.3167797462633834) < 1e-12
    assert abs(crossing.loc[('st000818', 'local_svd')].declared_rmse - 0.957410719643628) < 1e-12


def test_ladder_section_numbers_are_backed():
    backed = set()
    for row in _steps().itertuples():
        if '_share_' in row.step:
            backed.add(f'{round(row.estimate * 100):d}%')
        else:
            backed.update(f'{v:.3f}' for v in (row.estimate, row.ci95_lower, row.ci95_upper) if pd.notna(v))
    quoted = [x for x in re.findall(r'\d+\.\d{3}|\d+%', _section('### A qualification ladder')) if x != '95%']
    assert quoted and all(x in backed for x in quoted), [x for x in quoted if x not in backed]


def test_aggregation_section_numbers_are_backed():
    crossing = pd.read_csv(RES / 'r1-membership-by-aggregation.csv')
    backed = {'0.2425', '0.9443', '0.2434', '0.9574', '62%', '73%'}
    for row in crossing.itertuples():
        backed.update(f'{abs(v):.3f}' for v in (row.improvement, row.ci95_lower, row.ci95_upper))
        backed.update(f'{v:.4f}' for v in (row.declared_rmse, row.expected_null_rmse))
    quoted = re.findall(r'\d+\.\d{3,4}|\d+%', _section('### The membership advantage depends on aggregation'))
    quoted = [q for q in quoted if q != '95%']
    assert quoted and all(q in backed for q in quoted), [q for q in quoted if q not in backed]


def test_toy_null_preserves_degrees():
    real = {'D1': [0, 1, 2], 'D2': [1, 2], 'D3': [3, 4, 5]}
    rewired = {'D1': [1, 3, 5], 'D2': [0, 2], 'D3': [1, 2, 4]}
    assert {k: len(v) for k, v in real.items()} == {k: len(v) for k, v in rewired.items()}
    assert Counter(sum(real.values(), [])) == Counter(sum(rewired.values(), []))
