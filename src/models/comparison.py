"""Comparison with alternative methods (lecturer requirement, docs/DECISIONS.md 04/10).

Every alternative is run on exactly the same data, folds and metrics as the model the
project uses, and the project's own model is re-run inside this module and checked
against its committed output, so the comparison is like-for-like:

- Q3 salary band: decision tree vs other classifiers, same nested CV
  (outer 5 folds / inner 3 folds) as src/models/classification.py, bootstrap CI and a
  paired bootstrap CI of the accuracy difference vs the decision tree.
- Q2 clustering: weighted HAC (the project's choice) vs average/complete HAC, K-means
  and HDBSCAN on the same filtered skill matrix and the same noise rule as
  src/models/clustering.py, plus a subsampling stability check (ARI).
- Q1 association rules: Apriori vs FP-Growth — same rules, different runtime.

Run: python -m src.models.comparison   (→ reports/model_comparison.md + figures)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori as mlx_apriori
from mlxtend.frequent_patterns import association_rules, fpgrowth
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, adjusted_rand_score, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import BernoulliNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils import resample

from src.models import apriori as ap
from src.models import classification as clf
from src.models import clustering as cl
from src.models.features import load_and_verify_data

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = PROJECT_ROOT / "reports" / "model_comparison.md"
FIG_DIR = PROJECT_ROOT / "reports" / "figures"
RANDOM_STATE = clf.RANDOM_STATE
N_STABILITY = 50          # subsamples for the clustering stability check
STABILITY_FRAC = 0.8      # each subsample keeps 80% of the clustered jobs
APRIORI_SUPPORTS = [0.03, 0.04, 0.05, 0.06, 0.10]  # same grid as src/models/apriori.py
TIMING_REPEATS = 5


# ---------------------------------------------------------------------------
# Q3 — classifiers
# ---------------------------------------------------------------------------

def _to_bool(X):
    return np.asarray(X).astype(bool)


def classifier_specs() -> dict:
    """name → (estimator, param_grid, feature_prefixes or None for all features)."""
    tree = DecisionTreeClassifier(criterion="gini", random_state=RANDOM_STATE)
    return {
        "Majority class (baseline)": (DummyClassifier(strategy="most_frequent"), {}, None),
        "Seniority only (decision tree)": (tree, clf.PARAM_GRID, ("lvl_",)),
        "Decision tree (CART) — project model": (tree, clf.PARAM_GRID, None),
        "Logistic regression (L2)": (
            LogisticRegression(max_iter=5000, random_state=RANDOM_STATE), {"C": [0.01, 0.1, 1.0, 10.0]}, None),
        "Bernoulli naive Bayes": (BernoulliNB(), {"alpha": [0.1, 0.5, 1.0]}, None),
        "k-NN (Jaccard)": (
            make_pipeline(FunctionTransformer(_to_bool), KNeighborsClassifier(metric="jaccard")),
            {"kneighborsclassifier__n_neighbors": [5, 11, 21]}, None),
        "Random forest": (
            RandomForestClassifier(n_estimators=300, random_state=RANDOM_STATE),
            {"max_depth": [3, 6, None], "min_samples_leaf": [1, 5]}, None),
        "Gradient boosting (HistGB)": (
            HistGradientBoostingClassifier(early_stopping=False, random_state=RANDOM_STATE),
            {"learning_rate": [0.05, 0.1], "max_depth": [2, 3]}, None),
    }


def nested_cv_predict(estimator, param_grid: dict, X: pd.DataFrame, y: pd.Series) -> np.ndarray:
    """Out-of-fold predictions with the same outer/inner folds as classification.nested_cv."""
    outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    X_arr, y_arr = X.to_numpy(), y.to_numpy(dtype=object)
    oof = np.empty(len(y_arr), dtype=object)
    for tr, te in outer.split(X_arr, y_arr):
        if param_grid:
            model = GridSearchCV(estimator, param_grid, cv=inner, scoring="accuracy").fit(X_arr[tr], y_arr[tr])
        else:
            model = estimator.fit(X_arr[tr], y_arr[tr])
        oof[te] = model.predict(X_arr[te])
    return oof


def paired_bootstrap_diff(y_true, pred_a, pred_b, n=clf.N_BOOTSTRAP):
    """95% CI of accuracy(a) − accuracy(b) on the same bootstrap resamples as classification.bootstrap_ci."""
    idx = np.arange(len(y_true))
    diffs = [
        accuracy_score(y_true[s], pred_a[s]) - accuracy_score(y_true[s], pred_b[s])
        for s in (resample(idx, replace=True, random_state=RANDOM_STATE + i) for i in range(n))
    ]
    return np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)


def compare_classifiers(X: pd.DataFrame, y: pd.Series, specs: dict | None = None):
    """Run every classifier with nested CV. Returns (results table, out-of-fold predictions per model)."""
    specs = specs or classifier_specs()
    y_arr = y.to_numpy(dtype=object)
    preds, rows = {}, []
    for name, (estimator, grid, prefixes) in specs.items():
        cols = [c for c in X.columns if prefixes is None or c.startswith(prefixes)]
        start = time.perf_counter()
        preds[name] = nested_cv_predict(estimator, grid, X[cols], y)
        seconds = time.perf_counter() - start
        acc = accuracy_score(y_arr, preds[name])
        lo, hi = clf.bootstrap_ci(y_arr, preds[name])
        cm = confusion_matrix(y_arr, preds[name], labels=clf.CLASSES)
        rows.append({
            "model": name, "n_features": len(cols), "accuracy": acc, "ci_low": lo, "ci_high": hi,
            "macro_f1": f1_score(y_arr, preds[name], average="macro", zero_division=0),
            **{f"recall_{c}": cm[i, i] / cm[i].sum() for i, c in enumerate(clf.CLASSES)},
            "seconds": seconds,
        })
    table = pd.DataFrame(rows).set_index("model")
    ref = next(n for n in specs if "project model" in n)
    for name in table.index:
        lo, hi = paired_bootstrap_diff(y_arr, preds[name], preds[ref])
        table.loc[name, "diff_vs_tree_low"], table.loc[name, "diff_vs_tree_high"] = lo, hi
    return table, preds


# ---------------------------------------------------------------------------
# Q2 — clustering
# ---------------------------------------------------------------------------

def clustering_matrix(skills_df: pd.DataFrame) -> pd.DataFrame:
    """Same skill/job filtering as clustering.run_clustering (boolean jobs × skills)."""
    sm = skills_df.set_index("job_id") if "job_id" in skills_df.columns else skills_df
    sm = sm.sort_index(axis=1)
    frequent = sm.columns[sm.mean() > cl.FREQUENT_SKILL_RATIO]
    rare = sm.columns[sm.sum() < cl.RARE_SKILL_MIN]
    drop = [c for c in sorted(set(frequent) | set(rare) | set(cl.MANUAL_DROPS)) if c in sm.columns]
    filtered = sm.drop(columns=drop)
    keep = filtered.sum(axis=1) >= cl.MIN_SKILLS_PER_JOB
    return filtered[keep].astype(bool)


def _score_labels(labels: np.ndarray, D_square: np.ndarray, groups: np.ndarray) -> dict:
    """Metrics on non-noise jobs, consistent with clustering.evaluate_k, plus ARI vs job families."""
    keep = labels != cl.NOISE_LABEL
    n_real = len(set(labels[keep]))
    out = {
        "n_real_clusters": n_real,
        "noise_share": float((~keep).mean()),
        "silhouette": np.nan, "purity": np.nan, "baseline": np.nan, "f_measure": np.nan, "ari": np.nan,
        "valid": n_real >= cl.MIN_REAL_CLUSTERS and (~keep).sum() <= cl.MAX_NOISE_SHARE * len(labels),
    }
    if n_real >= 2:
        from sklearn.metrics import silhouette_score
        out["silhouette"] = silhouette_score(D_square[np.ix_(keep, keep)], labels[keep], metric="precomputed")
        crosstab = pd.crosstab(labels[keep], groups[keep])
        out["purity"], out["baseline"], out["f_measure"] = cl.calculate_purity_fmeasure(crosstab)
        out["ari"] = adjusted_rand_score(groups[keep], labels[keep])
    return out


def _best_over_k(label_fn, D_square, groups):
    """Apply the project's noise rule for every k and pick the valid k with the highest silhouette
    (falls back to the best silhouette overall, marked invalid, if no k is valid)."""
    results = []
    for k in cl.K_RANGE:
        labels = cl.assign_noise(label_fn(k))
        res = _score_labels(labels, D_square, groups)
        res.update(k=k, labels=labels)
        results.append(res)
    valid = [r for r in results if r["valid"]]
    pool = valid or [r for r in results if not np.isnan(r["silhouette"])]
    if not pool:
        # every k collapses into < 2 real clusters (e.g. chaining): report the k with the most real clusters
        return max(results, key=lambda r: (r["n_real_clusters"], -r["noise_share"], -r["k"]))
    return max(pool, key=lambda r: (r["silhouette"], -r["k"]))


def compare_clustering(skills_df: pd.DataFrame, groups_by_job: pd.Series):
    """Returns (results table, labels per method, filtered matrix, Jaccard distance matrix)."""
    M = clustering_matrix(skills_df)
    D = pdist(M.to_numpy(), metric="jaccard")
    D_square = squareform(D)
    groups = groups_by_job.reindex(M.index).to_numpy()

    methods = {}
    for method in ("weighted", "average", "complete"):
        Z = linkage(D, method=method)
        methods[f"HAC {method} linkage (Jaccard)"] = _best_over_k(
            lambda k, Z=Z: fcluster(Z, k, criterion="maxclust"), D_square, groups)
    methods["K-means (binary vectors)"] = _best_over_k(
        lambda k: KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit_predict(M.to_numpy(dtype=float)),
        D_square, groups)
    # copy=True: HDBSCAN would otherwise modify the shared distance matrix in place
    hdb = HDBSCAN(min_cluster_size=cl.MIN_CLUSTER_SIZE, metric="precomputed", copy=True).fit_predict(D_square)
    hdb = np.where(hdb < 0, cl.NOISE_LABEL, hdb + 1)
    res = _score_labels(hdb, D_square, groups)
    res.update(k=None, labels=hdb)
    methods["HDBSCAN (Jaccard, min cluster 15)"] = res

    table = pd.DataFrame({name: {k: v for k, v in r.items() if k != "labels"} for name, r in methods.items()}).T
    labels = {name: r["labels"] for name, r in methods.items()}
    return table, labels, M, D


# method key used by clustering_stability for each compared method with a chosen k
STABILITY_METHODS = {
    "HAC weighted linkage (Jaccard)": "weighted",
    "HAC average linkage (Jaccard)": "average",
    "K-means (binary vectors)": "kmeans",
}


def _fit_labels(X: np.ndarray, k: int, method: str) -> np.ndarray:
    """Cluster boolean rows with one method at k clusters, then apply the project's noise rule."""
    if method == "kmeans":
        raw = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit_predict(X.astype(float))
    else:
        raw = fcluster(linkage(pdist(X, metric="jaccard"), method=method), k, criterion="maxclust")
    return cl.assign_noise(raw)


