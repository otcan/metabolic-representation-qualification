# Supplementary information


This supplement accompanies the manuscript "Matched nulls and compact baselines qualify biochemical representations for metabolite reconstruction". All model outcomes, including negative controls and implementation failures, are retained. Primary results use only the accepted human revision-2 and full CCLE runs.


## S1. Cohorts, masks and independent units

ST002081 uses 1,539 assay records from 112 repository participant identifiers after removing 104 QC/missing-identifier rows. The final Hornburg et al. 2023 publication independently reports 1,539 samples, 112 participants and 104 QC samples. The deposit narrative says 1,546/109; its history is not explained by the available records. Repeated visits remain together. ST000818 provides 450 unique sample identifiers and 15 population categories and is described by its source as 450 individuals; distinct donor identity was not independently verified. CCLE aligns 913 lines but evaluates 876 lines in 18 retained lineages for every one of 60 targets. Each target has two predictions per line across two outer repeats, giving 105,120 prediction rows per model; these are not 105,120 independent cell lines.

The human primary panels contain 493 and 255 complete lipid labels. Masks are family-stratified and disjoint. The human structural representation has 95 and 81 descriptors before visible-mask restriction. Representation rules are refit independently within each cohort; no frozen ST002081 model is transferred to ST000818. CCLE uses 76 mapped metabolites and 317 direct-reaction candidate rows regenerated from Human-GEM v2.0.0. Each target is excluded from its own inputs. Its compact neighbor panel contains 1–19 metabolites, median 3; correlation selection uses the same target-specific prediction-time count while inspecting 75 candidate inputs during training.

Ordinary rows are equally weighted for fitting. Reported human evaluation first averages hidden-target errors within each sample/mask, then masks within samples, samples within participants, and finally participants equally; ST000818 uses population categories at the final level. CCLE averages repeated/cell-line losses within each target/lineage, then available lineages and fixed targets equally before taking a square root. Biological-group bootstrap intervals condition on fitted models and the fixed target panel. The inferential claim does not include refitting variability or unidentified future populations.


## S2. Complete primary scorecards


### ST002081

| Model | Primary RMSE | Row-weighted RMSE |
| --- | --- | --- |
| all visible ridge | 0.1780 | 0.1747 |
| degree preserving null | 0.4192 | 0.4096 |
| descriptor local svd | 0.2434 | 0.2389 |
| family median | 0.6680 | 0.6503 |
| pca matched dimension | 0.1964 | 0.1929 |
| population mean | 1.0652 | 1.0129 |
| structural median | 0.3168 | 0.3091 |


### ST000818

| Model | Primary RMSE | Row-weighted RMSE |
| --- | --- | --- |
| all visible ridge | 0.8491 | 0.8457 |
| degree preserving null | 1.8030 | 1.7873 |
| descriptor local svd | 0.9574 | 0.9543 |
| family median | 1.8869 | 1.8714 |
| pca matched dimension | 0.8394 | 0.8376 |
| population mean | 2.0130 | 1.9983 |
| structural median | 1.2267 | 1.2201 |


### CCLE

| Model | Primary RMSE | Row-weighted RMSE |
| --- | --- | --- |
| all other metabolites ridge | 0.6648 | 0.7014 |
| correlation selected ridge | 0.7315 | 0.7684 |
| direct neighbor ridge | 0.8239 | 0.8696 |
| global pca ridge | 0.8090 | 0.8412 |
| network additive ridge | 0.8117 | 0.8639 |
| network interaction ridge | 0.8170 | 0.8748 |
| population mean | 0.9865 | 1.0666 |


## S3. Prespecified primary contrasts

Positive improvement is statistical-reference RMSE minus mechanism-representation RMSE. Negative results favor the reference. All five contrasts were defined before extension outcomes. Descriptive 95% intervals and 99% per-contrast intervals are retained in the source CSV. The latter target nominal 95% Bonferroni familywise coverage across five contrasts, subject to the conditional bootstrap assumptions. The table reports 99% per-contrast limits. Main Figure 3 uses thick 95% and thin 99% per-contrast intervals. All five two-sided Monte Carlo sign-flip tests have raw p = 0.0000999900 and Holm-adjusted p = 0.0004999500 across the five tests. The raw probabilities reach the 1/10,001 simulation-resolution floor, not an arbitrarily small exact p value. Sign flips assume exchangeability of paired group-effect signs under the null. Overlapping cross-validation training sets can induce dependence across held-out groups that these procedures do not fully represent. Inference remains conditional on the fitted models and fixed target panel, without full-pipeline refitting.

