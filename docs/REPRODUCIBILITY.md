# Reproducing the review package

This is an internal review package for an openly adaptive post-release analysis.
It is not a new public release or a claim of journal acceptance. The original
public software archive is v1.0.1, DOI https://doi.org/10.5281/zenodo.22207315.
The archive ZIP SHA-256 is
`826d7a19d33955587f1911f0b0850d475b487780c17ac5b026e165541221dc9a`.

## Inputs and environment

Use Python 3.12.3 or a compatible 3.12 interpreter. The exact tested package versions
are in `receipts/m0-environment-freeze.txt` and the archive's `requirements.lock`.
Git is needed by the released verifier. Document rendering also requires the
Poppler utilities `pdfinfo` and `pdftotext`; `pdftoppm` supports visual inspection.
BLAS implementation, operating system and floating-point ordering can affect
outputs; file identity is reported separately from numerical differences.

On this workspace, verified raw inputs are under ignored `work/release/data/raw/`.
They total 171,453,766 bytes across ten files. No 63-GB original data tree is needed.
In a fresh extracted review-code directory, recover the existing public archive
and exact raw inputs with the standard-library bootstrap:

```bash
python3 scripts/bootstrap_public_inputs.py
python3 -m venv .venv
.venv/bin/pip install -r work/release/requirements.lock
.venv/bin/pip install --no-deps --no-build-isolation -e work/release
```

The bootstrap never overwrites an existing inputs/work tree. Downloads fail closed
on hash changes. ST002081 trailing CR/LF bytes are normalized exactly as in the
published fetcher. Old URLs may disappear or drift; a checksum mismatch must be
investigated rather than bypassed. The portable bootstrap is code-reviewed;
network availability of every remote payload at future execution is not promised.
The main work used already available local files and independently checked their
expected hashes before copying them. Exact public URLs and checksums are in the
input ledger and bootstrap. Source terms and declarations remain component-specific.

## Executions

Run these sequentially for a four-worker maximum; each script enforces one BLAS
thread per scientific process. Do not launch the original unrestricted make target
alongside these jobs. Peak measured memory is comfortably below the 8-GiB budget.

```bash
.venv/bin/python work/release/scripts/verify_release.py
.venv/bin/pytest -q work/release/tests tests
.venv/bin/python scripts/run_baselines.py
.venv/bin/python scripts/run_remaining_baselines.py
.venv/bin/python scripts/rebuild_ccle_mapping.py
.venv/bin/python scripts/close_baseline_audit.py
.venv/bin/python scripts/run_human_grid.py
.venv/bin/python scripts/ccle_extension.py --output runs/m2-ccle --private-output work/m2-ccle/full
.venv/bin/python scripts/consolidate_results.py
.venv/bin/python scripts/human_mean_sensitivity.py --dataset st002081
.venv/bin/python scripts/human_mean_sensitivity.py --dataset st000818
.venv/bin/python scripts/make_figures.py
.venv/bin/python scripts/build_supplement.py
```

Use fresh output directories or a fresh workspace for reruns. Completed extension
outputs are not intentionally overwritten. The secondary mean comparison is an
outcome-aware amendment; it never replaces one of the five locked primary tests.
Earlier defective human v1 runs and one failed secondary startup remain in this
workspace but are explicitly excluded from accepted results.

The three orchestration runners were repaired after Academic review 005: a failed
child now produces a failed state and nonzero runner exit while preserving stage
records/logs. Nine synthetic success, exit-code and signal tests cover those paths;
the full suite now has 68 passing tests. Historical successful analyses used the
earlier wrappers; their hashes and receipts remain unchanged. This orchestration
repair changes no estimator, scientific command or accepted numerical result.

## Inspecting results

Start with `results/primary-comparisons.csv`, `results/all-model-metrics.csv`, the
two information-budget tables, and `results/source-manifests.json`. Every accepted
run manifest hashes output tables, code and protocol. Runtime configuration copies
for archived reruns are under `receipts/runtime-configs/`. The code-release snapshot
is separate from generated rerun outputs. Core release checksums passing is not
scientific reproduction; the 14 actual pipeline executions and independent table
reductions are documented separately.

The published archive was recovered exactly and 51 of 62 declared rerun outputs
matched byte for byte. Eleven differ, principally ST002081 all-visible ridge
numerics and downstream tables/figures/reports. All 14 manifest decisions match.
No unreported numerical tolerance converts mismatches into exact matches. Three
old implementation digests do not match any surviving source copy; current
reproduction does not establish their historical source identity.

Participant-linked sample losses, exact human split maps and individual CCLE
predictions stay under ignored `work/`. Review-package exports contain model,
fold/population/lineage and target aggregates plus scripts. The original public
archive already contains some pseudonymous participant-linked derived tables;
this is disclosed rather than misdescribed as exclusively aggregate data. This
workspace does not alter or redistribute that archive as a new public release.

## Figures and documents

`scripts/make_qualification_ladder.py` writes main Figure 1 and
`results/qualification-{ladder,steps}.csv` from accepted run outputs and the archived CCLE
property-matched null report, without refitting. `scripts/make_figures.py` writes PNG, SVG, PDF
and exact CSV source data for main Figures 2 and 3 (files `figure1-performance.*` and
`figure2-comparisons.*`). Figure 2 uses only the accepted three primary scorecards; Figure 3
uses only the five locked contrasts. Thick intervals are descriptive 95% intervals; thin intervals
are 99% per-contrast intervals targeting nominal 95% Bonferroni familywise coverage
across five contrasts. Negative values favor the statistical reference. Inference
is conditional on fitted models and the fixed target panel. Sign flips assume
exchangeability of paired group-effect signs under the null, and overlapping
cross-validation training sets can induce dependence across held-out groups that
these procedures do not fully represent.

`scripts/render_documents.py` uses Pandoc and LibreOffice, writes editable DOCX
and PDF under deliverables/, and retains conversion logs. PDF page renderings
are inspected locally. Supplement tables summarize every model and sensitivity;
machine-readable complete tuning, null and sensitivity grids accompany them.

Document rendering additionally uses `python-docx` (tested version 1.1.0) outside
the scientific environment. Run `python3 scripts/render_documents.py`. This host's
virtual `/tmp` cannot create LibreOffice IPC sockets, so the completed render used
`--local-ipc-workaround`: a small local C shim redirects only LibreOffice sockets
into `work/doc-ipc/`, with temporary files also confined there. This option requires
GCC and is unnecessary on ordinary hosts. It has no role in scientific computation.

## External and author boundaries

No controlled-data access, paid compute, wet-lab work or external contact was used.
MIRTH is cited but its restricted implementation was neither executed nor adapted.
No human independent peer review is implied by AI specialist or Academic-agent
checks. Academic's explicit gate and author declarations determine whether the
package may be called author-review ready; no submission or publication is authorized.
