"""Post-review R1-H: declared vs rewired membership crossed with median, mean and local-SVD aggregation.

Primary code is reused unchanged; this wrapper only adds models. Realization k uses null seed
primary_seed + 1000*k; k = 0 reproduces the primary degree-preserving null exactly.
"""
import argparse
import json
from pathlib import Path

import numpy as np

import human_extension as base

ORIGINAL = base.representations
EXTRA = ('descriptor_mean', 'null_mean', 'null_local_svd')


def mean_score(a, b, membership):
    weights = membership.to_numpy(dtype=float)
    weights = weights / weights.sum(axis=0)
    return a @ weights, b @ weights


def make_wrapper(offset):
    def wrapped(train, test, visible, incidence, families, seed):
        seed = seed + 1000 * offset
        values = ORIGINAL(train, test, visible, incidence, families, seed)
        keep = np.isfinite(train).mean(axis=0) >= .8
        names = list(np.asarray(visible)[keep])
        a, b, _, _ = base.standardize(train[:, keep], test[:, keep])
        member = incidence.loc[names]
        member = member.loc[:, member.sum(axis=0).ge(2)]
        null = base.degree_preserving_descriptor_null(member, swaps_per_edge=10, seed=seed)
        assert np.array_equal(member.sum(axis=0), null.sum(axis=0))
        assert np.array_equal(member.sum(axis=1), null.sum(axis=1))
        budget = values['structural_median'][2]
        extra = {
            'descriptor_mean': mean_score(a, b, member),
            'null_mean': mean_score(a, b, null),
            'null_local_svd': base.memberships_score(a, b, null, True)[:2],
        }
        for key, (x, z) in extra.items():
            x, z, _, _ = base.standardize(x, z)
            values[key] = (x, z, dict(budget))
        return values
    return wrapped


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True, choices=['st002081', 'st000818'])
    parser.add_argument('--realization', type=int, required=True)
    args = parser.parse_args()
    lock = base.sha(base.ROOT / 'readiness/post-review-r1-amendment.md')
    expected = (base.ROOT / 'receipts/post-review-r1-amendment.sha256').read_text().split()[0]
    if lock != expected:
        raise RuntimeError('R1 amendment changed after freezing')
    wrapper_hash = base.sha(__file__)
    base.MODELS = (*base.MODELS, *EXTRA)
    base.representations = make_wrapper(args.realization)
    path = base.ROOT / f'runs/r1-human-crossing-{args.dataset}-k{args.realization:02d}'
    result = base.run(args.dataset, 'primary', path)
    assert base.sha(__file__) == wrapper_hash
    result.update(post_review_r1=True, realization=args.realization, wrapper_sha256=wrapper_hash,
                  amendment_sha256=lock)
    (path / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'dataset': args.dataset, 'k': args.realization, 'elapsed': result['elapsed_seconds']}))
