# Matched nulls and compact baselines qualify metabolic-state representations

<!-- EDITION-FRONT-MATTER -->

## Abstract

Biochemical representations can outperform randomized controls while retaining less predictive information than compact statistical alternatives. We tested this distinction by reconstructing hidden metabolites in held-out biological groups: 1,539 samples from 112 participants, 450 samples from 15 population categories and 876 cancer cell lines from 18 lineages. A qualification ladder compared each representation with a matched null, which preserves its group sizes and overlaps but randomizes membership, and with compact statistical predictors of equal size. Chemical-descriptor medians outperformed matched nulls in both human cohorts (equal-group RMSE 0.317 versus 0.419 and 1.227 versus 1.803 training standard deviations), and reaction neighborhoods outperformed property-matched random features in an archived ensemble. However, dimension-matched principal components reduced error further (0.196 and 0.839), as did correlation-selected panels in cell lines (0.731 versus 0.824); all five primary contrasts favored the statistical reference. In the larger cohort, a matched null alone accounted for 74% of the error reduction from the training mean to principal components. Declared biochemical membership therefore carries information, but less than compact statistics extract from the same measurements. The workflow is openly available, and we recommend reporting both steps of the ladder.

**Keywords:** benchmarking; lipidomics; metabolite imputation; pathway analysis; randomization

## Introduction

Metabolomics representations compress measured abundance profiles into quantities intended to be easier to compare and interpret. A useful evaluation must distinguish three questions: whether a representation predicts hidden measurements, whether its declared membership carries information beyond specified random controls, and whether it competes with practical alternatives. These questions require different comparators, which can be arranged as a qualification ladder (Figure 1). A population mean tests basic predictive information. A matched null tests whether the declared membership matters: it is a randomized representation with the same shape as the biochemical one, the same number and sizes of groups and the same overlap between them, but with members assigned without regard to biochemistry. Any advantage over that null can therefore be attributed to which metabolites were grouped together, rather than to how many were grouped or how often they overlapped. A learned representation or selected panel of the same size then tests whether the chosen construction is an effective way to use the available measurements. Passing the second rung does not imply passing the third.

The components of this approach have substantial prior art. Single-sample pathway scoring has been benchmarked in metabolomics [1], and pathway-local singular value decomposition was introduced through PLAGE [2]. LION/web organizes lipids by chemical and biological attributes [3]; subsequent LION-PCA work uses learned components to guide sample-level lipid summaries [4]. Thus, naming a lipid score by class, chain composition or ontology membership does not establish a new scoring method. It also does not establish that the named property is responsible for the score's predictive performance.

Metabolite reconstruction has similarly used network information and learned low-dimensional structure. MINMA combines metabolic-network and adduct relationships for missing-value prediction [5]. MIRTH reconstructs missing analytes using rank transformation and matrix factorization [6], while variational autoencoders have been evaluated for transferable metabolomics representations [7]. These methods address related but nonidentical endpoints: missing values, wholly unmeasured analytes, ranks or harmonized cohort representations. They establish relevant prior art without implying that a generic ridge or principal-component implementation constitutes a reproduction of their complete methods.

Null calibration itself is established in metabolic-network enrichment [8], and simulations have shown that pathway-analysis methods can recover nonspecific signals [9]. Our contribution is a reproducible empirical qualification of chemical and reaction-derived representations under biological-group exclusion, with both matched random structures and strong compact predictors. We evaluate a previously released benchmark, then add openly adaptive comparisons on its already examined cohorts. The aim is to determine what the available evidence permits users to claim about these representations. Success against random structure is retained as evidence even when stronger predictors perform better.

## Results

### Source recovery separates reproduction from new comparisons

The human discovery data were ST002081/AN003790, associated with Hornburg et al. [10]. The evaluated matrix contained 1,539 repeated samples and 112 participant codes, matching the final publication. Its demographic supplement also contains 112 participant codes but includes additional sample records; the Workbench narrative's 1,546 samples/109 subjects remains a documented metadata discrepancy. The second dataset, ST000818/AN001299, contained 450 samples across 15 population categories [11]. The deposit reports 450 individuals, although a separate public donor-to-sample mapping was unavailable. Cohorts were analyzed separately, with models refitted within each cohort.

