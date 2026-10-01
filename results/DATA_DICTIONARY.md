# Result field definitions

`primary_rmse` is a dataset-specific training-standardized reconstruction error.
For humans it is the square root of equally weighted biological-group mean
squared error after averaging masks within samples and samples within groups.
For CCLE it is the square root of mean fixed-target, mean available-lineage MSE,
with cells and repeat losses pooled inside each target/lineage. It differs from
the archived CCLE mean of target-specific RMSE values. Do not combine datasets.

`improvement` is reference RMSE minus mechanism-model RMSE; negative values favor
the statistical reference. `ci95_*` are ordinary paired percentile 95% intervals.
Legacy fields `simultaneous99_lower` and `simultaneous99_upper` actually contain
**99% per-contrast percentile intervals**. For the five predeclared primary
contrasts, allocating 1% error to each targets **nominal 95% familywise coverage**
by Bonferroni. They are NOT 99% simultaneous familywise intervals. This correction
clarifies interpretation without altering hashed numeric files or the frozen
protocol. Other exported comparisons with the same column names have descriptive
99% intervals and do not inherit familywise protection for an unspecified family.

`p_raw` is a two-sided paired biological-group sign-flip Monte Carlo probability
with plus-one correction. All five primary values are the resolution floor
1/10,001, not independently finely measured tail probabilities. `p_holm` applies
Holm to the five-test primary family, yielding approximately 0.00049995 each.
Shared training folds and sign-exchangeability assumptions limit formal inference.
Bootstrap intervals condition on fitted predictions and fixed targets; they do not
refit the pipeline or guarantee coverage for future populations.

`groups` means112 participant IDs for ST002081,15 population categories for
ST000818 and18 cancer lineages for CCLE. CCLE has913 aligned source lines and876
evaluated lines. Each model has105,120 target/repeat prediction rows over the60
targets; those rows are not independent lines. ST000818's450 individuals are
source-reported; a separate donor mapping is unavailable.

`skill_vs_training_mean` is1−SSE/sum(z²), where z is standardized using each
training fold's target moments. It is not test-mean-centered pooled R².

Budget fields distinguish visible prediction-time assays, raw transcript genes,
output coordinates, transform loadings and regression coefficients. Human
`learned_loadings_median` excludes mean/SD estimates and intercepts; it is not a
total model-parameter count. CCLE `transform_learned_parameters` additionally
counts the code's standardization moments and PCA loadings. Do not compare these
two differently defined columns as a single cross-dataset parameter budget.
Correlation selection sees75 non-target metabolites in training; its1–19 selected
prediction-time metabolites match the direct-neighbor count. PCA sees all75.

Human sensitivity modes may change the eligible feature/target universe. Scores
are compared within the same mode, never as if a cross-mode raw difference were
solely an algorithm effect. The outcome-aware mean-aggregation table is secondary
and outside the five primary tests. Pilot, superseded and failed runs are excluded
from accepted consolidated tables, but preserved in the workspace audit trail.
