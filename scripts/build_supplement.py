"""Generate supplementary tables directly from accepted result CSVs."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'manuscript'; OUT.mkdir(exist_ok=True)

def table(frame,digits=4):
    def format_value(value):
        if isinstance(value,float): return f'{value:.{digits}f}'
        return str(value).replace('_',' ').replace('|','/')
    columns=list(frame.columns)
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    for row in frame.itertuples(index=False,name=None): lines.append('| '+' | '.join(format_value(x) for x in row)+' |')
    return '\n'.join(lines)

metrics=pd.read_csv(ROOT/'results/all-model-metrics.csv')
contrasts=pd.read_csv(ROOT/'results/primary-comparisons.csv')
baseline=pd.read_csv(ROOT/'receipts/m0-all-stage-summary.csv')
parts=['# Supplementary information',
       '\nThis supplement accompanies the manuscript "Matched nulls and compact baselines qualify biochemical representations for metabolite reconstruction". All model outcomes, including negative controls and implementation failures, are retained. Primary results use only the accepted human revision-2 and full CCLE runs.',
       '\n## S1. Cohorts, masks and independent units',
       '''ST002081 uses 1,539 assay records from 112 repository participant identifiers after removing 104 QC/missing-identifier rows. The final Hornburg et al. 2023 publication independently reports 1,539 samples, 112 participants and 104 QC samples. The deposit narrative says 1,546/109; its history is not explained by the available records. Repeated visits remain together. ST000818 provides 450 unique sample identifiers and 15 population categories and is described by its source as 450 individuals; distinct donor identity was not independently verified. CCLE aligns 913 lines but evaluates 876 lines in 18 retained lineages for every one of 60 targets. Each target has two predictions per line across two outer repeats, giving 105,120 prediction rows per model; these are not 105,120 independent cell lines.

The human primary panels contain 493 and 255 complete lipid labels. Masks are family-stratified and disjoint. The human structural representation has 95 and 81 descriptors before visible-mask restriction. Representation rules are refit independently within each cohort; no frozen ST002081 model is transferred to ST000818. CCLE uses 76 mapped metabolites and 317 direct-reaction candidate rows regenerated from Human-GEM v2.0.0. Each target is excluded from its own inputs. Its compact neighbor panel contains 1–19 metabolites, median 3; correlation selection uses the same target-specific prediction-time count while inspecting 75 candidate inputs during training.

Ordinary rows are equally weighted for fitting. Reported human evaluation first averages hidden-target errors within each sample/mask, then masks within samples, samples within participants, and finally participants equally; ST000818 uses population categories at the final level. CCLE averages repeated/cell-line losses within each target/lineage, then available lineages and fixed targets equally before taking a square root. Biological-group bootstrap intervals condition on fitted models and the fixed target panel. The inferential claim does not include refitting variability or unidentified future populations.''',
       '\n## S2. Complete primary scorecards']
for dataset in ['st002081','st000818','ccle']:
    f=metrics.loc[metrics.dataset.eq(dataset)&metrics['mode'].eq('primary'),['model','primary_rmse','row_weighted_rmse']].copy()
    f.columns=['Model','Primary RMSE','Row-weighted RMSE']
    parts.extend([f'\n### {dataset.upper()}',table(f)])
parts.extend(['\n## S3. Prespecified primary contrasts',
              'Positive improvement is statistical-reference RMSE minus mechanism-representation RMSE. Negative results favor the reference. All five contrasts were defined before extension outcomes. Descriptive 95% intervals and 99% per-contrast intervals are retained in the source CSV. The latter target nominal 95% Bonferroni familywise coverage across five contrasts, subject to the conditional bootstrap assumptions. The table reports 99% per-contrast limits. Main Figure 3 uses thick 95% and thin 99% per-contrast intervals. All five two-sided Monte Carlo sign-flip tests have raw p = 0.0000999900 and Holm-adjusted p = 0.0004999500 across the five tests. The raw probabilities reach the 1/10,001 simulation-resolution floor, not an arbitrarily small exact p value. Sign flips assume exchangeability of paired group-effect signs under the null. Overlapping cross-validation training sets can induce dependence across held-out groups that these procedures do not fully represent. Inference remains conditional on the fitted models and fixed target panel, without full-pipeline refitting.',
              table(contrasts[['dataset','reference','improvement','simultaneous99_lower','simultaneous99_upper']].rename(columns={'dataset':'Dataset','reference':'Reference','improvement':'Improvement','simultaneous99_lower':'99% lower','simultaneous99_upper':'99% upper'})),
              '\n## S4. Information and fitting budgets',
              'Measured inputs, output dimension, learned transform loadings, ridge coefficients and tuning budgets are separate. Human models generally see the same visible assay panel; 95 descriptors do not mean a 95-analyte panel. PCA has learned loadings not required by the fixed median membership. Below, transform loadings exclude common centering/scaling parameters and intercepts; total parameter equality is not claimed. Every fitted ridge model uses the same four-alpha grid and three grouped inner folds. Both PC representations are training-standardized before ridge.'])
budget=pd.read_csv(ROOT/'results/human-information-budgets.csv')
for dataset in ['st002081','st000818']:
    rows=[]
    for r in budget.loc[budget.dataset.eq(dataset)&budget['mode'].eq('primary')].itertuples():
        rows.append({'Model':r.model,'Visible inputs':f'{int(r.measured_inputs_min)}–{int(r.measured_inputs_max)}','Dimension':f'{int(r.dimension_min)}–{int(r.dimension_max)}','Median loadings':int(r.learned_loadings_median)})
    parts.extend([f'\n### {dataset.upper()} budgets',table(pd.DataFrame(rows))])
cb=pd.read_csv(ROOT/'results/ccle-information-budgets.csv')
parts.extend(['\n### CCLE budgets',table(cb[['model','raw_metabolites_median','raw_transcript_genes_median','representation_dimension_median','selection_candidate_metabolites_median']].rename(columns={'model':'Model','raw_metabolites_median':'Median metabolites','raw_transcript_genes_median':'Median genes','representation_dimension_median':'Median dimension','selection_candidate_metabolites_median':'Selection pool'}),1),
              'Correlation-selected panels use 75 candidate metabolites in training and 1–19 at prediction. This comparison matches deployment metabolite count, not development assay cost. The direct-neighbor map instead uses curated network information. PCA sees all 75 non-target metabolites even when only a few components are retained. No assay-cost, user-interpretability or clinical-benefit experiment was performed.',
              '\n## S5. Full human sensitivity scorecards',
              'These sensitivities are descriptive, not additional primary discoveries. Training-only missingness starts from all eligible assay labels, retains visible inputs with ≥80% training observations, and keeps only targets complete and variable in the applicable training partition. Inner target/feature rules use inner training only. Test errors include observed targets only. Changing the eligible universe changes the task; differences across modes are not effects of a model change on identical targets. In ST000818 the missingness version retains the same 255-feature panel and is numerically identical to primary, so it provides no additional missingness stress test. Resolution sensitivity removes unsupported individual-chain memberships from sum-composition-only labels while retaining reported family and total composition. It is a conservative name-parser check, not expert reannotation.'])
for dataset in ['st002081','st000818']:
    for mode in ['missingness','resolution']:
        path=ROOT/f'runs/m2-human-r2-{dataset}-{mode}'
        manifest=json.loads((path/'manifest.json').read_text())
        exclusions=pd.read_csv(path/'exclusions.csv')
        data=metrics.loc[metrics.dataset.eq(dataset)&metrics['mode'].eq(mode),['model','primary_rmse']].copy()
        data.columns=['Model','Primary RMSE']
        parts.extend([f'\n### {dataset.upper()} — {mode}',
                      f"Schema: {manifest['features']} features; {manifest['descriptors']} descriptors. Retained targets per outer mask/fold: {int(exclusions.targets_retained.min())}–{int(exclusions.targets_retained.max())}. Full fold exclusions, changing visible panels, observed-target denominators and budgets are retained in run CSVs.",table(data)])
parts.extend(['\n## S6. Outcome-aware secondary mean aggregator',
              'An AI-assisted supervisory review requested the inexpensive mean aggregator proposed in the initial literature audit. This amendment was recorded after the five primary outcomes were viewed; it adds no primary test. Arithmetic means use exactly the same visible descriptor memberships and train-only standardization, nested tuning and outer splits as the median/SVD comparison. All seven primary models are rerun alongside it. One startup failed before predictions because a read-only NumPy view was modified in place; the failure and repair are retained.'])
mean_rows=[]
for dataset in ['st002081','st000818']:
    p=ROOT/f'runs/m2-human-mean-secondary-v2-{dataset}'
    m=json.loads((p/'manifest.json').read_text())
    assert m['secondary_outcome_aware'] and not m['pilot']
    t=pd.read_csv(p/'model-metrics.csv'); t.insert(0,'dataset',dataset)
    for record in t.to_dict('records'): mean_rows.append(record)
    show=t[['model','equal_group_rmse_sd']] if 'equal_group_rmse_sd' in t else t[['model','equal_group_rmse']]
    show=show.copy(); show.columns=['Model','Primary RMSE']
    parts.extend([f'\n### {dataset.upper()} — all secondary-run models',table(show)])
pd.DataFrame(mean_rows).to_csv(ROOT/'results/secondary-mean-model-metrics.csv',index=False)
parts.extend(['\n## S7. Reproduction, retained nulls and sensitivity grids',
              'Fourteen released pipeline/report stages completed independently in the new environment. 51 of 62 declared outputs are byte-identical. All 14 manifest decisions agree. The remaining 11 mismatches include ST002081 all-visible ridge numerics and their downstream tables, report and figure consequences. Largest coarse summary RMSE difference is 0.000002997 SD, largest target RMSE difference approximately 0.000475 SD; two sample-level priority rankings change precision by 1/3. No tolerance was used to call these files byte-identical. Exact changed-value counts, maximum absolute/relative differences, interval changes and gate comparisons are in the audit CSVs. The cause is not established by package-version identity. The released source bytes match the public ZIP, but three historical implementation digests cannot be recovered from available copies.',
              table(baseline[['artifact','outputs','byte_identical','decision_matches']].rename(columns={'artifact':'Stage','outputs':'Outputs','byte_identical':'Byte-identical','decision_matches':'Decision agrees'}),0),
              'Complete archived and regenerated null grids are included in the public code archive under evidence/baseline and evidence/new: 20 human structural nulls, 20 CCLE dimension-matched draws, 20 CCLE degree/coverage-matched draws, and ST000818\'s 20 nulls. Nine human sensitivity settings per cohort, ten CCLE settings, graph-mixing diagnostics, mapping ledgers and reaction-subsystem robustness tables are retained. These grids were originally adaptive; passing all sampled null realizations is not an exact graph-randomization p value or proof of uniform graph sampling. Archived CCLE target-bootstrap intervals remain a distinct estimand from the new biological-lineage intervals.',
              '\n## S8. Audit and version history',
              'AUD-01–14 dispositions are recorded in readiness/audit-resolution.csv. Repairs in the new analysis include common ST000818 splits, one baseline per observation, group-level uncertainty, corrected mean-imputation Methods, train-only missingness rules, explicit skill-statistic terminology, saved losses/splits and input preflight. The initial human extension accidentally weighted inner folds rather than groups, capped PCA by a rank upper bound, inherited outer target eligibility in inner validation, and aggregated missing masks before samples. Those outputs are preserved but superseded. Revision 2 fixes all four and passes nine targeted tests; CCLE passes ten tests. Independent arithmetic review agrees within 4.44e-16 and confirms all prediction and split identities. The CCLE numerical reviewer also wrote its implementation; that role is disclosed. A separate AI-assisted verification pass is likewise disclosed; it is not independent human peer review.',
              '\n## S9. Interpretation and rights',
              'Chemical or reaction membership remains inspectable, but interpretability benefit was not measured. Success against matched random controls does not establish greater prediction accuracy, pathway causality, physiological flux, treatment response, rejuvenation or clinical value. Different cohorts are never pooled as if jointly measured; the human lipid cohorts do not provide same-person multimodal validation in this work. Genetic/topology, constraint and perturbational artifacts from the older package remain supporting/exploratory material and are not new independent confirmation here.',
              'Both Workbench study APIs report CC BY 4.0; Human-GEM v2.0.0 is CC BY 4.0. Raw CCLE files are not redistributed and should be obtained from the original release [12]. The existing software archive is Apache-2.0 with separate content licensing. MIRTH was not executed or adapted because posted permissions are unresolved. Participant-linked losses and human split maps are not redistributed. Authorship, funding, competing-interest and ethics statements appear in the main manuscript.',
              '\n## S10. Machine-readable evidence index',
              'The public code archive includes results/ CSVs, figure source data, exact run manifests, code, configuration snapshots, frozen environment versions, defect dispositions and reproducibility instructions. Participant-level records and raw matrices are excluded. Detailed tuning/exclusion/budget grids are supplied electronically rather than rendered as tens of thousands of PDF rows. Captions and main tables link to the same result sources; no hand-entered alternative scorecard is used.'])
ladder=pd.read_csv(ROOT/'results/qualification-ladder.csv'); steps=pd.read_csv(ROOT/'results/qualification-steps.csv')
lad=ladder.assign(Dataset=ladder.dataset.str.upper())[['Dataset','label','note','rmse']].rename(columns={'label':'Rung','note':'Construction','rmse':'Primary RMSE'})
steps=steps.assign(ci95_lower=steps.ci95_lower.map(lambda v:'—' if pd.isna(v) else f'{v:.4f}'),ci95_upper=steps.ci95_upper.map(lambda v:'—' if pd.isna(v) else f'{v:.4f}'),step=steps.step.str.replace('_',' '))
st=steps.assign(Dataset=steps.dataset.str.upper())[['Dataset','step','estimate','ci95_lower','ci95_upper','estimator']].rename(columns={'step':'Step','estimate':'Estimate','ci95_lower':'95% lower','ci95_upper':'95% upper','estimator':'Estimator'})
parts.extend(['\n## S11. Qualification ladder source values',
              'Main Figure 1 uses current estimators throughout. Rungs are primary equal-group or equal-lineage RMSEs; matched nulls are expected values over 20 realizations (Section S12). Compact steps are the locked primary contrasts. Shares are descriptive point-estimate partitions of the training-mean-to-compact gap on the RMSE and MSE scales and have no intervals. The archived CCLE ensemble row is listed for completeness only; it used the released estimator and target-level resampling.',
              table(lad),table(st)])
crossing=pd.read_csv(ROOT/'results/r1-membership-by-aggregation.csv')
cross_seed=pd.read_csv(ROOT/'results/r1-membership-by-aggregation-per-seed.csv')
ccle_seed=pd.read_csv(ROOT/'results/r1-ccle-null-per-seed.csv')
ccle_sum=json.loads((ROOT/'results/r1-ccle-null-summary.json').read_text())
seed_summary=cross_seed.assign(dataset=cross_seed.dataset.str.upper()).groupby(['dataset','aggregation'],sort=False).agg(realizations=('k','count'),min_effect=('improvement','min'),max_effect=('improvement','max'),ci_above_zero=('ci95_lower',lambda s:int((s>0).sum()))).reset_index()
parts.extend(['\n## S12. Post-review analyses (outcome-aware)',
              'Both analyses were frozen in readiness/post-review-r1-amendment.md before their outcomes were computed and reuse the accepted code, splits and tuning. They do not alter the five primary contrasts.',
              '\n### Membership by aggregation (human cohorts)',
              'Membership effect is expected-null RMSE minus declared RMSE over 20 degree-preserving null realizations; realization 0 reproduces the primary null exactly.',
              table(crossing.assign(Dataset=crossing.dataset.str.upper(),Rule=crossing.aggregation.str.replace('_',' '),
                    Declared=crossing.declared_rmse.map(lambda v:f'{v:.4f}'),Null=crossing.expected_null_rmse.map(lambda v:f'{v:.4f}'),
                    Effect=crossing.improvement.map(lambda v:f'{v:.4f}'.replace('-','\u2212')),
                    Interval=[f'{l:.3f}'.replace('-','\u2212')+' to '+f'{u:.3f}'.replace('-','\u2212') for l,u in zip(crossing.ci95_lower,crossing.ci95_upper)])
                    [['Dataset','Rule','Declared','Null','Effect','Interval']].rename(columns={'Null':'Expected null','Interval':'95% interval'})),
              table(crossing.assign(Dataset=crossing.dataset.str.upper(),Rule=crossing.aggregation.str.replace('_',' '),
                    Pos=crossing.seeds_positive.map(lambda v:f'{v}/20'),Ci=crossing.seeds_ci_above_zero.map(lambda v:f'{v}/20'),
                    Mn=crossing.seed_min.map(lambda v:f'{v:.4f}'.replace('-','\u2212')),Mx=crossing.seed_max.map(lambda v:f'{v:.4f}'.replace('-','\u2212')))
                    [['Dataset','Rule','Pos','Ci','Mn','Mx']].rename(columns={'Pos':'Positive effects, n/20','Ci':'95% intervals above zero, n/20','Mn':'Smallest effect','Mx':'Largest effect'})),

              '\n### CCLE matched null under the current estimator',
              f"Declared direct neighbours: {ccle_sum['declared_rmse_sd']:.4f}; expected property-matched null over 20 seeds: {ccle_sum['expected_null_rmse_sd']:.4f}; effect {ccle_sum['improvement_sd']:.4f} (lineage-bootstrap 95% interval {ccle_sum['ci95_lower']:.4f} to {ccle_sum['ci95_upper']:.4f}). All {ccle_sum['seeds_ci_above_zero']} seeds had intervals above zero. The table below reports seed-specific results under the current estimator. The archived ensemble, reported separately in Section S11, used the released estimator and target-level resampling and is not combined with the current ladder.",
              table(ccle_seed.rename(columns={'seed':'Seed','improvement':'Effect','ci95_lower':'95% lower','ci95_upper':'95% upper'})),
              '\n## S13. Availability inventory',
              '| Material | Status | Location |\n| --- | --- | --- |\n'
              '| Code, tests, figure scripts, frozen amendments | Public | code archive: scripts/, tests/, readiness/ |\n'
              '| Aggregate model metrics, contrasts, budgets, ladder and post-review summaries | Public | results/ |\n'
              '| Per-run summaries, tuning and budget grids, null grids (archived and regenerated) | Public | evidence/new, evidence/baseline, evidence/archived-ccle-property-matched-null |\n'
              '| Raw Metabolomics Workbench and CCLE matrices | Not redistributed; regenerable | original repositories (Data availability) |\n'
              '| Individual predictions, participant-linked losses and split maps | Withheld | regenerable locally from code and public source data |'])
(OUT/'supplement.md').write_text('\n\n'.join(parts)+'\n')
print('Wrote manuscript/supplement.md and results/secondary-mean-model-metrics.csv')