CCLE metabolomics and expression provided 913 aligned cell lines [12]. The frozen mapping retained 76 of 225 assayed metabolites; target and lineage eligibility yielded 60 reconstruction targets evaluated on 876 cell lines from 18 lineages. Thus 913 describes source alignment, while 876 describes the evaluated population. Direct-reaction features used the pinned Human-GEM v2.0.0 model, with credit to the foundational Human1 resource and the Human2 update [13,14].

The public software package [15] was recovered and compared with an immutable local snapshot. Fourteen real-data analysis/report stages completed in a fresh environment; 51 of 62 declared outputs were byte-identical, and the recorded analysis decisions agreed. Remaining numerical differences were retained. This scientific execution is separate from checksum verification. Three archived implementation fingerprints could not be reconstructed from surviving release files, although the source files themselves agreed across the recovered locations. Accordingly, the reproduction establishes execution of released source bytes, with explicit numerical comparisons; it cannot reconstruct every historical pre-release implementation.

The new primary comparisons used corrected and reviewed code. An initial human implementation was superseded after defects in inner-fold weighting, rank capping, target eligibility and loss aggregation were identified. Its outputs remain archived and are excluded from the results below. The comparator set, split rules, hyperparameter grid, estimands and five primary contrasts were retained through these repairs.

### A qualification ladder separates membership information from competitive value

Each comparison in this study answers one rung of the ladder in Figure 1. The matched nulls differ by representation but follow the same principle: preserve the structural budget of the biochemical representation and randomize only its biochemical content (Table 1). A null that is easier than this, for example random groups smaller than the declared ones, would be beaten for uninteresting reasons; one that also matched outcome correlation would be built from the answer. The property-matched CCLE null therefore matches network degree and assay coverage but deliberately not correlation with the target.

| Null control | Held fixed | Randomized | Used for |
| --- | --- | --- | --- |
| Size-matched random groups | Number and sizes of groups | Which metabolites form each group | Historical family scores (ST002081) |
| Degree-preserving descriptor graph (primary) | Every descriptor's size; every lipid's number of descriptors | Which lipids share a descriptor | New human primary analyses |
| 20-graph null ensemble | As above, over 20 independent rewirings | As above | Checks that one rewiring was not unusually weak |
| Dimension-matched random features | Number of metabolite and expression features per target | Which features are used | CCLE reaction neighborhoods (archived) |
| Property-matched random features | Feature count, network degree and assay coverage | Network relationships | CCLE, strictest null; matched without using outcomes (archived) |

Table 1. Matched null controls. Each preserves a stated structural budget and randomizes only biochemical membership. Archived controls used the released estimator and are reported on that scale.

Both steps of the ladder held in every dataset (Figure 1D). Descriptor medians reduced error relative to the primary matched null by 0.102 training standard deviations in ST002081 (95% interval 0.097 to 0.108) and by 0.576 in ST000818 (0.046 to 1.031); CCLE reaction neighborhoods outperformed the property-matched null ensemble by 0.137 (0.097 to 0.181) in the archived analysis. Compact statistics then reduced error relative to the biochemical representation by 0.120 (0.115 to 0.126), 0.387 (0.075 to 0.687) and 0.092 (0.083 to 0.103), respectively.

The ladder also shows where predictive information arises. Of the error reduction from the training mean to dimension-matched PCA, the matched null alone accounted for 74% in ST002081, declared membership for a further 12% and the compact learned representation for the remaining 14%. In ST000818 the corresponding shares were 18%, 49% and 33%. Thus, in the larger cohort, most of the gain came from aggregating correlated lipids in groups of the declared shape, regardless of their biochemical identity; in the smaller, more heterogeneous cohort, membership mattered substantially more. These shares are descriptive decompositions of point estimates from one fixed set of splits; they carry no separate intervals and are not part of the primary inference.

