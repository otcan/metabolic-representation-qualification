#!/usr/bin/env python3
"""Post-release CCLE benchmark under the immutable Paper 1 M2 v1 specification.

Generic NumPy SVD and sklearn ridge implementations; no MIRTH or other prior-art
package code is used. Run only after coordinating the four-worker project cap.
"""
from __future__ import annotations

import os
for _thread_variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                         "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread_variable] = "1"

import argparse
import csv
import gzip
import hashlib
import importlib.metadata
import json
import platform
import resource
import shlex
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_info, threadpool_limits

WORKSPACE = Path(__file__).resolve().parents[1]
LOCK_SHA256 = "b0bb3f38101a4d469eef9cc4cf4479433e0a57536df6edf15a74f2194f9def4f"
ALPHAS = (0.1, 1.0, 10.0, 100.0)
MODELS = ("population_mean", "direct_neighbor_ridge", "correlation_selected_ridge",
          "global_pca_ridge", "all_other_metabolites_ridge", "network_additive_ridge",
          "network_interaction_ridge")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity_hash(values: Any) -> str:
    return hashlib.sha256(json.dumps(list(map(str, values)), separators=(",", ":")).encode()).hexdigest()


def json_write(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def configure_archive(release: Path) -> None:
    source = str(release.resolve() / "src")
    if source not in sys.path:
        sys.path.insert(0, source)


def grouped_splits(groups: np.ndarray, folds: int, repeats: int, seed: int):
    from genotype_gated_metabolism.ml.validation import (
        GroupedValidationSpec, repeated_balanced_group_splits,
    )
    return repeated_balanced_group_splits(
        groups, GroupedValidationSpec(outer_folds=folds, repeats=repeats, seed=seed)
    )


@dataclass(frozen=True)
class Target:
    name: str
    metabolites: tuple[str, ...]
    signatures: tuple[str, ...]
    interactions: tuple[tuple[str, str], ...]


def standardize(train: np.ndarray, test: np.ndarray):
    """Fit mean imputation then population-SD scaling on training rows only."""
    train = np.asarray(train, dtype=float)
    test = np.asarray(test, dtype=float)
    finite = np.isfinite(train)
    count = finite.sum(axis=0)
    center = np.divide(np.where(finite, train, 0.0).sum(axis=0), count,
                       out=np.zeros(train.shape[1]), where=count > 0)
    train_filled = np.where(finite, train, center)
    test_filled = np.where(np.isfinite(test), test, center)
    scale = np.std(train_filled, axis=0, ddof=0)
    constant = ~np.isfinite(scale) | (scale <= 1e-12)
    scale = np.where(constant, 1.0, scale)
    # Entirely absent training features carry no learned signal, even if observed in test.
    train_z = (train_filled - center) / scale
    test_z = (test_filled - center) / scale
    return train_z, test_z, {
        "empty_training_features": int((count == 0).sum()),
        "constant_training_features": int(constant.sum()),
        "center": center, "scale": scale,
    }


def target_standardize(train_y: np.ndarray, test_y: np.ndarray):
    if not np.isfinite(train_y).all() or not np.isfinite(test_y).all():
        raise ValueError("Target observations must be finite before splitting.")
    center = float(np.mean(train_y))
    scale = float(np.std(train_y, ddof=0))
    constant = not np.isfinite(scale) or scale <= 1e-12
    if constant:
        scale = 1.0
    return (train_y - center) / scale, (test_y - center) / scale, center, scale, constant


def fit_representation(model: str, train_m: pd.DataFrame, test_m: pd.DataFrame,
                       train_t: pd.DataFrame, test_t: pd.DataFrame,
                       train_y: np.ndarray, target: Target):
    """Return a fold-fitted representation; target data are never in metabolite inputs."""
    if target.name in train_m or target.name in test_m:
        raise ValueError("Target is present in candidate predictor matrix.")
    if not train_m.columns.equals(test_m.columns) or not train_t.columns.equals(test_t.columns):
        raise ValueError("Training and test schemas differ.")
    pool = sorted(train_m.columns)
    k = len(target.metabolites)
    if target.name in target.metabolites or any(m == target.name for m, _ in target.interactions):
        raise ValueError("Direct target leakage in network map.")
    info: dict[str, Any] = {"model": model, "selection_candidate_metabolites": 0,
                            "raw_transcript_genes": 0, "expression_signatures": 0,
                            "interaction_count": 0, "pca_requested_components": 0,
                            "pca_training_rank": 0, "pca_rank_capped": False}
    if model == "population_mean":
        info.update(raw_metabolites=0, representation_dimension=0,
                    empty_training_features=0, constant_training_features=0,
                    selected_metabolites=[], selected_signatures=[],
                    transform_learned_parameters=0, coefficient_count=1)
        return np.empty((len(train_m), 0)), np.empty((len(test_m), 0)), info
    if model == "correlation_selected_ridge":
        # Selection may inspect the training candidate panel, but prediction reads only
        # the selected test markers; unused held-out assays never enter this operation.
        raw_train, _, scan = standardize(train_m[pool].to_numpy(), np.empty((0, len(pool))))
        y_centered = train_y - np.mean(train_y)
        y_scale = float(np.std(y_centered))
        correlations = (raw_train.T @ y_centered) / (len(train_y) * y_scale) if y_scale > 1e-12 else np.zeros(len(pool))
        order = np.argsort(-np.abs(correlations), kind="stable")
        members = sorted(pool[int(i)] for i in order[:k])
        info["selection_candidate_metabolites"] = len(pool)
        info["selection_empty_candidates"] = scan["empty_training_features"]
    elif model in ("global_pca_ridge", "all_other_metabolites_ridge"):
        members = pool
    elif model in ("direct_neighbor_ridge", "network_additive_ridge", "network_interaction_ridge"):
        members = list(target.metabolites)
    else:
        raise ValueError(f"Unknown model: {model}")
    signature_names = list(target.signatures) if model in ("network_additive_ridge", "network_interaction_ridge") else []
    train_blocks = [train_m[members].to_numpy()]
    test_blocks = [test_m[members].to_numpy()]
    if signature_names:
        train_blocks.append(train_t[signature_names].to_numpy())
        test_blocks.append(test_t[signature_names].to_numpy())
    train_x, test_x, moments = standardize(np.column_stack(train_blocks), np.column_stack(test_blocks))
    info.update(raw_metabolites=len(members), selected_metabolites=members,
                selected_signatures=signature_names, expression_signatures=len(signature_names),
                raw_transcript_genes=len({gene for signature in signature_names for gene in signature.split(";")}),
                empty_training_features=moments["empty_training_features"],
                constant_training_features=moments["constant_training_features"],
                transform_learned_parameters=2 * train_x.shape[1])
    if model == "global_pca_ridge":
        # Standardized training columns are centered; recenter explicitly for numerical clarity.
        center = train_x.mean(axis=0)
        centered = train_x - center
        _, singular, vt = np.linalg.svd(centered, full_matrices=False)
        tolerance = (singular[0] if len(singular) else 0.0) * max(centered.shape) * np.finfo(float).eps
        rank = int((singular > tolerance).sum())
        components = min(k, len(train_x) - 1, train_x.shape[1], rank)
        components = max(0, components)
        loadings = vt[:components].T
        train_x, test_x = centered @ loadings, (test_x - center) @ loadings
        # Pre-pilot convention shared with the human extension: ridge receives unit-SD
        # component scores, with component moments fitted on training rows only.
        train_x, test_x, _ = standardize(train_x, test_x)
        info.update(pca_requested_components=k, pca_training_rank=rank,
                    pca_rank_capped=components < k,
                    transform_learned_parameters=info["transform_learned_parameters"] + len(center) + loadings.size + 2 * components)
    if model == "network_interaction_ridge":
        metabolite_index = {value: i for i, value in enumerate(members)}
        signature_index = {value: len(members) + i for i, value in enumerate(signature_names)}
        products_train = np.column_stack([train_x[:, metabolite_index[m]] * train_x[:, signature_index[t]] for m, t in target.interactions])
        products_test = np.column_stack([test_x[:, metabolite_index[m]] * test_x[:, signature_index[t]] for m, t in target.interactions])
        products_train, products_test, product_info = standardize(products_train, products_test)
        train_x = np.column_stack([train_x, products_train])
        test_x = np.column_stack([test_x, products_test])
        info.update(interaction_count=len(target.interactions),
                    constant_interactions=product_info["constant_training_features"],
                    transform_learned_parameters=info["transform_learned_parameters"] + 2 * len(target.interactions))
    info.update(representation_dimension=train_x.shape[1], coefficient_count=train_x.shape[1] + 1)
    if not np.isfinite(train_x).all() or not np.isfinite(test_x).all():
        raise ValueError("Nonfinite transformed predictors.")
    return train_x, test_x, info


def ridge_predict(train_x: np.ndarray, test_x: np.ndarray, train_y: np.ndarray, alpha: float):
    if train_x.shape[1] == 0:
        return np.full(len(test_x), float(np.mean(train_y)))
    return Ridge(alpha=alpha, solver="lsqr").fit(train_x, train_y).predict(test_x)


def tune_alpha(model: str, metabolites: pd.DataFrame, signatures: pd.DataFrame,
               outcome: np.ndarray, groups: np.ndarray, target: Target, splits: list):
    records = []
    group_losses: dict[float, list[float]] = {alpha: [] for alpha in ALPHAS}
    for train, validation, repeat, fold in splits:
        if set(groups[train]) & set(groups[validation]):
            raise ValueError("Inner group leakage.")
        train_y, validation_y, _, _, constant = target_standardize(outcome[train], outcome[validation])
        x_train, x_validation, budget = fit_representation(
            model, metabolites.iloc[train], metabolites.iloc[validation],
            signatures.iloc[train], signatures.iloc[validation], train_y, target,
        )
        for alpha in ALPHAS:
            prediction = ridge_predict(x_train, x_validation, train_y, alpha)
            loss = (validation_y - prediction) ** 2
            by_group = pd.Series(loss).groupby(groups[validation]).mean()
            group_losses[alpha].extend(by_group.tolist())
            records.append({"inner_fold": fold, "alpha": alpha,
                            "validation_groups": len(by_group), "mean_group_mse": float(by_group.mean()),
                            "training_target_constant": constant,
                            "inner_training_sample_digest": identity_hash(metabolites.index[train]),
                            "inner_validation_sample_digest": identity_hash(metabolites.index[validation]),
                            "selected_metabolites": json.dumps(budget["selected_metabolites"]),
                            "representation_dimension": budget["representation_dimension"],
                            "empty_training_features": budget["empty_training_features"],
                            "constant_training_features": budget["constant_training_features"],
                            "pca_rank_capped": budget["pca_rank_capped"]})
    means = {alpha: float(np.mean(group_losses[alpha])) for alpha in ALPHAS}
    chosen = min(ALPHAS, key=lambda alpha: (means[alpha], alpha))
    for record in records:
        record["selection_mean_group_mse"] = means[record["alpha"]]
        record["selected"] = record["alpha"] == chosen
    return chosen, records


def load_inputs(release: Path):
    configure_archive(release)
    from genotype_gated_metabolism.datasets.ccle import CCLE_FILES, load_ccle
    from genotype_gated_metabolism.features.signatures import parse_gene_signature
    from genotype_gated_metabolism.analysis.ccle_pathway_prediction import build_signature_matrix, target_feature_sets
    artifact = release / "artifacts/pathway-score-ccle"
    manifest = json.loads((artifact / "manifest.json").read_text())
    paths = {"mapping": release / "artifacts/ccle-expanded/ccle_metabolite_mapping.csv",
             "candidates": release / "artifacts/ccle-expanded/ccle_candidate_hypotheses.csv",
             "source_manifest": release / "artifacts/ccle-expanded/ccle_proof_manifest.json"}
    for key, path in paths.items():
        if sha256(path) != manifest["source_sha256"][key]:
            raise ValueError(f"Archived source pin mismatch: {key}")
    archived_features_path = artifact / "target-feature-sets.csv"
    if sha256(archived_features_path) != manifest["output_sha256"][archived_features_path.name]:
        raise ValueError("Archived target-definition pin mismatch")
    mapping = pd.read_csv(paths["mapping"])
    candidates = pd.read_csv(paths["candidates"])
    if len(candidates) != 317:
        raise ValueError("Expected exactly 317 frozen candidate rows")
    mapped = sorted(mapping.loc[mapping["mapping_status"].eq("mapped"), "assay_metabolite_id"].astype(str))
    genes = sorted({gene for value in candidates["genes"].dropna().astype(str) for gene in parse_gene_signature(value)})
    raw = release / "data/raw/ccle/2019"
    dataset = load_ccle(raw, genes)  # Loader verifies all three fixed source checksums.
    metabolites = dataset.blocks["metabolomics"].loc[:, mapped]
    if metabolites.index.duplicated().any():
        raise ValueError("Duplicate biological sample identifiers")
    signatures = build_signature_matrix(dataset.blocks["transcriptomics"], candidates["genes"].dropna().astype(str).tolist(), aggregation="limiting_subunit")
    archived = pd.read_csv(archived_features_path).set_index("target")
    definitions = target_feature_sets(candidates, mapped_metabolites=mapped,
                                     available_signatures=list(signatures.columns), seed=20260831)
    targets = []
    for feature in definitions:
        if feature.target not in archived.index:
            continue
        row = archived.loc[feature.target]
        for key, actual in (("network_metabolites", feature.network_metabolites),
                            ("network_signatures", feature.network_signatures)):
            if ";".join(actual) != row[key]:
                raise ValueError(f"Rebuilt archived feature definition differs: {feature.target}/{key}")
        if ";".join(f"{m}*{t}" for m, t in feature.network_interactions) != row["network_interactions"]:
            raise ValueError("Rebuilt interaction map differs")
        targets.append(Target(feature.target, feature.network_metabolites, feature.network_signatures, feature.network_interactions))
    if len(targets) != 60 or {t.name for t in targets} != set(archived.index):
        raise ValueError("Frozen 60-target set could not be reconstructed exactly")
    provenance = {key: {"path": str(path), "sha256": sha256(path)} for key, path in paths.items()}
    provenance["target_definitions"] = {"path": str(archived_features_path), "sha256": sha256(archived_features_path)}
    provenance["raw_ccle"] = {name: {"path": str(raw / name), "sha256": value} for name, value in CCLE_FILES.items()}
    provenance["archived_code"] = {str(path.relative_to(release)): sha256(path) for path in (
        release / "src/genotype_gated_metabolism/datasets/ccle.py",
        release / "src/genotype_gated_metabolism/analysis/ccle_pathway_prediction.py",
        release / "src/genotype_gated_metabolism/ml/validation.py",
        release / "src/genotype_gated_metabolism/features/signatures.py")}
    return metabolites, signatures, dataset.sample_metadata["lineage"], targets, archived, provenance


def aggregate_metrics(fold_losses: pd.DataFrame):
    grouped = fold_losses.groupby(["target", "model", "lineage"], as_index=False).agg(
        squared_error_sum=("squared_error_sum", "sum"), truth_energy_sum=("truth_energy_sum", "sum"),
        observations=("observations", "sum"))
    grouped["mean_squared_error"] = grouped["squared_error_sum"] / grouped["observations"]
    targets = grouped.groupby(["target", "model"], as_index=False).agg(
        mean_lineage_mse=("mean_squared_error", "mean"), available_lineages=("lineage", "nunique"),
        squared_error_sum=("squared_error_sum", "sum"), truth_energy_sum=("truth_energy_sum", "sum"),
        prediction_rows=("observations", "sum"))
    targets["equal_lineage_rmse_sd"] = np.sqrt(targets["mean_lineage_mse"])
    targets["row_weighted_rmse_sd"] = np.sqrt(targets["squared_error_sum"] / targets["prediction_rows"])
    targets["skill_vs_training_mean"] = 1 - targets["squared_error_sum"] / targets["truth_energy_sum"]
    models = targets.groupby("model", as_index=False).agg(
        targets=("target", "nunique"), mean_target_lineage_mse=("mean_lineage_mse", "mean"),
        archived_mean_target_rmse_sd=("equal_lineage_rmse_sd", "mean"),
        median_target_skill=("skill_vs_training_mean", "median"),
        squared_error_sum=("squared_error_sum", "sum"), prediction_rows=("prediction_rows", "sum"))
    models["primary_rmse_sd"] = np.sqrt(models["mean_target_lineage_mse"])
    models["descriptive_row_weighted_rmse_sd"] = np.sqrt(models["squared_error_sum"] / models["prediction_rows"])
    return grouped, targets, models


def primary_inference(group_losses: pd.DataFrame, draws: int = 10000):
    reference, mechanism = "correlation_selected_ridge", "direct_neighbor_ridge"
    targets = sorted(group_losses["target"].unique())
    lineages = sorted(group_losses["lineage"].unique())
    arrays = []
    for model in (reference, mechanism):
        arrays.append(group_losses.loc[group_losses["model"].eq(model)].pivot(
            index="target", columns="lineage", values="mean_squared_error").reindex(index=targets, columns=lineages).to_numpy())
    ref, mech = arrays
    valid = np.isfinite(ref) & np.isfinite(mech)
    if not np.array_equal(np.isfinite(ref), np.isfinite(mech)) or not valid.any(axis=1).all():
        raise ValueError("Primary models lack paired target-lineage observations")
    ref0, mech0 = np.where(valid, ref, 0.0), np.where(valid, mech, 0.0)
    denominator = valid.sum(axis=1)
    point = float(np.sqrt((ref0.sum(axis=1) / denominator).mean()) - np.sqrt((mech0.sum(axis=1) / denominator).mean()))
    rng = np.random.default_rng(20260921)
    improvements = []
    rejected = 0
    # Bootstrap shared lineage labels while preserving fixed targets and missingness pattern.
    while len(improvements) < draws:
        indices = rng.integers(0, len(lineages), size=min(256, draws - len(improvements)) * len(lineages)).reshape(-1, len(lineages))
        weights = np.stack([np.bincount(row, minlength=len(lineages)) for row in indices])
        counts = weights @ valid.T
        keep = (counts > 0).all(axis=1)
        rejected += int((~keep).sum())
        if rejected > draws * 100:
            raise ValueError("Insufficient common lineage support for fixed-target bootstrap")
        selected, counts = weights[keep], counts[keep]
        ref_rmse = np.sqrt(((selected @ ref0.T) / counts).mean(axis=1))
        mech_rmse = np.sqrt(((selected @ mech0.T) / counts).mean(axis=1))
        improvements.extend((ref_rmse - mech_rmse).tolist())
    bootstrap = np.asarray(improvements)
    # Flip the paired MSE contrast jointly for each lineage across all fixed targets.
    group_contributions = ((ref0 - mech0) / denominator[:, None]).mean(axis=0)
    observed_mse_difference = float(group_contributions.sum())
    flip_rng = np.random.default_rng(20260922)
    extreme = 0
    for start in range(0, draws, 256):
        signs = flip_rng.choice(np.asarray([-1.0, 1.0]), size=(min(256, draws - start), len(lineages)))
        permuted = signs @ group_contributions
        extreme += int((np.abs(permuted) >= abs(observed_mse_difference) - 1e-15).sum())
    return {"comparison": "ccle_direct_neighbor_vs_correlation_selected", "reference": reference,
            "mechanism": mechanism, "targets": len(targets), "biological_groups": len(lineages),
            "rmse_improvement_sd": point, "draws": draws,
            "ci95_lower": float(np.quantile(bootstrap, .025)), "ci95_upper": float(np.quantile(bootstrap, .975)),
            "simultaneous99_lower": float(np.quantile(bootstrap, .005)), "simultaneous99_upper": float(np.quantile(bootstrap, .995)),
            "simultaneous_family_size": 5, "signflip_mse_difference": observed_mse_difference,
            "signflip_p_two_sided_raw": (extreme + 1) / (draws + 1),
            "holm_status": "requires joint adjustment with four human primary contrasts",
            "bootstrap_rejected_draws_without_all_targets": rejected,
            "uncertainty_scope": "conditional on fixed fitted predictions and target panel; lineage resampling, not full-pipeline refitting"}


def execute(args: argparse.Namespace) -> dict[str, Any]:
    started = time.monotonic()
    output, private = args.output.resolve(), args.private_output.resolve()
    if WORKSPACE not in output.parents or (WORKSPACE / "work") not in private.parents:
        raise ValueError("Outputs must be inside this workspace; individual predictions must be under work/")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty output: {output}")
    if private.exists() and any(private.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty private output: {private}")
    protocol = WORKSPACE / "readiness/m2-benchmark-lock-v1.md"
    if sha256(protocol) != LOCK_SHA256:
        raise ValueError("M2 v1 protocol hash changed")
    code_hash = sha256(Path(__file__))
    output.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    json_write(output / "live.json", {"state": "loading", "pid": os.getpid(), "started_at": datetime.now(timezone.utc).isoformat()})
    metabolites, signatures, lineages, targets, archived, provenance = load_inputs(args.release.resolve())
    full_target_count = len(targets)
    if args.max_targets is not None:
        if args.max_targets < 1:
            raise ValueError("--max-targets must be positive")
        targets = targets[:args.max_targets]
    pilot = len(targets) < full_target_count
    fold_losses, tuning, budgets, split_records, exclusions = [], [], [], [], []
    predictions_path = private / "predictions.csv.gz"
    prediction_fields = ["target", "sample_id", "lineage", "repeat", "fold", "model", "observed_sd", "predicted_sd", "squared_error"]
    with gzip.open(predictions_path, "wt", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=prediction_fields)
        writer.writeheader()
        for target_index, target in enumerate(targets):
            target_start = time.monotonic()
            available = metabolites[target.name].notna() & lineages.notna()
            counts = lineages.loc[available].astype(str).value_counts()
            retained = set(counts.loc[counts >= 15].index)
            available &= lineages.astype(str).isin(retained)
            indexes = np.flatnonzero(available.to_numpy())
            if len(indexes) < 300 or len(retained) < 5:
                raise ValueError(f"Frozen target no longer eligible: {target.name}")
            if len(indexes) != int(archived.loc[target.name, "samples"]) or len(retained) != int(archived.loc[target.name, "lineages"]):
                raise ValueError(f"Eligibility changed relative to archived target: {target.name}")
            local_m = metabolites.iloc[indexes].drop(columns=target.name)
            local_t = signatures.iloc[indexes]
            local_y = metabolites[target.name].iloc[indexes].to_numpy(dtype=float)
            local_g = lineages.iloc[indexes].astype(str).to_numpy()
            outer = grouped_splits(local_g, folds=5, repeats=2, seed=20260830)
            exclusions.append({"target": target.name, "aligned_samples": len(metabolites),
                               "retained_samples": len(indexes), "excluded_samples": len(metabolites) - len(indexes),
                               "retained_lineages": len(retained), "eligibility": "archived global target-observation and lineage-size metadata restriction"})
            for train, test, repeat, fold in outer:
                train_y, test_y, target_center, target_scale, constant = target_standardize(local_y[train], local_y[test])
                inner_seed = 20260921 + repeat * 100 + fold
                inner = grouped_splits(local_g[train], folds=3, repeats=1, seed=inner_seed)
                split_hash = identity_hash([identity_hash(local_m.index[train]), identity_hash(local_m.index[test])])
                for kind, selected in (("train", train), ("test", test)):
                    for lineage in sorted(set(local_g[selected])):
                        split_records.append({"target": target.name, "repeat": repeat, "fold": fold,
                                              "partition": kind, "lineage": lineage,
                                              "samples": int((local_g[selected] == lineage).sum()),
                                              "split_digest": split_hash, "inner_seed": inner_seed})
                for model in MODELS:
                    before = time.monotonic()
                    chosen = None
                    if model != "population_mean":
                        chosen, local_tuning = tune_alpha(model, local_m.iloc[train], local_t.iloc[train],
                                                          local_y[train], local_g[train], target, inner)
                        tuning.extend({"target": target.name, "model": model, "repeat": repeat,
                                       "outer_fold": fold, "split_digest": split_hash, **row} for row in local_tuning)
                    training_x, test_x, budget = fit_representation(model, local_m.iloc[train], local_m.iloc[test],
                                                                   local_t.iloc[train], local_t.iloc[test], train_y, target)
                    prediction = ridge_predict(training_x, test_x, train_y, chosen or 10.0)
                    squared = (test_y - prediction) ** 2
                    if not np.isfinite(squared).all():
                        raise ValueError(f"Nonfinite predictions: {target.name}/{model}/{repeat}/{fold}")
                    for lineage in sorted(set(local_g[test])):
                        keep = local_g[test] == lineage
                        fold_losses.append({"target": target.name, "model": model, "lineage": lineage,
                                            "repeat": repeat, "fold": fold, "observations": int(keep.sum()),
                                            "squared_error_sum": float(squared[keep].sum()),
                                            "truth_energy_sum": float((test_y[keep] ** 2).sum()), "split_digest": split_hash})
                    for j, original in enumerate(test):
                        writer.writerow({"target": target.name, "sample_id": str(local_m.index[original]),
                                         "lineage": local_g[original], "repeat": repeat, "fold": fold, "model": model,
                                         "observed_sd": float(test_y[j]), "predicted_sd": float(prediction[j]),
                                         "squared_error": float(squared[j])})
                    budget.update(target=target.name, repeat=repeat, outer_fold=fold,
                                  selected_alpha=chosen, training_samples=len(train), test_samples=len(test),
                                  training_groups=len(set(local_g[train])), test_groups=len(set(local_g[test])),
                                  target_center=target_center, target_scale=target_scale,
                                  training_target_constant=constant, split_digest=split_hash,
                                  elapsed_seconds=time.monotonic() - before)
                    for key in ("selected_metabolites", "selected_signatures"):
                        budget[key] = json.dumps(budget[key])
                    budgets.append(budget)
            json_write(output / "live.json", {"state": "running", "pid": os.getpid(), "completed_targets": target_index + 1,
                       "total_targets": len(targets), "last_target": target.name,
                       "last_target_seconds": time.monotonic() - target_start,
                       "elapsed_seconds": time.monotonic() - started})
            # Group-only checkpoints remain reviewable without committing individual records.
            pd.DataFrame(fold_losses).to_csv(output / "fold-lineage-losses.csv", index=False)
            pd.DataFrame(budgets).to_csv(output / "budgets.csv", index=False)
            pd.DataFrame(tuning).to_csv(output / "tuning.csv", index=False)
    groups, target_metrics, model_metrics = aggregate_metrics(pd.DataFrame(fold_losses))
    groups.to_csv(output / "lineage-target-losses.csv", index=False)
    target_metrics.to_csv(output / "target-metrics.csv", index=False)
    model_metrics.to_csv(output / "model-metrics.csv", index=False)
    pd.DataFrame(split_records).to_csv(output / "split-ledger.csv", index=False)
    pd.DataFrame(exclusions).to_csv(output / "eligibility.csv", index=False)
    inference = primary_inference(groups)
    inference["pilot_not_full_panel_inference"] = pilot
    json_write(output / "primary-comparison.json", inference)
    if sha256(Path(__file__)) != code_hash:
        raise RuntimeError("Script changed during execution; results require provenance review")
    outputs = {path.name: sha256(path) for path in output.iterdir() if path.name != "live.json" and path.is_file()}
    manifest = {"analysis": "ccle_adaptive_extension_v1", "completed_at": datetime.now(timezone.utc).isoformat(),
                "state": "PILOT_COMPLETE" if pilot else "COMPLETE", "pilot": pilot,
                "post_release_adaptive": True, "targets": len(targets), "full_archived_targets": full_target_count,
                "target_names": [target.name for target in targets], "models": list(MODELS),
                "alpha_grid": list(ALPHAS), "outer_seed": 20260830,
                "inner_seed_rule": "20260921 + outer_repeat * 100 + outer_fold",
                "alpha_tie_break": "exact equal mean group MSE: smaller alpha",
                "imputation_scaling": "training arithmetic mean, then population SD of imputed training rows; empty mean=0, zero SD=1",
                "primary_metric": "sqrt(mean_target(mean_available_lineage(mean_cell_and_repeat_squared_error)))",
                "correlation_selection": "absolute training Pearson correlation after mean imputation, stable lexical ties; same direct-neighbor count",
                "pca": "all other mapped metabolites; component count matches direct-neighbor count capped by centered training rank; scores standardized to training population SD before ridge; representation-size matched only",
                "code_sha256": code_hash, "protocol_sha256": LOCK_SHA256, "protocol_path": str(protocol),
                "command": shlex.join([sys.executable, *sys.argv]), "pid": os.getpid(),
                "software": {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn", "threadpoolctl")},
                "python": sys.version, "platform": platform.platform(), "threadpools": threadpool_info(),
                "max_workers": 1, "elapsed_seconds": time.monotonic() - started,
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "input_provenance": provenance, "outputs_sha256": outputs,
                "private_predictions": {"path": str(predictions_path), "sha256": sha256(predictions_path)},
                "limitations": ["retrospective frozen mapping and global eligibility; not new blind validation",
                                "training lines equally weighted, evaluation lineages equally weighted within target",
                                "fixed-target conditional uncertainty; no pipeline bootstrap or frozen-model cross-cohort transfer",
                                "no external prior-art-specific package executed; generic NumPy SVD and sklearn ridge",
                                "Holm adjustment requires all five locked primary comparisons"]}
    json_write(output / "manifest.json", manifest)
    json_write(output / "live.json", {"state": manifest["state"], "pid": os.getpid(), "elapsed_seconds": manifest["elapsed_seconds"]})
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=WORKSPACE / "work/release")
    parser.add_argument("--output", type=Path, default=WORKSPACE / "runs/m2-ccle")
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--max-targets", type=int, help="Deterministic sorted-prefix pilot; never treated as full-panel evidence")
    args = parser.parse_args()
    args.private_output = args.private_output or WORKSPACE / "work/m2-ccle" / args.output.name
    try:
        with threadpool_limits(limits=1):
            result = execute(args)
    except Exception as exc:
        live = args.output / "live.json"
        owned_output = False
        if live.exists() and WORKSPACE in args.output.resolve().parents:
            try:
                owned_output = json.loads(live.read_text()).get("pid") == os.getpid()
            except (OSError, ValueError):
                pass
        if owned_output:
            json_write(args.output / "failure.json", {"state": "FAILED", "pid": os.getpid(),
                       "error_type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        raise
    print(json.dumps({key: result[key] for key in ("state", "targets", "elapsed_seconds", "peak_rss_kib")}, indent=2))


if __name__ == "__main__":
    main()