def clustering_stability(M: pd.DataFrame, k: int, method: str = "weighted",
                         n: int = N_STABILITY, frac: float = STABILITY_FRAC) -> np.ndarray:
    """ARI between the full-data clustering and clusterings of random 80% subsamples (same k, same noise rule).

    The same subsamples (same seed) are used for every method, so the scores are directly comparable.
    """
    X = M.to_numpy()
    full = _fit_labels(X, k, method)
    rng = np.random.default_rng(RANDOM_STATE)
    scores = []
    for _ in range(n):
        idx = np.sort(rng.choice(len(M), size=int(frac * len(M)), replace=False))
        scores.append(adjusted_rand_score(full[idx], _fit_labels(X[idx], k, method)))
    return np.array(scores)


def _purity_ari(labels: np.ndarray, groups: np.ndarray) -> tuple[float, float]:
    keep = labels != cl.NOISE_LABEL
    purity, _, _ = cl.calculate_purity_fmeasure(pd.crosstab(labels[keep], groups[keep]))
    return purity, adjusted_rand_score(groups[keep], labels[keep])


def paired_bootstrap_clustering(labels_a: np.ndarray, labels_b: np.ndarray, groups: np.ndarray,
                                n: int = clf.N_BOOTSTRAP) -> pd.DataFrame:
    """Paired bootstrap of purity and ARI for two fixed clusterings of the same jobs.

    Each resample draws jobs with replacement (same seeds as classification.bootstrap_ci) and scores both
    clusterings on the same jobs (each on its own non-noise jobs). Returns value of a, value of b, a − b and
    the 95% CI of a − b for each metric.
    """
    idx_all = np.arange(len(groups))
    diffs = {"purity": [], "ari": []}
    for i in range(n):
        s = resample(idx_all, replace=True, random_state=RANDOM_STATE + i)
        pa, aa = _purity_ari(labels_a[s], groups[s])
        pb, ab = _purity_ari(labels_b[s], groups[s])
        diffs["purity"].append(pa - pb)
        diffs["ari"].append(aa - ab)
    full_a, full_b = _purity_ari(labels_a, groups), _purity_ari(labels_b, groups)
    rows = []
    for j, metric in enumerate(("purity", "ari")):
        rows.append({"metric": metric, "a": full_a[j], "b": full_b[j], "diff": full_a[j] - full_b[j],
                     "ci_low": np.percentile(diffs[metric], 2.5), "ci_high": np.percentile(diffs[metric], 97.5)})
    return pd.DataFrame(rows).set_index("metric")