![Figure 1. The qualification ladder. **A,** Construction of the primary matched null in a toy example: lipid–descriptor memberships are rewired so that each descriptor keeps its size and each lipid its number of descriptors, while biochemically coherent groups (circles or squares) become mixed. **B,C,** Held-out reconstruction error for each rung in the two human cohorts, in training-standard-deviation units; lower is better. **D,** Error reduction contributed by the two decisive steps with 95% biological-group bootstrap intervals; intervals in ST002081 are narrower than the markers. The CCLE matched-null step (open marker) comes from the archived property-matched 20-seed ensemble, which used the released estimator, and is not on the same scale as the new CCLE primary metric.](../figures/figure1-qualification-ladder.png){width=78%}

### Historical matched-null results are reproduced

The reproduced historical benchmark contained a useful negative control. Broad-family scores in ST002081 had row-weighted RMSE 0.650 training standard deviations, whereas size-matched random groups had RMSE 0.627. The family representation predicted hidden measurements but did not establish the claimed membership advantage. The all-visible ridge reference reached 0.175. These historical values use the archived estimator and should not be interchanged with the new equal-group metric.

An adaptive structural follow-up used 95 overlapping lipid descriptors. Its archived row-weighted RMSE was 0.309, compared with 0.410 for the primary degree-preserving randomized graph. The analogous ST000818 values were 1.237 and a consistently poorer 20-graph null ensemble. Across the archived human graph ensembles and CCLE dimension/property-matched controls, the previously reported direction of structural advantage was reproduced. These comparisons concern the specified null distributions. Twenty sampled graphs do not justify a graph-randomization probability below 1/21, and biological-unit intervals against individual graphs are a different calculation.

The extended primary analysis preserved a degree-preserving null alongside compact competitors. Structural-median scores continued to have lower equal-group error than that null in both human cohorts: 0.317 versus 0.419 in ST002081 and 1.227 versus 1.803 in ST000818. The result therefore does not disappear when evaluation uses common splits and training-only tuning. Its interpretation changes when informative alternatives are included.

### Compact learned scores outperform descriptor medians in both human cohorts

At the same visible-input panel and representation dimension, global principal-component scores reduced error from 0.3168 to 0.1964 in ST002081 and from 1.2267 to 0.8394 in ST000818 (Table 2, Figure 2). Descriptor-local first-component scores also improved prediction, reaching 0.2434 and 0.9574 respectively. The latter comparison holds the descriptor memberships fixed and changes their aggregation from an unweighted median to learned local loadings. Consequently, the median-based implementation cannot attribute its predictive gap solely to a shortage of biochemical annotations.

The human panels supplied 390–397 visible lipid inputs per mask in ST002081 and 202–208 in ST000818. Structural median, local SVD and global PCA each produced 95 or 81 coordinates in the respective primary panels. All-visible ridge used the full visible dimension and achieved RMSE 0.178 and 0.849. Dimension matching therefore did not remove the reference methods' advantages. It also did not equalize every development cost: PCA and local SVD learn loadings that the fixed median representation does not require.

| Dataset | Structural median | Descriptor-local SVD | Global PCA | All-visible ridge | Degree-preserving null |
| --- | ---: | ---: | ---: | ---: | ---: |
| ST002081 | 0.3168 | 0.2434 | 0.1964 | 0.1780 | 0.4192 |
| ST000818 | 1.2267 | 0.9574 | 0.8394 | 0.8491 | 1.8030 |

Table 2. New adaptive human primary results: square root of equal biological-group MSE in training-target standard-deviation units. Groups are 112 participants or 15 population categories. Models share their cohort's outer splits and within-fit eligibility.

### Reaction neighborhoods lose to selected panels with matching prediction-time size

Direct-neighbor ridge in CCLE achieved RMSE 0.8239. Selecting the same number of metabolites by absolute correlation within the training data reduced error to 0.7315. Both predictors used 1–19 metabolites per target, with median three. This comparison matches prediction-time marker count, not development information: correlation selection screened all 75 eligible non-target metabolites in the training set, whereas reaction neighborhoods were fixed by prior annotation. No unselected held-out markers were used to form correlation-selected predictions.

An all-other-metabolite model reached 0.6648. Global PCA with the same number of coordinates as the direct panel reached 0.8090, while reading all 75 non-target assays at prediction time. Its coordinate count therefore must not be described as a matched assay budget. Adding reaction-linked expression signatures yielded 0.8117; adding metabolite–expression products yielded 0.8170. The interaction construction did not improve the aggregate point estimate over the additive model, preserving the historical absence of a general interaction gain. These ablations were descriptive rather than extra primary significance tests.

