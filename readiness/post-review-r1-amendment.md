# Post-review amendment R1 — membership × aggregation and current-estimator CCLE null

**Frozen:** 1 October 2026, before any R1 outcome was computed.
**Status:** post-review, outcome-aware secondary analyses requested by the author's review of preprint v1.1.
They do not alter the five primary contrasts, their estimands or their multiplicity family.

## R1-H: declared versus rewired membership crossed with aggregation (human cohorts)

- Data, masks, outer and inner splits, tuning grid, standardization and loss definitions are exactly
  those of the accepted primary runs (`scripts/human_extension.py`, primary mode).
- Aggregations on identical memberships: median (existing `structural_median`), arithmetic mean
  (existing secondary `descriptor_mean` definition) and descriptor-local first-component SVD
  (existing `descriptor_local_svd`).
- Null memberships: degree-preserving rewiring of the visible, training-eligible lipid–descriptor
  graph inside every fit (existing `degree_preserving_descriptor_null`, 10 swaps per edge). Realization
  `k = 0…19` uses seed `primary_null_seed + mask + 1000·k`; `k = 0` reproduces the primary null.
  The same null graph is used for all three aggregations within a fit.
- Estimand per aggregation X: equal-group RMSE(null_X) − RMSE(declared_X); positive favours declared
  membership. Reported per realization and for the expected null (group MSE averaged over the 20
  realizations, then paired with declared_X).
- Uncertainty: paired biological-group bootstrap (10,000 draws, seed 20260921) as in the primary code.
- Descriptive only; no new significance family.

## R1-C: CCLE matched null under the current estimator

- Null neighbour sets: the archived property-matched assignment
  (`propensity_matched_target_feature_sets`, network degree and assay coverage, no outcome data),
  seeds 20262100–20262119 as in the archived ensemble; metabolite sets only, because the current
  direct-neighbour model uses metabolite inputs only.
- Predictor, eligibility, outer splits (seed 20260830), inner tuning and equal-lineage RMSE are those of
  the accepted `direct_neighbor_ridge`.
- Estimand: equal-lineage RMSE(null) − RMSE(direct neighbours), per seed and for the expected null
  (target-lineage MSE averaged over seeds); positive favours declared reaction neighbours.
- Uncertainty: lineage bootstrap preserving the fixed target panel (10,000 draws, seed 20260921), as in
  the current primary CCLE inference.
- This replaces the archived-estimator CCLE step in the qualification-ladder figure; the archived result is
  retained in the supplement.