SAME_SIZE_RANGE = range(3, 8)   # numbers of real clusters compared at equal size
SAME_SIZE_K_MAX = 20            # largest k searched to reach a given number of real clusters


def labels_with_n_real(X: np.ndarray, method: str, n_real: int, k_max: int = SAME_SIZE_K_MAX):
    """Smallest k (2..k_max) whose clustering has exactly n_real real clusters after the noise rule.

    Returns (k, labels) or (None, None) if no k reaches that number.
    """
    Z = None if method == "kmeans" else linkage(pdist(X, metric="jaccard"), method=method)
    for k in range(2, k_max + 1):
        if method == "kmeans":
            labels = _fit_labels(X, k, "kmeans")
        else:
            labels = cl.assign_noise(fcluster(Z, k, criterion="maxclust"))
        if len(set(labels[labels != cl.NOISE_LABEL])) == n_real:
            return k, labels
    return None, None


def same_size_comparison(M: pd.DataFrame, groups: np.ndarray, sizes=SAME_SIZE_RANGE,
                         n_boot: int = clf.N_BOOTSTRAP) -> pd.DataFrame:
    """Weighted HAC vs K-means at the same number of real clusters (removes purity's bias towards more clusters)."""
    X = M.to_numpy()
    rows = []
    for m in sizes:
        k_h, lab_h = labels_with_n_real(X, "weighted", m)
        k_k, lab_k = labels_with_n_real(X, "kmeans", m)
        if lab_h is None or lab_k is None:
            continue
        paired = paired_bootstrap_clustering(lab_h, lab_k, groups, n=n_boot)
        row = {"n_real_clusters": m, "hac_k": k_h, "kmeans_k": k_k,
               "hac_noise": float((lab_h == cl.NOISE_LABEL).mean()),
               "kmeans_noise": float((lab_k == cl.NOISE_LABEL).mean())}
        for metric, r in paired.iterrows():
            row.update({f"{metric}_hac": r["a"], f"{metric}_kmeans": r["b"], f"{metric}_diff": r["diff"],
                        f"{metric}_ci_low": r["ci_low"], f"{metric}_ci_high": r["ci_high"]})
        rows.append(row)
    return pd.DataFrame(rows).set_index("n_real_clusters")


