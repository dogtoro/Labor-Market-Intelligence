"""Tests for src/models/comparison.py on small synthetic data (no frozen data needed)."""
import numpy as np
import pandas as pd
import pytest
from sklearn.tree import DecisionTreeClassifier

from src.models import classification as clf
from src.models import clustering as cl
from src.models import comparison as cmp


@pytest.fixture
def toy_xy():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.integers(0, 2, size=(90, 6)), columns=[f"lvl_{i}" for i in range(3)] + ["a", "b", "c"])
    y = pd.Series(np.where(X["lvl_0"] == 1, "Low", np.where(X["a"] == 1, "High", "Mid")))
    return X, y


def test_nested_cv_predict_matches_project_tree(toy_xy):
    X, y = toy_xy
    tree = DecisionTreeClassifier(criterion="gini", random_state=clf.RANDOM_STATE)
    ours = cmp.nested_cv_predict(tree, clf.PARAM_GRID, X, y)
    ref, _ = clf.nested_cv(X, y)
    assert (ours == ref).all()


def test_paired_bootstrap_diff_is_zero_for_identical_predictions(toy_xy):
    _, y = toy_xy
    y_arr = y.to_numpy(dtype=object)
    assert cmp.paired_bootstrap_diff(y_arr, y_arr, y_arr, n=50) == (0.0, 0.0)


def test_compare_classifiers_uses_feature_subsets(toy_xy):
    X, y = toy_xy
    specs = {k: v for k, v in cmp.classifier_specs().items()
             if k.startswith(("Majority", "Seniority", "Decision tree"))}
    table, preds = cmp.compare_classifiers(X, y, specs)
    assert table.loc["Seniority only (decision tree)", "n_features"] == 3
    assert set(preds) == set(specs)
    assert table.loc["Decision tree (CART) — project model", "diff_vs_tree_low"] == 0.0


def test_clustering_matrix_applies_project_filters():
    rng = np.random.default_rng(1)
    common = np.ones(100, dtype=int)                       # in > 40% of jobs → dropped
    rare = np.r_[np.ones(3, dtype=int), np.zeros(97, dtype=int)]  # < 10 jobs → dropped
    df = pd.DataFrame({"job_id": [f"j{i}" for i in range(100)], "common": common, "rare": rare,
                       "english": rng.integers(0, 2, 100),  # manual drop
                       **{f"s{i}": (rng.random(100) < 0.3).astype(int) for i in range(4)}})
    M = cmp.clustering_matrix(df)
    assert not {"common", "rare", "english"} & set(M.columns)
    assert (M.sum(axis=1) >= cl.MIN_SKILLS_PER_JOB).all()


def test_best_over_k_survives_collapsed_clusterings():
    D = np.zeros((40, 40))
    groups = np.array(["A"] * 40)
    res = cmp._best_over_k(lambda k: np.ones(40, dtype=int), D, groups)  # always one cluster
    assert res["n_real_clusters"] == 1 and not res["valid"]


def test_apriori_and_fpgrowth_give_identical_rules():
    rng = np.random.default_rng(2)
    base = rng.random(200) < 0.5
    data = pd.DataFrame({"x": base, "y": base | (rng.random(200) < 0.1), "z": rng.random(200) < 0.4})
    table = cmp.compare_apriori_fpgrowth(data, supports=[0.1, 0.2], repeats=1)
    assert table["same_itemsets"].all() and table["same_rules"].all()