| Dataset | Reference | Improvement | 99% lower | 99% upper |
| --- | --- | --- | --- | --- |
| st002081 | pca matched dimension | -0.1204 | -0.1278 | -0.1140 |
| st002081 | descriptor local svd | -0.0733 | -0.0789 | -0.0676 |
| st000818 | pca matched dimension | -0.3873 | -0.7902 | -0.0712 |
| st000818 | descriptor local svd | -0.2693 | -0.5388 | -0.0494 |
| ccle | correlation selected ridge | -0.0924 | -0.1073 | -0.0807 |


## S4. Information and fitting budgets

Measured inputs, output dimension, learned transform loadings, ridge coefficients and tuning budgets are separate. Human models generally see the same visible assay panel; 95 descriptors do not mean a 95-analyte panel. PCA has learned loadings not required by the fixed median membership. Below, transform loadings exclude common centering/scaling parameters and intercepts; total parameter equality is not claimed. Every fitted ridge model uses the same four-alpha grid and three grouped inner folds. Both PC representations are training-standardized before ridge.


### ST002081 budgets

| Model | Visible inputs | Dimension | Median loadings |
| --- | --- | --- | --- |
| all visible ridge | 390–397 | 390–397 | 0 |
| degree preserving null | 390–397 | 95–95 | 0 |
| descriptor local svd | 390–397 | 95–95 | 2798 |
| family median | 390–397 | 9–9 | 0 |
| pca matched dimension | 390–397 | 95–95 | 37525 |
| structural median | 390–397 | 95–95 | 0 |


### ST000818 budgets

| Model | Visible inputs | Dimension | Median loadings |
| --- | --- | --- | --- |
| all visible ridge | 202–208 | 202–208 | 0 |
| degree preserving null | 202–208 | 81–81 | 0 |
| descriptor local svd | 202–208 | 81–81 | 917 |
| family median | 202–208 | 6–6 | 0 |
| pca matched dimension | 202–208 | 81–81 | 16443 |
| structural median | 202–208 | 81–81 | 0 |


### CCLE budgets

| Model | Median metabolites | Median genes | Median dimension | Selection pool |
| --- | --- | --- | --- | --- |
| all other metabolites ridge | 75.0 | 0.0 | 75.0 | 0.0 |
| correlation selected ridge | 3.0 | 0.0 | 3.0 | 75.0 |
| direct neighbor ridge | 3.0 | 0.0 | 3.0 | 0.0 |
| global pca ridge | 75.0 | 0.0 | 3.0 | 0.0 |
| network additive ridge | 3.0 | 5.0 | 8.0 | 0.0 |
| network interaction ridge | 3.0 | 5.0 | 13.0 | 0.0 |
| population mean | 0.0 | 0.0 | 0.0 | 0.0 |

Correlation-selected panels use 75 candidate metabolites in training and 1–19 at prediction. This comparison matches deployment metabolite count, not development assay cost. The direct-neighbor map instead uses curated network information. PCA sees all 75 non-target metabolites even when only a few components are retained. No assay-cost, user-interpretability or clinical-benefit experiment was performed.


## S5. Full human sensitivity scorecards

These sensitivities are descriptive, not additional primary discoveries. Training-only missingness starts from all eligible assay labels, retains visible inputs with ≥80% training observations, and keeps only targets complete and variable in the applicable training partition. Inner target/feature rules use inner training only. Test errors include observed targets only. Changing the eligible universe changes the task; differences across modes are not effects of a model change on identical targets. In ST000818 the missingness version retains the same 255-feature panel and is numerically identical to primary, so it provides no additional missingness stress test. Resolution sensitivity removes unsupported individual-chain memberships from sum-composition-only labels while retaining reported family and total composition. It is a conservative name-parser check, not expert reannotation.