The additive and interaction models consumed additional expression information: median five unique genes and five expression signatures, with median representation dimensions eight and thirteen. A low-dimensional output is therefore an incomplete description of information cost. The full budget records expose metabolite inputs, raw transcript genes, signature counts, interaction terms, loadings and regression coefficients for each outer fit.

![Figure 2. Reconstruction performance in the accepted adaptive comparisons. Lower RMSE indicates better prediction. Human scores weight participants or population categories equally; CCLE scores average available lineages within each fixed target, then targets. Dataset-specific training-standardized units and different target panels preclude interpreting differences between datasets as a common biological effect size. All-model and sensitivity tables retain the training-mean, family and null references.](../figures/figure1-performance.png){width=80%}

### All five primary contrasts favor the reference methods

We defined improvement as reference RMSE minus the named structural model's RMSE, so negative values favor the reference. All five primary estimates were negative (Table 3, Figure 3). Their 95% descriptive intervals and 99% per-contrast intervals excluded zero. The latter use a Bonferroni allocation targeting nominal 95% familywise coverage across five contrasts. Monte Carlo group sign-flip tests gave raw two-sided probabilities at the 10,000-draw resolution floor, $1/10{,}001$, and Holm-adjusted probabilities approximately 0.00050 across the five contrasts. These values are conditional on the fitted predictions and fixed panel; their resolution and interpretation are not those of a fresh prospective study.

| Dataset and reference | Improvement | 95% interval | 99% per-contrast interval |
| --- | ---: | --- | --- |
| ST002081, global PCA | −0.1204 | −0.1258 to −0.1153 | −0.1278 to −0.1140 |
| ST002081, local SVD | −0.0733 | −0.0776 to −0.0691 | −0.0789 to −0.0676 |
| ST000818, global PCA | −0.3873 | −0.6872 to −0.0748 | −0.7902 to −0.0712 |
| ST000818, local SVD | −0.2693 | −0.4725 to −0.0518 | −0.5388 to −0.0494 |
| CCLE, correlation-selected ridge | −0.0924 | −0.1034 to −0.0830 | −0.1073 to −0.0807 |

Table 3. Paired contrasts from 10,000 biological-group bootstrap draws. The 99% per-contrast intervals target nominal 95% Bonferroni familywise coverage across five contrasts, subject to the conditional bootstrap assumptions. The structural model is descriptor median for human datasets and direct-neighbor ridge for CCLE. Intervals use participants, population categories or lineages; metabolites and validation folds are not counted as independent people.

![Figure 3. Primary reference-minus-structural-model RMSE contrasts. Zero denotes equal error; negative estimates favor the reference. Thick intervals are descriptive 95% intervals; thin intervals are 99% per-contrast intervals targeting nominal 95% Bonferroni familywise coverage across five contrasts. Resampling preserves paired outcomes and, for CCLE, the fixed target panel. It does not refit models or characterize uncertainty from choosing a different cohort, assay panel or annotation database.](../figures/figure2-comparisons.png)

### Sensitivities preserve the principal accuracy ordering

Training-defined missingness eligibility expanded the ST002081 visible panels to 571–596 inputs. Structural median remained less accurate than PCA and local SVD: RMSE 0.310, 0.214 and 0.241 respectively. ST000818's missingness run gave the same aggregate results as its primary panel. This sensitivity reduces dependence on whole-cohort complete-case selection; it does not turn the reused cohort into unseen confirmation.

A separate annotation-resolution sensitivity removed unsupported individual-chain descriptors from multi-chain sum-composition labels while retaining declared total composition. ST002081 results changed little. In ST000818 the representation shrank from 81 to 67 coordinates; median, PCA and local-SVD errors were 1.235, 0.863 and 0.962. Thus neither sensitivity reversed the principal ordering. These checks qualify the implemented annotations rather than validating every molecular identity.

An outcome-aware secondary analysis substituted the arithmetic mean for the median within the same descriptors. Errors were 0.2425 and 0.9443, close to the local-SVD results and below the median errors, while remaining above global PCA. This follow-up supports aggregation choice as a contributor to the observed gaps. It is descriptive, was requested after the primary outcomes, and does not alter the five primary contrasts.

