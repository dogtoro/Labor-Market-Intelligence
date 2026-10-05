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


def test_paired_bootstrap_clustering_zero_for_identical_labels():
    rng = np.random.default_rng(3)
    labels = rng.integers(1, 4, 120)
    groups = np.array(["A", "B", "C"])[rng.integers(0, 3, 120)]
    out = cmp.paired_bootstrap_clustering(labels, labels, groups, n=30)
    assert (out["diff"] == 0).all() and (out["ci_low"] == 0).all() and (out["ci_high"] == 0).all()


@pytest.mark.parametrize("method", ["weighted", "kmeans"])
def test_clustering_stability_is_perfect_on_well_separated_data(method):
    # 3 disjoint skill blocks, 40 jobs each → every method should recover the same clusters on any subsample
    blocks = np.zeros((120, 9), dtype=bool)
    for b in range(3):
        blocks[b * 40:(b + 1) * 40, b * 3:(b + 1) * 3] = True
    M = pd.DataFrame(blocks, columns=[f"s{i}" for i in range(9)])
    scores = cmp.clustering_stability(M, k=3, method=method, n=5)
    assert np.allclose(scores, 1.0)


def test_labels_with_n_real_finds_requested_cluster_count():
    blocks = np.zeros((120, 9), dtype=bool)
    for b in range(3):
        blocks[b * 40:(b + 1) * 40, b * 3:(b + 1) * 3] = True
    for method in ("weighted", "kmeans"):
        k, labels = cmp.labels_with_n_real(blocks, method, n_real=3)
        assert k == 3 and len(set(labels)) == 3
    assert cmp.labels_with_n_real(blocks, "kmeans", n_real=50, k_max=5) == (None, None)