# ---------------------------------------------------------------------------
# Q1 — Apriori vs FP-Growth
# ---------------------------------------------------------------------------

def _rule_set(itemsets: pd.DataFrame) -> set:
    rules = association_rules(itemsets, metric="lift", min_threshold=1.2)
    rules = rules[rules["confidence"] >= 0.5]
    return {(frozenset(a), frozenset(c)) for a, c in zip(rules["antecedents"], rules["consequents"])}


def compare_apriori_fpgrowth(train_df: pd.DataFrame, supports=APRIORI_SUPPORTS, repeats=TIMING_REPEATS):
    """Same itemsets/rules? and median runtime of each algorithm per min_support."""
    data = train_df.astype(bool)
    rows = []
    for ms in supports:
        times = {}
        out = {}
        for name, algo in (("apriori", mlx_apriori), ("fpgrowth", fpgrowth)):
            runs = []
            for _ in range(repeats):
                start = time.perf_counter()
                out[name] = algo(data, min_support=ms, use_colnames=True)
                runs.append(time.perf_counter() - start)
            times[name] = float(np.median(runs))
        a = dict(zip(out["apriori"]["itemsets"], out["apriori"]["support"]))
        f = dict(zip(out["fpgrowth"]["itemsets"], out["fpgrowth"]["support"]))
        same_itemsets = a.keys() == f.keys() and all(abs(a[k] - f[k]) < 1e-12 for k in a)
        rules_a, rules_f = _rule_set(out["apriori"]), _rule_set(out["fpgrowth"])
        rows.append({"min_support": ms, "itemsets": len(a), "rules": len(rules_a),
                     "same_itemsets": same_itemsets, "same_rules": rules_a == rules_f,
                     "apriori_ms": times["apriori"] * 1000, "fpgrowth_ms": times["fpgrowth"] * 1000})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figures + report