## Discussion

The benchmark distinguishes structural information from competitive predictive value. Chemical descriptors and direct reactions can outperform the specified random structures, yet their median or fixed-neighbor implementations can lose to straightforward statistical alternatives. Taken together, the reproduced null comparisons and five primary contrasts demonstrate this distinction. The project's original predictive-superiority ambition was not met. A claim of general predictive superiority for the biochemical representations is therefore unsupported. The positive contribution is an auditable qualification workflow that makes this distinction visible, including the cost of preserving a fixed, inspectable feature construction. We suggest that studies proposing biochemical representations report both ladder steps: the gain over a null that matches the representation's structural budget, and the gap to a compact statistical alternative of the same size. Either step alone invites a misleading conclusion: the first can make weak representations look biologically grounded, and the second can make informative structure look useless.

The local-SVD results show that annotation membership and aggregation deserve separate scrutiny. Keeping the descriptor definitions while learning within-descriptor weights improved accuracy in both human cohorts. This does not prove an optimal aggregation rule or isolate a causal biochemical mechanism. The global-PCA results further indicate that appreciable predictive information lies in broader covariance patterns. No noninferiority margin or preferred tradeoff was selected after observing these differences, and we did not measure an interpretability benefit that could compensate for them.

The evidence has important boundaries. Both human cohorts and their archived outcomes were known before the extension. Historical complete-case panels, CCLE mappings and lineage-size eligibility were retained to make comparisons auditable. The missingness sensitivity addresses one selection mechanism, while assay coverage, lipid identification and network accessibility still limit scope. Training weights each sample equally, so frequently sampled people contribute more to model fitting, even though the primary evaluation weights people equally. Fifteen population categories and 18 cancer lineages provide limited support for inference to substantially different populations or tissues.

Related methods were treated as prior art, not as unperformed benchmark wins. The local SVD is an implementation of a standard principle, not a full ssPA package evaluation. Neither MINMA, MIRTH, LION-PCA nor a deep representation was executed as a native comparator. MIRTH code was excluded because applicable commercial-research and publication permissions were unresolved. The present result concerns the tested methods and endpoint; it establishes no ranking against those systems.

Finally, the original factorized evidence contract separates measured metabolic state, genetic support, transcript state, constraint-based reserve, perturbational evidence and uncertainty. Archived genetics, constraint, isotope and longitudinal challenges retain supporting or exploratory status; they were not newly validated by these compact-baseline comparisons. They cannot convert concentration reconstruction into flux, establish temporal causality, support treatment response or combine unrelated cohorts into an individual's multimodal measurement. The technology value demonstrated here is disciplined qualification of a representation and its limits. Broader biological or practical benefits require new evidence.

## Methods

### Data, source boundaries and eligibility

Inputs were recovered into an isolated workspace with source checksums. ST002081 used the pinned Workbench AN003790 table: 1,643 rows, of which 104 QC rows had `RandomID = NA`; 1,539 rows and 112 participant codes remained. The archived primary schema contained 493 lipids in nine families. ST000818 used AN001299 and its Categorization factor, yielding 450 sample rows, 15 groups and 255 primary lipids in six families. Unique sample labels and the deposit's 450-person statement were retained separately from the unavailable donor-level crosswalk. Abundance values were used in the provided scale before training-fold standardization; no additional human log transformation was introduced.

CCLE input files were `CCLE_metabolomics_20190502.csv`, `CCLE_RNAseq_genes_rpkm_20180929.gct.gz` and `Cell_lines_annotations_20181226.txt`. The loader retained source-provided cleaned log10 metabolite abundance and transformed expression to log2(RPKM + 1), averaging duplicate gene rows before transformation. The 913 aligned lines supplied 76 mapped metabolites. Frozen candidate definitions required direct non-transport reactions containing at most eight metabolites and complete reaction-linked gene signatures. Sixty target definitions were reconstructed from 317 candidate rows. For each target, finite target measurements and lineages with at least 15 eligible lines were required; target eligibility also required at least 300 lines and five lineages. All 60 accepted targets retained 876 lines and 18 lineages. These restrictions were applied retrospectively to the known assay and are disclosed as such.