### ST002081 — missingness

Schema: 841 features; 135 descriptors. Retained targets per outer mask/fold: 96–109. Full fold exclusions, changing visible panels, observed-target denominators and budgets are retained in run CSVs.

| Model | Primary RMSE |
| --- | --- |
| all visible ridge | 0.1860 |
| degree preserving null | 0.3995 |
| descriptor local svd | 0.2409 |
| family median | 0.6599 |
| pca matched dimension | 0.2137 |
| population mean | 1.0650 |
| structural median | 0.3100 |


### ST002081 — resolution

Schema: 493 features; 95 descriptors. Retained targets per outer mask/fold: 96–103. Full fold exclusions, changing visible panels, observed-target denominators and budgets are retained in run CSVs.

| Model | Primary RMSE |
| --- | --- |
| all visible ridge | 0.1780 |
| degree preserving null | 0.4153 |
| descriptor local svd | 0.2433 |
| family median | 0.6680 |
| pca matched dimension | 0.1964 |
| population mean | 1.0652 |
| structural median | 0.3163 |


### ST000818 — missingness

Schema: 255 features; 81 descriptors. Retained targets per outer mask/fold: 47–53. Full fold exclusions, changing visible panels, observed-target denominators and budgets are retained in run CSVs.

| Model | Primary RMSE |
| --- | --- |
| all visible ridge | 0.8491 |
| degree preserving null | 1.8030 |
| descriptor local svd | 0.9574 |
| family median | 1.8869 |
| pca matched dimension | 0.8394 |
| population mean | 2.0130 |
| structural median | 1.2267 |


### ST000818 — resolution

Schema: 255 features; 67 descriptors. Retained targets per outer mask/fold: 47–53. Full fold exclusions, changing visible panels, observed-target denominators and budgets are retained in run CSVs.

| Model | Primary RMSE |
| --- | --- |
| all visible ridge | 0.8491 |
| degree preserving null | 1.7860 |
| descriptor local svd | 0.9619 |
| family median | 1.8869 |
| pca matched dimension | 0.8630 |
| population mean | 2.0130 |
| structural median | 1.2347 |


## S6. Outcome-aware secondary mean aggregator

An AI-assisted supervisory review requested the inexpensive mean aggregator proposed in the initial literature audit. This amendment was recorded after the five primary outcomes were viewed; it adds no primary test. Arithmetic means use exactly the same visible descriptor memberships and train-only standardization, nested tuning and outer splits as the median/SVD comparison. All seven primary models are rerun alongside it. One startup failed before predictions because a read-only NumPy view was modified in place; the failure and repair are retained.


### ST002081 — all secondary-run models

| Model | Primary RMSE |
| --- | --- |
| all visible ridge | 0.1780 |
| degree preserving null | 0.4192 |
| descriptor local svd | 0.2434 |
| descriptor mean | 0.2425 |
| family median | 0.6680 |
| pca matched dimension | 0.1964 |
| population mean | 1.0652 |
| structural median | 0.3168 |


### ST000818 — all secondary-run models

| Model | Primary RMSE |
| --- | --- |
| all visible ridge | 0.8491 |
| degree preserving null | 1.8030 |
| descriptor local svd | 0.9574 |
| descriptor mean | 0.9443 |
| family median | 1.8869 |
| pca matched dimension | 0.8394 |
| population mean | 2.0130 |
| structural median | 1.2267 |


## S7. Reproduction, retained nulls and sensitivity grids

Fourteen released pipeline/report stages completed independently in the new environment. 51 of 62 declared outputs are byte-identical. All 14 manifest decisions agree. The remaining 11 mismatches include ST002081 all-visible ridge numerics and their downstream tables, report and figure consequences. Largest coarse summary RMSE difference is 0.000002997 SD, largest target RMSE difference approximately 0.000475 SD; two sample-level priority rankings change precision by 1/3. No tolerance was used to call these files byte-identical. Exact changed-value counts, maximum absolute/relative differences, interval changes and gate comparisons are in the audit CSVs. The cause is not established by package-version identity. The released source bytes match the public ZIP, but three historical implementation digests cannot be recovered from available copies.