# ---------------------------------------------------------------------------

FIG_STYLE = {"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12, "xtick.labelsize": 12,
             "ytick.labelsize": 12, "legend.fontsize": 12, "axes.spines.top": False, "axes.spines.right": False}


def plot_classifiers(table: pd.DataFrame, path: Path):
    plt.rcParams.update(FIG_STYLE)
    t = table.sort_values("accuracy")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#dd6b20" if "project model" in n else "#a0aec0" if "baseline" in n else "#2b6cb0" for n in t.index]
    ax.barh(t.index, t["accuracy"], color=colors,
            xerr=[t["accuracy"] - t["ci_low"], t["ci_high"] - t["accuracy"]], capsize=4)
    for i, (n, r) in enumerate(t.iterrows()):
        ax.text(r["ci_high"] + 0.01, i, f"{r['accuracy']:.3f}", va="center", fontsize=11)
    ax.set_xlabel("Out-of-fold accuracy (bars: 95% bootstrap CI)")
    ax.set_xlim(0, 1)
    ax.set_title("Q3 salary band: classifiers under the same nested CV")
    fig.text(0.01, 0.01, f"{len(clf.CLASSES)} balanced classes (tertiles); orange = project model",
             fontsize=10, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_clustering(table: pd.DataFrame, path: Path):
    plt.rcParams.update(FIG_STYLE)
    metrics = [("silhouette", "Silhouette (Jaccard)"), ("purity", "Purity (dashed: baseline)"), ("ari", "ARI vs job families")]
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    names = list(table.index)
    for ax, (col, title) in zip(axes, metrics):
        vals = table[col].astype(float)
        colors = ["#dd6b20" if n.startswith("HAC weighted") else "#2b6cb0" for n in names]
        ax.barh(names, vals.fillna(0), color=colors)
        for i, v in enumerate(vals):
            na = f" n/a ({int(table.iloc[i]['n_real_clusters'])} cluster)"
            ax.text(0 if np.isnan(v) else v, i, na if np.isnan(v) else f" {v:.3f}", va="center", fontsize=11)
        ax.set_title(title)
        ax.set_xlim(0, float(table[col].astype(float).max()) * 1.35)
        if col == "purity":
            ax.axvline(float(table["baseline"].astype(float).median()), color="grey", linestyle="--", linewidth=1)
    axes[0].invert_yaxis()
    fig.suptitle("Q2 clustering methods on the same skill matrix (non-noise jobs; orange = project model)", fontsize=15)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_apriori(table: pd.DataFrame, path: Path):
    plt.rcParams.update(FIG_STYLE)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(table["min_support"], table["apriori_ms"], marker="o", color="#2b6cb0", label="Apriori")
    ax.plot(table["min_support"], table["fpgrowth_ms"], marker="o", color="#dd6b20", label="FP-Growth")
    ax.set_yscale("log")
    ax.set_xlabel("min_support")
    ax.set_ylabel("Median runtime (ms, log scale)")
    ax.set_title("Q1: Apriori vs FP-Growth on the train set (identical rules)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _md(df: pd.DataFrame, floatfmt: str = ".3f") -> list[str]:
    cols = list(df.columns)
    lines = ["| " + " | ".join([df.index.name or ""] + cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for idx, row in df.iterrows():
        cells = [f"{v:{floatfmt}}" if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join([str(idx)] + cells) + " |")
    return lines


def load_inputs():
    jobs_df, skills_df = load_and_verify_data()
    with open(PROJECT_ROOT / "src" / "models" / "expertise_groups.json", encoding="utf-8") as f:
        groups = cl.map_expertise_groups(jobs_df["category"], json.load(f))
    groups_by_job = pd.Series(groups.to_numpy(), index=jobs_df["job_id"])
    return jobs_df, skills_df, groups_by_job


def run_comparison():
    jobs_df, skills_df, groups_by_job = load_inputs()

    # Q3
    X, y, _ = clf.build_dataset(jobs_df, skills_df)
    clf_table, preds = compare_classifiers(X, y)
    oof_ref, _ = clf.nested_cv(X, y)
    assert (preds["Decision tree (CART) — project model"] == oof_ref).all(), "tree re-run differs from classification.py"

    # Q2
    clu_table, clu_labels, M, _ = compare_clustering(skills_df, groups_by_job)
    committed = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "cluster_labels.csv").set_index("job_id")
    project = "HAC weighted linkage (Jaccard)"
    assert (committed.loc[M.index, "cluster"].to_numpy() == clu_labels[project]).all(), \
        "weighted HAC re-run differs from cluster_labels.csv"
    k_cut = int(clu_table.loc[project, "k"])
    stabilities = {name: clustering_stability(M, int(clu_table.loc[name, "k"]), method)
                   for name, method in STABILITY_METHODS.items() if clu_table.loc[name, "valid"]}
    stability = stabilities[project]
    groups = groups_by_job.reindex(M.index).to_numpy()
    cluster_paired = paired_bootstrap_clustering(clu_labels[project], clu_labels["K-means (binary vectors)"], groups)
    same_size = same_size_comparison(M, groups)

    # Q1
    df = skills_df.merge(jobs_df[["job_id", "posted_date"]], on="job_id")
    df["posted_date"] = pd.to_datetime(df["posted_date"])
    train_part, _ = ap.chronological_split(df, train_frac=0.7)
    train_df = train_part[[c for c in df.columns if c not in ("job_id", "posted_date")]]
    rules_table = compare_apriori_fpgrowth(train_df)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plot_classifiers(clf_table, FIG_DIR / "model_compare_classifiers.png")
    plot_clustering(clu_table, FIG_DIR / "model_compare_clustering.png")
    plot_apriori(rules_table, FIG_DIR / "model_compare_apriori_fpgrowth.png")
    write_report(clf_table, clu_table, stability, k_cut, rules_table, n_jobs=len(X), n_clustered=len(M),
                 stabilities=stabilities, cluster_paired=cluster_paired, same_size=same_size)
    return clf_table, clu_table, stability, rules_table, stabilities, cluster_paired, same_size


def _stability_lines(stabilities, clu_table) -> list[str]:
    if not stabilities:
        return []
    lines = ["### Stability (same 50 subsamples of 80% for every method)", "",
             "| Method | k | mean ARI | 5th–95th percentile |", "|---|---|---|---|"]
    for name, sc in stabilities.items():
        lines.append(f"| {name} | {int(clu_table.loc[name, 'k'])} | {sc.mean():.3f} | "
                     f"{np.percentile(sc, 5):.3f}–{np.percentile(sc, 95):.3f} |")
    best = max(stabilities, key=lambda n: stabilities[n].mean())
    lines += ["", f"- Most stable: **{best}**. ARI 1 = identical clusters on every subsample, 0 = chance agreement.", ""]
    return lines


def _paired_cluster_lines(paired) -> list[str]:
    if paired is None:
        return []
    lines = ["### Paired bootstrap: HAC weighted (project) − K-means", "",
             f"Both clusterings fixed; jobs resampled with replacement {clf.N_BOOTSTRAP} times; each method scored on "
             "its own non-noise jobs within the same resample.", "",
             "| Metric | HAC weighted | K-means | Difference | 95% CI of difference |", "|---|---|---|---|---|"]
    for metric, r in paired.iterrows():
        lines.append(f"| {metric} | {r['a']:.3f} | {r['b']:.3f} | {r['diff']:+.3f} | "
                     f"{r['ci_low']:+.3f} – {r['ci_high']:+.3f} |")
    verdicts = []
    for metric, r in paired.iterrows():
        if r["ci_low"] > 0:
            verdicts.append(f"{metric}: HAC weighted significantly higher")
        elif r["ci_high"] < 0:
            verdicts.append(f"{metric}: K-means significantly higher")
        else:
            verdicts.append(f"{metric}: no significant difference (CI includes 0)")
    lines += ["", "- " + "; ".join(verdicts) + ".", ""]
    return lines


def _same_size_lines(same) -> list[str]:
    if same is None or same.empty:
        return []
    def verdict(lo, hi):
        return "HAC higher*" if lo > 0 else "K-means higher*" if hi < 0 else "n.s."
    lines = ["### Same number of real clusters: HAC weighted vs K-means", "",
             "For each number of real clusters, the smallest k reaching it for each method (same noise rule); paired "
             f"bootstrap ({clf.N_BOOTSTRAP} resamples) of the difference HAC − K-means. * = 95% CI excludes 0.", "",
             "| Real clusters | k (HAC / K-means) | Noise (HAC / K-means) | Purity HAC / K-means | Purity diff (95% CI) | "
             "ARI HAC / K-means | ARI diff (95% CI) |", "|---|---|---|---|---|---|---|"]
    for m, r in same.iterrows():
        lines.append(
            f"| {m} | {int(r['hac_k'])} / {int(r['kmeans_k'])} | {r['hac_noise']:.1%} / {r['kmeans_noise']:.1%} | "
            f"{r['purity_hac']:.3f} / {r['purity_kmeans']:.3f} | {r['purity_diff']:+.3f} ({r['purity_ci_low']:+.3f} – "
            f"{r['purity_ci_high']:+.3f}) {verdict(r['purity_ci_low'], r['purity_ci_high'])} | "
            f"{r['ari_hac']:.3f} / {r['ari_kmeans']:.3f} | {r['ari_diff']:+.3f} ({r['ari_ci_low']:+.3f} – "
            f"{r['ari_ci_high']:+.3f}) {verdict(r['ari_ci_low'], r['ari_ci_high'])} |")
    n = len(same)
    km_p = int((same["purity_ci_high"] < 0).sum()); km_a = int((same["ari_ci_high"] < 0).sum())
    hac_p = int((same["purity_ci_low"] > 0).sum()); hac_a = int((same["ari_ci_low"] > 0).sum())
    lines += ["", f"- K-means significantly better: purity at {km_p}/{n} sizes, ARI at {km_a}/{n} sizes; "
                  f"HAC significantly better: purity at {hac_p}/{n}, ARI at {hac_a}/{n}.", ""]
    return lines


def write_report(clf_table, clu_table, stability, k_cut, rules_table, n_jobs, n_clustered,
                 stabilities=None, cluster_paired=None, same_size=None):
    ref = "Decision tree (CART) — project model"
    best = clf_table["accuracy"].idxmax()
    seniority = next(n for n in clf_table.index if n.startswith("Seniority only"))
    t = clf_table[["n_features", "accuracy", "ci_low", "ci_high", "macro_f1", "recall_Low", "recall_Mid",
                   "recall_High", "diff_vs_tree_low", "diff_vs_tree_high", "seconds"]].copy()
    t.index.name = "Model"
    t["n_features"] = [("—" if "baseline" in n else str(int(v))) for n, v in t["n_features"].items()]
    better = [n for n in clf_table.index if clf_table.loc[n, "diff_vs_tree_low"] > 0]
    worse = [n for n in clf_table.index if clf_table.loc[n, "diff_vs_tree_high"] < 0]

    c = clu_table[["k", "n_real_clusters", "noise_share", "silhouette", "purity", "baseline", "f_measure", "ari", "valid"]].copy()
    c.index.name = "Method"
    c["k"] = c["k"].map(lambda v: "—" if v is None or pd.isna(v) else str(int(v)))
    c["n_real_clusters"] = c["n_real_clusters"].astype(int).astype(str)
    c["valid"] = c["valid"].map(lambda v: "yes" if v else "no")
    for col in ["noise_share", "silhouette", "purity", "baseline", "f_measure", "ari"]:
        c[col] = c[col].astype(float)

    r = rules_table.copy().set_index("min_support")
    r.index = r.index.map(lambda v: f"{v:.2f}")
    r.index.name = "min_support"
    r["fpgrowth / apriori time"] = r["fpgrowth_ms"] / r["apriori_ms"]

    lines = [
        "# Model comparison",
        "",
        "Generated by `src/models/comparison.py` (lecturer requirement, `docs/DECISIONS.md` 04/10). "
        "Every method uses the same data, folds and metrics as the project model; the project models are re-run "
        "here and checked against `classification.py` / `cluster_labels.csv`.",
        "",
        "## Q3 — salary band classifiers",
        "",
        f"{n_jobs} jobs with a disclosed salary, 3 tertile classes, nested CV (outer 5 / inner 3 folds, same seeds as "
        "`classification.py`), out-of-fold predictions, 95% bootstrap CI. `diff_vs_tree` = paired bootstrap 95% CI of "
        "accuracy(model) − accuracy(decision tree).",
        "",
        *_md(t),
        "",
        f"- Highest accuracy: **{best}** ({clf_table.loc[best, 'accuracy']:.3f}); project decision tree: "
        f"{clf_table.loc[ref, 'accuracy']:.3f}.",
        f"- Significantly better than the decision tree (diff CI > 0): {', '.join(better) or 'none'}.",
        f"- Significantly worse than the decision tree (diff CI < 0): {', '.join(worse) or 'none'}.",
        f"- Seniority-only tree ({int(clf_table.loc[seniority, 'n_features'])} features): "
        f"{clf_table.loc[seniority, 'accuracy']:.3f} vs full tree ({int(clf_table.loc[ref, 'n_features'])} features): "
        f"{clf_table.loc[ref, 'accuracy']:.3f} — the skill features add little for a single tree.",
        "",
        "## Q2 — clustering methods",
        "",
        f"{n_clustered} jobs, same filtered skill matrix and noise rule as `clustering.py` (clusters < "
        f"{cl.MIN_CLUSTER_SIZE} jobs = noise; k valid with ≥ {cl.MIN_REAL_CLUSTERS} real clusters and noise ≤ "
        f"{cl.MAX_NOISE_SHARE:.0%}; k = {cl.K_RANGE.start}–{cl.K_RANGE.stop - 1}). Metrics on non-noise jobs; "
        "silhouette uses Jaccard distance for every method; ARI is against the 10 job families (A16). "
        "HDBSCAN chooses its own number of clusters.",
        "",
        *_md(c),
        "",
        f"**Stability of the project model** (weighted HAC, k = {k_cut}): ARI between the full-data clustering and "
        f"{len(stability)} random {STABILITY_FRAC:.0%} subsamples — mean {stability.mean():.3f}, "
        f"5th–95th percentile {np.percentile(stability, 5):.3f}–{np.percentile(stability, 95):.3f}.",
        "",
        *[f"- Best {label}: **{clu_table[col].astype(float).idxmax()}** "
          f"({clu_table[col].astype(float).max():.3f})." for col, label in
          (("silhouette", "silhouette"), ("purity", "purity"), ("ari", "ARI vs job families"))],
        f"- Methods with no valid k (or not meeting the noise rule): "
        f"{', '.join(n for n in clu_table.index if not clu_table.loc[n, 'valid']) or 'none'}.",
        "",
        *_stability_lines(stabilities, clu_table),
        *_paired_cluster_lines(cluster_paired),
        *_same_size_lines(same_size),
        "## Q1 — Apriori vs FP-Growth",
        "",
        f"Train set, lift > 1.2 and confidence ≥ 0.5 (same as `apriori.py`); median of {TIMING_REPEATS} runs. "
        "Runtimes depend on the machine.",
        "",
        *_md(r, ".1f"),
        "",
        f"- Identical itemsets and rules at every min_support: **{bool(r['same_itemsets'].all() and r['same_rules'].all())}**.",
        f"- FP-Growth is {'slower' if (r['fpgrowth / apriori time'] > 1).all() else 'not always slower'} than Apriori here "
        f"({r['fpgrowth / apriori time'].min():.1f}–{r['fpgrowth / apriori time'].max():.1f}× the time): with only "
        f"{len(rules_table) and int(rules_table['itemsets'].max())} frequent itemsets at most, its tree-building overhead "
        "dominates; FP-Growth's advantage appears on larger, denser data.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import matplotlib

    matplotlib.use("Agg")
    clf_t, clu_t, stab, rules_t, stabs, paired, same = run_comparison()
    print(clf_t[["accuracy", "ci_low", "ci_high", "macro_f1"]].round(3).to_string())
    print(clu_t[["k", "n_real_clusters", "noise_share", "silhouette", "purity", "ari", "valid"]].to_string())
    print({n: round(float(v.mean()), 3) for n, v in stabs.items()})
    print(paired.round(3).to_string())
    print(same.round(3).to_string())
    print(rules_t.to_string())
    print(f"Report: {REPORT_PATH}")