Human-GEM v2.0.0 supplied reaction and gene–protein–reaction mappings. Alternative GPR disjuncts were represented separately; multi-gene complex signatures used the minimum constituent log-expression value, with single-gene signatures unchanged. This is an expression proxy, not an enzyme-activity measurement or flux constraint calibration. Mapping/candidate reconstruction was compared with the frozen files. The input ledger, rejected mappings and per-target eligibility accompany the reproducibility dossier.

### Human representations and hidden panels

Five disjoint masks distributed eligible features within families, so each primary lipid was hidden once. Hidden analytes were removed before fitting every representation. Label-derived descriptors covered family, total carbon/unsaturation, family-by-unsaturation and parsed chain attributes. Descriptors had at least five panel members and at most 90% panel coverage; after masking and training eligibility, at least two visible members were required. Median scores and local first-component scores used identical memberships. Global PCA used the same visible panel and a component count equal to retained descriptor count, capped by numerical rank of the centered training matrix. Rank used the largest singular value times the largest matrix dimension times floating-point epsilon as tolerance.

Family medians and all-visible ridge were retained. The primary randomized descriptor graph used edge-switch attempts equal to ten times the edge count, accepting switches only when they preserved a simple bipartite graph. Both lipid and descriptor degrees were checked exactly. This algorithm and mixing diagnostics do not guarantee uniform sampling over all degree-matched graphs. Historical 20-seed ensembles remain separate from the new primary-null reference.

The primary schemas inherit whole-cohort complete-case selection. In the missingness sensitivity, all assay labels belonging to families of at least five labels were candidates. Every fit retained visible inputs observed in at least 80% of its training rows. Hidden targets had to be complete and nonconstant within that fitting partition; validation losses used only observed targets. Inner eligibility was recalculated from inner-training rows, independently of outer and inner validation missingness. The resolution sensitivity removed acyl, chain-carbon and chain-unsaturation assignments from multi-chain labels containing only a total-composition pair; single-chain and explicitly reported chain annotations were retained. Both sensitivities used all original models and unchanged tuning rules.

### CCLE predictors and information budgets

For each target, direct-neighbor ridge used its frozen set of $k$ measured neighbors. Correlation-selected ridge ranked all 75 non-target training metabolites by absolute Pearson correlation with the training response after mean imputation, selecting $k$ with stable lexical tie handling. Selection was repeated within every inner and outer training partition. Prediction used only those selected markers. Global PCA read all 75 non-target metabolites, with at most $k$ coordinates and a numerical training-rank cap. All-other-metabolite ridge used the full panel. Additive models combined neighbors and GPR signatures; interaction models additionally included mapped products of standardized metabolite and expression terms, standardized again from training moments. The target was excluded explicitly from predictor matrices and interaction definitions.

Prediction-time metabolite count, candidate-screening count, transcript genes, signature/interaction dimensions, loadings and regression coefficients were recorded separately. Human PCA and descriptor scores match visible inputs and output coordinates, not learned-transform parameters. CCLE selected panels match prediction-time metabolite count while requiring a broader training assay. Global CCLE PCA matches coordinates only.

### Training, validation and estimands

Each input column was imputed with its arithmetic training mean, then divided by the population standard deviation of the imputed training column after centering. Empty-column means defaulted to zero and scales at or below $10^{-12}$ to one. Representations, including PCA component scores, were standardized from their own training moments before ridge. Targets were standardized using training means and population standard deviations; held-out target values never supplied a transform or predictor. The training-mean reference predicted zero in these units. Regressions included an intercept and minimized squared error plus $\alpha\|\beta\|_2^2$.

Human outer validation used one balanced five-fold group partition shared across all masks/models. Groups were participants for ST002081 and population categories for ST000818. CCLE used two repeats of five lineage-isolated folds per target. Three grouped inner folds selected $\alpha\in\{0.1,1,10,100\}$ by pooling individual validation-group MSEs with equal group weight; exact ties favored the smaller value. Imputation, scaling, loadings and supervised marker selection were refitted within each inner training set, then on outer training using the selected alpha. Human regression used the Cholesky solver; CCLE used LSQR. Training rows were equally weighted. Split seeds and complete tuning grids are recorded with each run.

