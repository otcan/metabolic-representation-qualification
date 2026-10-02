"""Post-review R1-C: property-matched CCLE null under the current direct-neighbour estimator.

ccle_extension.py is reused unchanged. Only the target neighbour sets are replaced by the archived
property-matched random metabolite sets (network degree and assay coverage; no outcome data), and only
the direct-neighbour model is fitted, on the accepted outer splits and tuning grid.
"""
import argparse
import dataclasses
import json
import sys
from pathlib import Path

import pandas as pd
from threadpoolctl import threadpool_limits

import ccle_extension as ce

ROOT = ce.WORKSPACE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args()
    expected = (ROOT / 'receipts/post-review-r1-amendment.sha256').read_text().split()[0]
    if ce.sha256(ROOT / 'readiness/post-review-r1-amendment.md') != expected:
        raise RuntimeError('R1 amendment changed after freezing')
    original_load = ce.load_inputs

    def null_inputs(release):
        metabolites, signatures, lineages, targets, archived, provenance = original_load(release)
        from genotype_gated_metabolism.analysis.ccle_pathway_prediction import propensity_matched_target_feature_sets
        candidates = pd.read_csv(release / 'artifacts/ccle-expanded/ccle_candidate_hypotheses.csv')
        features = propensity_matched_target_feature_sets(
            candidates, mapped_metabolites=list(metabolites.columns),
            available_signatures=list(signatures.columns),
            metabolite_coverage=metabolites.notna().mean(axis=0), seed=args.seed)
        by_target = {f.target: f for f in features}
        replaced = []
        for target in targets:
            feature = by_target[target.name]
            assert tuple(feature.network_metabolites) == tuple(target.metabolites), target.name
            random = tuple(feature.random_metabolites)
            assert len(random) == len(target.metabolites) and not set(random) & set(target.metabolites)
            assert target.name not in random
            replaced.append(dataclasses.replace(target, metabolites=random))
        provenance['r1_null'] = {'seed': args.seed, 'matching': 'network degree and assay coverage (archived function)',
                                 'sets': {t.name: list(t.metabolites) for t in replaced}}
        return metabolites, signatures, lineages, replaced, archived, provenance

    ce.load_inputs = null_inputs
    ce.MODELS = ('direct_neighbor_ridge',)
    ce.primary_inference = lambda groups: {'not_applicable': 'R1 null run; paired with accepted run afterwards'}
    output = ROOT / f'runs/r1-ccle-null-s{args.seed}'
    ns = argparse.Namespace(release=ROOT / 'work/release', output=output,
                            private_output=ROOT / 'work/r1-ccle' / output.name, max_targets=None)
    with threadpool_limits(limits=1):
        manifest = ce.execute(ns)
    manifest.update(post_review_r1=True, r1_seed=args.seed, wrapper_sha256=ce.sha256(Path(__file__)), amendment_sha256=expected)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, default=str) + '\n')
    print(json.dumps({'seed': args.seed, 'elapsed': manifest['elapsed_seconds']}))


if __name__ == '__main__':
    sys.exit(main())
