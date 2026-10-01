# Metabolic representation qualification ladder

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23080177.svg)](https://doi.org/10.5281/zenodo.23080177)

Code, tests, aggregate results and figure sources for:

> **Matched nulls and compact baselines qualify metabolic-state representations.**
> Oğuzcan Ünver. Preprint (not peer reviewed), 2026. <https://doi.org/10.5281/zenodo.23080186>

## The idea

A biochemical representation of metabolomics data (pathway, chemical-class or reaction-neighbourhood
scores) is evaluated on a **qualification ladder**:

1. **Training mean** — no structure.
2. **Matched null** — the same shape as the biochemical representation (group sizes, overlaps,
   feature counts or network properties) with membership randomized.
3. **Biochemical representation** — the declared membership.
4. **Compact statistics** — a learned representation of the same size (e.g. PCA).

The step from 2 to 3 shows whether biochemical membership carries information; the step from 3 to 4
shows how much a compact statistical alternative still recovers. Reporting both avoids two opposite
errors: treating "beats random" as competitive, and treating "loses to PCA" as uninformative.

In the study, descriptor medians beat their matched nulls in every dataset, yet dimension-matched PCA
and correlation-selected panels outperformed them in all five primary contrasts (Figure 1 in
`paper/preprint-v1.0.pdf`).

## Contents

| Path | Contents |
| --- | --- |
| `scripts/` | Extension analyses (`human_extension.py`, `ccle_extension.py`), ladder and figure builders, supplement and edition renderers |
| `tests/` | Unit and consistency tests, including checks that every ladder number in the text matches `results/` |
| `results/` | Aggregate model metrics, primary contrasts, information budgets, ladder rungs and steps |
| `evidence/new/` | Per-run summaries, tuning and budget grids for every accepted run |
| `evidence/baseline/` | Reproduction comparison of the earlier released pipeline |
| `evidence/archived-ccle-property-matched-null/` | Archived 20-seed property-matched null ensemble used for the CCLE matched-null step |
| `figures/`, `manuscript/`, `paper/` | Figure files and source data, manuscript sources, preprint PDFs |
| `docs/` | Reproducibility guide and component licence register |

The earlier matched-null software is released separately as v1.0.1:
<https://doi.org/10.5281/zenodo.22207315>.

## Reproducing

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
.venv/bin/python -m pytest -q tests/test_qualification_ladder.py   # ladder consistency from included results
.venv/bin/python scripts/make_qualification_ladder.py               # regenerate Figure 1 and ladder tables
```

Full re-execution of the extension analyses requires the public source data, which are not
redistributed here: Metabolomics Workbench ST002081 (doi:10.21228/M8ZM5P) and ST000818
(doi:10.21228/M89M31), the CCLE 2019 metabolomics and expression release, and Human-GEM v2.0.0.
See `docs/REPRODUCIBILITY.md`.

## Data boundary

Raw source matrices and participant-linked losses or split maps are not included. All files here are
aggregates or summaries without participant identifiers.

## Licences

Code: Apache-2.0 (`LICENSE`). Manuscript text, figures and newly authored aggregate tables: CC BY 4.0
(`LICENSES/CC-BY-4.0.txt`). Source datasets retain their own terms.