For human data, let $e_{im}$ be the mean squared standardized error over observed hidden targets for sample $i$, mask $m$. Average nonempty masks within a sample, then samples within group $g$, to obtain $L_g$. The primary error is

$$
\operatorname{RMSE}_{human}=\sqrt{\frac{1}{G}\sum_{g=1}^{G}L_g}.
$$

Repeated samples stay within their participant. For CCLE, let $L_{t\ell}$ average squared errors over cells and repeated predictions for target $t$, lineage $\ell$. With fixed $T=60$ and available lineages $A_t$,

$$
\operatorname{RMSE}_{CCLE}=\sqrt{\frac{1}{T}\sum_{t=1}^{T}\frac{1}{|A_t|}\sum_{\ell\in A_t}L_{t\ell}}.
$$

CCLE repeats are averaged as losses, not counted as new cells. Supplementary row-weighted RMSE pools squared errors over observed prediction pairs. The supplementary skill statistic $1-\sum_j(z_j-\hat z_j)^2/\sum_jz_j^2$ uses standardized targets $z_j$ and predictions $\hat z_j$, with targets centered by training-fold means; it is improvement over that reference, not conventional test-set-centered $R^2$.

### Qualification ladder

The ladder (Figure 1) reorganizes accepted results and required no refitting. Human rungs are the primary equal-group RMSEs of the training mean, degree-preserving null, descriptor median, dimension-matched global PCA and all-visible ridge. Step intervals are the existing paired biological-group bootstrap intervals for null versus descriptor median and PCA versus descriptor median (10,000 draws, seed 20260921). Shares divide the training-mean-to-PCA error reduction into the reductions from mean to null, null to descriptor median and descriptor median to PCA; they are point-estimate decompositions without intervals. The CCLE matched-null step is the expected random-minus-topology improvement from the archived 20-seed property-matched ensemble with its 5,000-draw target-bootstrap interval, computed with the released estimator rather than the new equal-lineage metric. The toy example in Figure 1A is illustrative; its rewired graph preserves both degree sequences, which the figure script asserts.

### AI-assisted research and writing

OpenAI Codex and Anthropic Claude were used under the author's direction for code drafting, analysis orchestration, literature organization, figure preparation and manuscript-language development. The author defined the scientific questions and claim boundaries, reviewed the analysis code and outputs, verified citations and numerical claims, revised the manuscript and accepts full responsibility for its content. AI systems were not treated as authors or as independent sources of evidence.

### Uncertainty, adaptation and reproducibility

The five primary contrasts were descriptor median versus global PCA and local SVD in each human cohort, plus CCLE direct neighbors versus correlation selection. Improvement equals reference RMSE minus structural-model RMSE. Paired bootstrap draws resampled 112 participants, 15 population categories or shared CCLE lineage labels, preserving all fixed targets and repeated losses. Ten thousand draws used seed 20260921. Percentile 95% intervals were descriptive; 99% per-contrast intervals allocated 0.05 across five contrasts by Bonferroni, targeting nominal 95% familywise coverage. Two-sided paired sign flips used seed 20260922, 10,000 draws and a plus-one Monte Carlo correction; their five probabilities received Holm adjustment. All five raw probabilities reached the resolution floor of $1/10{,}001$. For CCLE, each lineage's paired MSE contribution was flipped jointly across targets. Sign flips assume exchangeability of paired group-effect signs under the null. Overlapping cross-validation training sets can induce dependence across held-out groups that neither procedure fully represents. Uncertainty is conditional on fixed fits, targets and these resampling assumptions, with no full-pipeline refitting or population-sampling guarantee.

The specification and resolution amendment were frozen before extension outcomes, after earlier cohort results had been inspected. The work is therefore post-release/adaptive, not prospective or blind. An outcome-aware descriptor-mean follow-up requested after the primary results is reported as secondary and descriptive, with its full scorecards in the supplement; it is not part of the five-test family. Superseded human implementation outputs are explicitly excluded. Accepted human revision 2 and CCLE implementations have distinct code hashes, input checks, split/eligibility records and meaningful numerical tests. The environment used Python 3.12.3, NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.1 and scikit-learn 1.9.0, with single-threaded BLAS and bounded local concurrency. Historical implementation-fingerprint discrepancies remain disclosed; no tolerance was chosen to relabel differing files as byte-identical.