| Stage | Outputs | Byte-identical | Decision agrees |
| --- | --- | --- | --- |
| pathway-score-st002081 | 7 | 2 | True |
| pathway-score-st002081-structural | 6 | 3 | True |
| pathway-score-st000818-replication | 6 | 6 | True |
| pathway-score-ccle | 5 | 5 | True |
| pathway-score-st002081-structural-null-sensitivity | 2 | 2 | True |
| pathway-score-ccle-null-ensemble | 3 | 3 | True |
| pathway-score-ccle-property-matched-null | 3 | 3 | True |
| pathway-score-human-sensitivity | 3 | 3 | True |
| pathway-score-human-graph-mixing | 3 | 3 | True |
| pathway-score-ccle-sensitivity | 3 | 3 | True |
| pathway-score-ccle-reaction-cluster | 4 | 4 | True |
| pathway-score-mapping-supplement | 6 | 6 | True |
| pathway-score-publication-figures | 7 | 5 | True |
| factorized-pathway-publication | 4 | 3 | True |

Complete archived and regenerated null grids are included in the public code archive under evidence/baseline and evidence/new: 20 human structural nulls, 20 CCLE dimension-matched draws, 20 CCLE degree/coverage-matched draws, and ST000818's 20 nulls. Nine human sensitivity settings per cohort, ten CCLE settings, graph-mixing diagnostics, mapping ledgers and reaction-subsystem robustness tables are retained. These grids were originally adaptive; passing all sampled null realizations is not an exact graph-randomization p value or proof of uniform graph sampling. Archived CCLE target-bootstrap intervals remain a distinct estimand from the new biological-lineage intervals.


## S8. Audit and version history

AUD-01–14 dispositions are recorded in readiness/audit-resolution.csv. Repairs in the new analysis include common ST000818 splits, one baseline per observation, group-level uncertainty, corrected mean-imputation Methods, train-only missingness rules, explicit skill-statistic terminology, saved losses/splits and input preflight. The initial human extension accidentally weighted inner folds rather than groups, capped PCA by a rank upper bound, inherited outer target eligibility in inner validation, and aggregated missing masks before samples. Those outputs are preserved but superseded. Revision 2 fixes all four and passes nine targeted tests; CCLE passes ten tests. Independent arithmetic review agrees within 4.44e-16 and confirms all prediction and split identities. The CCLE numerical reviewer also wrote its implementation; that role is disclosed. A separate AI-assisted verification pass is likewise disclosed; it is not independent human peer review.


## S9. Interpretation and rights

Chemical or reaction membership remains inspectable, but interpretability benefit was not measured. Success against matched random controls does not establish greater prediction accuracy, pathway causality, physiological flux, treatment response, rejuvenation or clinical value. Different cohorts are never pooled as if jointly measured; the human lipid cohorts do not provide same-person multimodal validation in this work. Genetic/topology, constraint and perturbational artifacts from the older package remain supporting/exploratory material and are not new independent confirmation here.

Both Workbench study APIs report CC BY 4.0; Human-GEM v2.0.0 is CC BY 4.0. Raw CCLE files are not redistributed and should be obtained from the original release [12]. The existing software archive is Apache-2.0 with separate content licensing. MIRTH was not executed or adapted because posted permissions are unresolved. Participant-linked losses and human split maps are not redistributed. Authorship, funding, competing-interest and ethics statements appear in the main manuscript.


## S10. Machine-readable evidence index

The public code archive includes results/ CSVs, figure source data, exact run manifests, code, configuration snapshots, frozen environment versions, defect dispositions and reproducibility instructions. Participant-level records and raw matrices are excluded. Detailed tuning/exclusion/budget grids are supplied electronically rather than rendered as tens of thousands of PDF rows. Captions and main tables link to the same result sources; no hand-entered alternative scorecard is used.


## S11. Qualification ladder source values

Main Figure 1 uses current estimators throughout. Rungs are primary equal-group or equal-lineage RMSEs; matched nulls are expected values over 20 realizations (Section S12). Compact steps are the locked primary contrasts. Shares are descriptive point-estimate partitions of the training-mean-to-compact gap on the RMSE and MSE scales and have no intervals. The archived CCLE ensemble row is listed for completeness only; it used the released estimator and target-level resampling.

