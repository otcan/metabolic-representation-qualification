"""Small synthetic checks of leakage boundaries, budgets, tuning and estimands."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ccle_extension.py"
SPEC = importlib.util.spec_from_file_location("paper1_ccle_extension", SCRIPT)
ccle = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ccle
SPEC.loader.exec_module(ccle)


def empty_signatures(index):
    return pd.DataFrame(index=index)


def test_mean_imputation_then_imputed_population_sd_and_empty_fallback():
    train = np.array([[0., np.nan], [2., np.nan], [10., np.nan], [np.nan, np.nan]])
    test = np.array([[np.nan, np.nan], [8., 7.]])
    z, test_z, info = ccle.standardize(train, test)
    assert info["center"].tolist() == [4., 0.]
    assert info["scale"][0] == pytest.approx(np.sqrt(14))
    assert info["empty_training_features"] == 1
    assert np.isfinite(z).all() and np.isfinite(test_z).all()
    assert test_z[0, 0] == 0
    assert np.std(z[:, 0]) == pytest.approx(1)
    # A feature absent in training learns zero coefficient even when observed in test.
    prediction = ccle.ridge_predict(z[:, 1:], test_z[:, 1:], np.array([-1., 0., 1., 0.]), 1.)
    assert np.allclose(prediction, 0.)


def test_target_never_enters_predictor_transform():
    train = pd.DataFrame({"TARGET": [1., 2., 3.], "A": [3., 2., 1.]})
    target = ccle.Target("TARGET", ("A",), (), ())
    with pytest.raises(ValueError, match="Target is present"):
        ccle.fit_representation("global_pca_ridge", train, train,
                                empty_signatures(train.index), empty_signatures(train.index),
                                np.array([1., 2., 3.]), target)


def test_correlation_selection_uses_training_only_and_keeps_input_budget():
    train = pd.DataFrame({"A": [-2., -1., 1., 2.], "B": [1., -1., -1., 1.]})
    test = pd.DataFrame({"A": [1., 2.], "B": [1000., -1000.]})
    target = ccle.Target("TARGET", ("B",), (), ())
    args = (empty_signatures(train.index), empty_signatures(test.index), train["A"].to_numpy(), target)
    x, _, budget = ccle.fit_representation("correlation_selected_ridge", train, test, *args)
    changed_test = test * 1000000
    x_again, _, budget_again = ccle.fit_representation("correlation_selected_ridge", train, changed_test, *args)
    assert budget["selected_metabolites"] == ["A"]
    assert budget["raw_metabolites"] == 1
    assert budget["selection_candidate_metabolites"] == 2
    assert budget_again["selected_metabolites"] == budget["selected_metabolites"]
    assert np.array_equal(x, x_again)


def test_pca_training_rank_cap_and_no_heldout_transform_fit():
    train = pd.DataFrame({"A": [1., 2., 3., 4.], "B": [2., 4., 6., 8.], "C": [5., 5., 5., 5.]})
    test = pd.DataFrame({"A": [100.], "B": [-100.], "C": [50.]})
    target = ccle.Target("TARGET", ("A", "B"), (), ())
    args = (empty_signatures(train.index), empty_signatures(test.index), np.arange(4.), target)
    fitted, _, budget = ccle.fit_representation("global_pca_ridge", train, test, *args)
    fitted_again, _, budget_again = ccle.fit_representation("global_pca_ridge", train, test * -9, *args)
    assert budget["pca_rank_capped"]
    assert budget["pca_training_rank"] == 1
    assert budget["representation_dimension"] == 1
    assert budget["raw_metabolites"] == 3
    assert np.array_equal(fitted, fitted_again)
    assert np.std(fitted[:, 0], ddof=0) == pytest.approx(1)
    assert budget == budget_again


def test_nested_tuning_fits_transforms_separately_and_weights_groups_not_folds(monkeypatch):
    # Three validation folds have respectively one, one, and two groups. Correct group
    # weighting chooses alpha .1; incorrectly averaging three fold means chooses alpha 1.
    groups = np.array(["a", "b", "c"] + ["d"] * 10)
    frame = pd.DataFrame({"A": np.arange(len(groups), dtype=float)})
    empty = empty_signatures(frame.index)
    tests = [np.array([0]), np.array([1]), np.arange(2, len(groups))]
    splits = [(np.setdiff1d(np.arange(len(groups)), te), te, 0, i) for i, te in enumerate(tests)]
    calls = []

    def representation(model, train_m, test_m, train_t, test_t, train_y, target):
        calls.append((set(train_m.index), set(test_m.index)))
        info = {"selected_metabolites": ["A"], "representation_dimension": 1,
                "empty_training_features": 0, "constant_training_features": 0,
                "pca_rank_capped": False}
        return train_m.to_numpy(), test_m.to_numpy(), info

    def prediction(train_x, test_x, train_y, alpha):
        first_two = test_x[:, 0] < 2
        if alpha == .1:
            losses = np.where(first_two, 3., 0.)
        elif alpha == 1.:
            losses = np.where(first_two, 0., 3.5)
        else:
            losses = np.full(len(test_x), 99.)
        return np.sqrt(losses)

    monkeypatch.setattr(ccle, "fit_representation", representation)
    monkeypatch.setattr(ccle, "ridge_predict", prediction)
    chosen, records = ccle.tune_alpha("direct_neighbor_ridge", frame, empty,
                                      np.zeros(len(groups)), groups,
                                      ccle.Target("TARGET", ("A",), (), ()), splits)
    assert chosen == .1
    assert len(calls) == 3
    assert all(not train & validation for train, validation in calls)
    assert [validation for _, validation in calls] == [set(x) for x in tests]
    assert len(records) == 12
    assert all(r["selection_mean_group_mse"] == pytest.approx(1.5) for r in records if r["alpha"] == .1)


def test_exact_tuning_ties_choose_smaller_alpha(monkeypatch):
    frame = pd.DataFrame({"A": np.zeros(6)})
    groups = np.array(["a", "a", "b", "b", "c", "c"])
    splits = [(np.flatnonzero(groups != g), np.flatnonzero(groups == g), 0, i) for i, g in enumerate(["a", "b", "c"])]
    chosen, records = ccle.tune_alpha("direct_neighbor_ridge", frame, empty_signatures(frame.index),
                                      np.zeros(6), groups, ccle.Target("TARGET", ("A",), (), ()), splits)
    assert chosen == .1
    assert all(r["selection_mean_group_mse"] == 0 for r in records)


def test_transcript_budget_counts_unique_genes_and_products():
    frame = pd.DataFrame({"A": [1., 3., 2., 5.]})
    signatures = pd.DataFrame({"G1;G2": [2., 1., 4., 3.], "G2": [1., 2., 5., 3.]})
    target = ccle.Target("TARGET", ("A",), ("G1;G2", "G2"), (("A", "G1;G2"), ("A", "G2")))
    _, _, budget = ccle.fit_representation("network_interaction_ridge", frame, frame,
                                          signatures, signatures, np.arange(4.), target)
    assert budget["raw_metabolites"] == 1
    assert budget["raw_transcript_genes"] == 2
    assert budget["expression_signatures"] == 2
    assert budget["interaction_count"] == 2
    assert budget["representation_dimension"] == 5
    assert budget["coefficient_count"] == 6


def test_primary_estimand_averages_losses_before_square_root():
    rows = []
    for target, losses in (("A", [1., 9.]), ("B", [16., 36.])):
        for lineage, loss in zip(("L1", "L2"), losses):
            for repeat in (0, 1):
                rows.append({"target": target, "model": "direct_neighbor_ridge", "lineage": lineage,
                             "squared_error_sum": loss * 3, "truth_energy_sum": 100., "observations": 3})
    groups, targets, models = ccle.aggregate_metrics(pd.DataFrame(rows))
    assert len(groups) == 4  # Repeats were reduced within the same target/biological group.
    assert models.iloc[0]["primary_rmse_sd"] == pytest.approx(np.sqrt(15.5))
    assert models.iloc[0]["archived_mean_target_rmse_sd"] == pytest.approx((np.sqrt(5) + np.sqrt(26)) / 2)


def test_lineage_bootstrap_identical_predictions_and_group_count():
    rows = [{"target": target, "lineage": lineage, "model": model,
             "mean_squared_error": float(i + 1)}
            for target in ("A", "B") for i, lineage in enumerate(("L1", "L2", "L3"))
            for model in ("correlation_selected_ridge", "direct_neighbor_ridge")]
    result = ccle.primary_inference(pd.DataFrame(rows), draws=200)
    assert result["biological_groups"] == 3
    assert result["targets"] == 2
    assert result["rmse_improvement_sd"] == 0
    assert result["ci95_lower"] == result["ci95_upper"] == 0
    assert result["signflip_p_two_sided_raw"] == 1


def test_inference_rejects_unpaired_target_lineage_cells():
    rows = [{"target": "A", "lineage": "L1", "model": "direct_neighbor_ridge", "mean_squared_error": 1.},
            {"target": "A", "lineage": "L2", "model": "correlation_selected_ridge", "mean_squared_error": 1.}]
    with pytest.raises(ValueError, match="paired"):
        ccle.primary_inference(pd.DataFrame(rows), draws=10)