<!-- EDITION-DECLARATIONS -->

## References

1. Wieder C, Lai RP, Ebbels TM. Single sample pathway analysis in metabolomics: performance evaluation and application. BMC Bioinformatics 2022;23:481. doi: 10.1186/s12859-022-05005-1.
2. Tomfohr J, Lu J, Kepler TB. Pathway level analysis of gene expression using singular value decomposition. BMC Bioinformatics 2005;6:225. doi: 10.1186/1471-2105-6-225.
3. Molenaar MR, Jeucken A, Wassenaar TA, van de Lest CH, Brouwers JF, Helms JB. LION/web: a web-based ontology enrichment tool for lipidomic data analysis. GigaScience 2019;8:giz061. doi: 10.1093/gigascience/giz061.
4. Molenaar MR, Haaker MW, Vaandrager AB, Houweling M, Helms JB. Lipidomic profiling of rat hepatic stellate cells during activation reveals a two-stage process accompanied by increased levels of lysosomal lipids. J Biol Chem 2023;299:103042. doi: 10.1016/j.jbc.2023.103042.
5. Jin Z, Kang J, Yu T. Missing value imputation for LC-MS metabolomics data by incorporating metabolic network and adduct ion relations. Bioinformatics 2018;34:1555–61. doi: 10.1093/bioinformatics/btx816.
6. Freeman BA, Jaro S, Park T, Keene S, Tansey W, Reznik E. MIRTH: metabolite imputation via rank-transformation and harmonization. Genome Biol 2022;23:184. doi: 10.1186/s13059-022-02738-3.
7. Gomari DP, Schweickart A, Cerchietti L, Paietta E, Fernandez H, Al-Amin H et al. Variational autoencoders learn transferrable representations of metabolomics data. Commun Biol 2022;5:645. doi: 10.1038/s42003-022-03579-3.
8. Picart-Armada S, Fernández-Albert F, Vinaixa M, Rodríguez MA, Aivio S, Stracker TH et al. Null diffusion-based enrichment for metabolomics data. PLoS One 2017;12:e0189012. doi: 10.1371/journal.pone.0189012.
9. Cooke J, Wieder C, Poupin N, Frainay C, Ebbels T, Jourdan F. Simulated metabolic profiles reveal biases in pathway analysis methods. Metabolomics 2025;21:136. doi: 10.1007/s11306-025-02335-y.
10. Hornburg D, Wu S, Moqri M, Zhou X, Contrepois K, Bararpour N et al. Dynamic lipidome alterations associated with human health, disease and ageing. Nat Metab 2023;5:1578–94. doi: 10.1038/s42255-023-00880-1.
11. Metabolomics Workbench. African Diet Studies, project PR000583, study ST000818, analysis AN001299. Released 23 September 2019; accessed 21 September 2026. Available at: https://doi.org/10.21228/M89M31.
12. Li H, Ning S, Ghandi M, Kryukov GV, Gopal S, Deik A et al. The landscape of cancer cell line metabolism. Nat Med 2019;25:850–60. doi: 10.1038/s41591-019-0404-8.
13. Robinson JL, Kocabaş P, Wang H, Cholley PE, Cook D, Nilsson A et al. An atlas of human metabolism. Sci Signal 2020;13:eaaz1482. doi: 10.1126/scisignal.aaz1482.
14. Luo J, Wang H, Moyer D, Guo Z, Robinson JL, Gustafsson J et al. Reconstruction of human metabolic models with large language models. Proc Natl Acad Sci U S A 2026;123:e2516511123. doi: 10.1073/pnas.2516511123. Model version used: Human-GEM v2.0.0, available at: https://github.com/SysBioChalmers/Human-GEM/tree/v2.0.0.
15. Ünver O. Matched nulls for metabolic pathway scores. Software release v1.0.1, 31 August 2026. Available at: https://doi.org/10.5281/zenodo.22207315.