| Dataset | Rung | Construction | Primary RMSE |
| --- | --- | --- | --- |
| ST002081 | Training mean | no structure | 1.0652 |
| ST002081 | Matched null | same shape, rewired membership | 0.4168 |
| ST002081 | Biochemical descriptors | declared membership, median | 0.3168 |
| ST002081 | Compact statistics | PCA, same dimension | 0.1964 |
| ST002081 | Full-panel ridge | all visible inputs | 0.1780 |
| ST000818 | Training mean | no structure | 2.0130 |
| ST000818 | Matched null | same shape, rewired membership | 1.7901 |
| ST000818 | Biochemical descriptors | declared membership, median | 1.2267 |
| ST000818 | Compact statistics | PCA, same dimension | 0.8394 |
| ST000818 | Full-panel ridge | all visible inputs | 0.8491 |
| CCLE | Training mean | no structure | 0.9865 |
| CCLE | Matched null | property-matched random neighbours | 0.9238 |
| CCLE | Reaction neighbours | declared neighbours | 0.8239 |
| CCLE | Compact statistics | correlation-selected, same count | 0.7315 |
| CCLE | Full-panel ridge | all other metabolites | 0.6648 |

| Dataset | Step | Estimate | 95% lower | 95% upper | Estimator |
| --- | --- | --- | --- | --- | --- |
| ST002081 | biochemistry vs matched null | 0.1000 | 0.0949 | 0.1053 | expected over 20 null realizations; current estimator; biological-group bootstrap |
| ST002081 | compact vs biochemistry | 0.1204 | 0.1153 | 0.1258 | locked primary contrast; biological-group bootstrap |
| ST002081 | matched null share rmse | 0.7464 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| ST002081 | biochemistry share rmse | 0.1151 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| ST002081 | compact share rmse | 0.1385 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| ST002081 | matched null share mse | 0.8767 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| ST002081 | biochemistry share mse | 0.0669 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| ST002081 | compact share mse | 0.0564 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| ST000818 | biochemistry vs matched null | 0.5634 | 0.0463 | 1.0098 | expected over 20 null realizations; current estimator; biological-group bootstrap |
| ST000818 | compact vs biochemistry | 0.3873 | 0.0748 | 0.6872 | locked primary contrast; biological-group bootstrap |
| ST000818 | matched null share rmse | 0.1900 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| ST000818 | biochemistry share rmse | 0.4800 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| ST000818 | compact share rmse | 0.3300 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| ST000818 | matched null share mse | 0.2533 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| ST000818 | biochemistry share mse | 0.5077 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| ST000818 | compact share mse | 0.2390 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| CCLE | biochemistry vs matched null | 0.1000 | 0.0846 | 0.1197 | expected over 20 null realizations; current estimator; biological-group bootstrap |
| CCLE | compact vs biochemistry | 0.0924 | 0.0830 | 0.1034 | locked primary contrast; biological-group bootstrap |
| CCLE | matched null share rmse | 0.2457 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| CCLE | biochemistry share rmse | 0.3920 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| CCLE | compact share rmse | 0.3623 | — | — | descriptive share of training-mean-to-compact gap (RMSE scale) |
| CCLE | matched null share mse | 0.2732 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| CCLE | biochemistry share mse | 0.3988 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| CCLE | compact share mse | 0.3280 | — | — | descriptive share of training-mean-to-compact gap (MSE scale) |
| CCLE | archived biochemistry vs matched null | 0.1374 | 0.0971 | 0.1807 | archived property-matched ensemble; released estimator; target bootstrap (supplement only) |


## S12. Post-review analyses (outcome-aware)

Both analyses were frozen in readiness/post-review-r1-amendment.md before their outcomes were computed and reuse the accepted code, splits and tuning. They do not alter the five primary contrasts.


### Membership by aggregation (human cohorts)

Membership effect is expected-null RMSE minus declared RMSE over 20 degree-preserving null realizations; realization 0 reproduces the primary null exactly.

| Dataset | Rule | Declared | Expected null | Effect | 95% interval |
| --- | --- | --- | --- | --- | --- |
| ST002081 | median | 0.3168 | 0.4168 | 0.1000 | 0.095 to 0.105 |
| ST002081 | mean | 0.2425 | 0.2417 | −0.0009 | −0.003 to 0.001 |
| ST002081 | local svd | 0.2434 | 0.2789 | 0.0355 | 0.033 to 0.038 |
| ST000818 | median | 1.2267 | 1.7901 | 0.5634 | 0.046 to 1.010 |
| ST000818 | mean | 0.9443 | 1.0592 | 0.1149 | 0.012 to 0.216 |
| ST000818 | local svd | 0.9574 | 1.3620 | 0.4046 | 0.019 to 0.764 |

| Dataset | Rule | Positive effects, n/20 | 95% intervals above zero, n/20 | Smallest effect | Largest effect |
| --- | --- | --- | --- | --- | --- |
| ST002081 | median | 20/20 | 20/20 | 0.0956 | 0.1050 |
| ST002081 | mean | 5/20 | 0/20 | −0.0025 | 0.0009 |
| ST002081 | local svd | 20/20 | 20/20 | 0.0304 | 0.0409 |
| ST000818 | median | 20/20 | 20/20 | 0.4488 | 0.5840 |
| ST000818 | mean | 20/20 | 20/20 | 0.0341 | 0.1717 |
| ST000818 | local svd | 20/20 | 20/20 | 0.1279 | 0.5898 |


### CCLE matched null under the current estimator

Declared direct neighbours: 0.8239; expected property-matched null over 20 seeds: 0.9238; effect 0.1000 (lineage-bootstrap 95% interval 0.0846 to 0.1197). All 20 seeds had intervals above zero. The table below reports seed-specific results under the current estimator. The archived ensemble, reported separately in Section S11, used the released estimator and target-level resampling and is not combined with the current ladder.

| Seed | Effect | 95% lower | 95% upper |
| --- | --- | --- | --- |
| 20262100 | 0.0980 | 0.0824 | 0.1177 |
| 20262101 | 0.0983 | 0.0825 | 0.1195 |
| 20262102 | 0.0918 | 0.0778 | 0.1091 |
| 20262103 | 0.1055 | 0.0898 | 0.1249 |
| 20262104 | 0.1036 | 0.0878 | 0.1238 |
| 20262105 | 0.1048 | 0.0883 | 0.1261 |
| 20262106 | 0.0906 | 0.0758 | 0.1094 |
| 20262107 | 0.1057 | 0.0893 | 0.1257 |
| 20262108 | 0.0980 | 0.0827 | 0.1173 |
| 20262109 | 0.0893 | 0.0748 | 0.1082 |
| 20262110 | 0.1070 | 0.0901 | 0.1305 |
| 20262111 | 0.1123 | 0.0957 | 0.1338 |
| 20262112 | 0.1019 | 0.0854 | 0.1225 |
| 20262113 | 0.0803 | 0.0670 | 0.0959 |
| 20262114 | 0.1066 | 0.0890 | 0.1299 |
| 20262115 | 0.0946 | 0.0785 | 0.1150 |
| 20262116 | 0.1008 | 0.0872 | 0.1172 |
| 20262117 | 0.1076 | 0.0896 | 0.1308 |
| 20262118 | 0.1030 | 0.0875 | 0.1234 |
| 20262119 | 0.0994 | 0.0850 | 0.1181 |


## S13. Availability inventory

| Material | Status | Location |
| --- | --- | --- |
| Code, tests, figure scripts, frozen amendments | Public | code archive: scripts/, tests/, readiness/ |
| Aggregate model metrics, contrasts, budgets, ladder and post-review summaries | Public | results/ |
| Per-run summaries, tuning and budget grids, null grids (archived and regenerated) | Public | evidence/new, evidence/baseline, evidence/archived-ccle-property-matched-null |
| Raw Metabolomics Workbench and CCLE matrices | Not redistributed; regenerable | original repositories (Data availability) |
| Individual predictions, participant-linked losses and split maps | Withheld | regenerable locally from code and public source data |
