"""Task 3 — Decision Tree phân lớp dải lương (Low / Mid / High theo tertile).

Feature: kỹ năng + cấp bậc + địa điểm (Q3 kickoff). Đánh giá bằng nested CV,
accuracy/F1 tính trên dự đoán out-of-fold, bootstrap CI, so với baseline.
"""
import json
import pickle
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.utils import resample

from src.models.features import (
    LEVEL_GROUPS,
    calculate_salary_mid,
    clean_level_feature,
    extract_location_flags,
    load_and_verify_data,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = PROJECT_ROOT / "reports"
FIG_DIR = REPORT_DIR / "figures"
MODEL_DIR = PROJECT_ROOT / "models"

CLASSES = ["Low", "Mid", "High"]
LEVEL_COLUMNS = [f"lvl_{g}" for g in sorted(set(LEVEL_GROUPS.values()) | {"Unknown"})]
MIN_SKILL_COUNT = 5            # bỏ kỹ năng xuất hiện < 5 lần trong tập tin có lương
PARAM_GRID = {"max_depth": [3, 4, 5, 6], "min_samples_leaf": [5, 10, 15]}
RANDOM_STATE = 42
N_BOOTSTRAP = 1000

# Giá trị đã chốt ở DECISIONS 01/10 (dữ liệu freeze) — lệch thì dừng, không chạy tiếp
EXPECTED_N = 172
EXPECTED_CLASS_COUNTS = {"Low": 60, "Mid": 55, "High": 57}


def build_dataset(jobs_df: pd.DataFrame, skills_df: pd.DataFrame, min_skill_count: int = MIN_SKILL_COUNT):
    """Tạo X, y cho các tin có lương.

    - Nhãn tertile tính trên toàn bộ tin có lương (trước khi join).
    - Left join với skill_matrix, điền 0 cho tin không bắt được kỹ năng nào.
    - Feature: kỹ năng (≥ min_skill_count lần), level one-hot (đủ LEVEL_COLUMNS), location multi-hot.

    Returns:
        X (DataFrame, cột sắp theo tên), y (Series nhãn), bins (ranh giới qcut).
    """
    jobs = jobs_df[jobs_df["salary_status"] != "undisclosed"].copy()
    salary_mid = calculate_salary_mid(jobs)
    jobs["salary_tertile"], bins = pd.qcut(salary_mid, q=3, labels=CLASSES, retbins=True)
    jobs = jobs.set_index("job_id")

    skills = skills_df.set_index("job_id") if "job_id" in skills_df.columns else skills_df
    merged = jobs.join(skills, how="left")
    skill_columns = list(skills.columns)
    merged[skill_columns] = merged[skill_columns].fillna(0).astype(int)

    counts = merged[skill_columns].sum()
    kept_skills = sorted(counts[counts >= min_skill_count].index)

    levels = pd.get_dummies(clean_level_feature(merged), prefix="lvl").astype(int)
    levels = levels.reindex(columns=LEVEL_COLUMNS, fill_value=0)
    locations = extract_location_flags(merged).astype(int)

    X = pd.concat([merged[kept_skills], levels, locations], axis=1).sort_index(axis=1)
    y = merged["salary_tertile"].astype(str)
    return X, y, bins


def choose_final_params(best_params_list):
    """Bộ tham số được vòng trong chọn nhiều nhất; hoà thì chọn cây đơn giản hơn
    (max_depth nhỏ hơn, rồi min_samples_leaf lớn hơn)."""
    counts = Counter(best_params_list)
    return min(counts, key=lambda p: (-counts[p], p[0], -p[1]))


def nested_cv(X: pd.DataFrame, y: pd.Series):
    """Vòng ngoài 5 fold đánh giá, vòng trong 3 fold chọn tham số. Trả về dự đoán out-of-fold."""
    outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    X_arr, y_arr = X.to_numpy(), y.to_numpy(dtype=object)  # pandas 3: chuỗi là Arrow, phải ép về numpy
    oof = np.empty(len(y_arr), dtype=object)
    folds = []

    for fold, (tr, te) in enumerate(outer.split(X_arr, y_arr), start=1):
        grid = GridSearchCV(
            DecisionTreeClassifier(criterion="gini", random_state=RANDOM_STATE),
            PARAM_GRID, cv=inner, scoring="accuracy",
        )
        grid.fit(X_arr[tr], y_arr[tr])
        oof[te] = grid.best_estimator_.predict(X_arr[te])
        folds.append({
            "fold": fold,
            "max_depth": grid.best_params_["max_depth"],
            "min_samples_leaf": grid.best_params_["min_samples_leaf"],
            "inner_cv_accuracy": round(grid.best_score_, 4),
            "fold_accuracy": round(accuracy_score(y_arr[te], oof[te]), 4),
        })
    return oof, pd.DataFrame(folds)


def bootstrap_ci(y_true, y_pred, n=N_BOOTSTRAP):
    idx = np.arange(len(y_true))
    scores = [
        accuracy_score(y_true[s], y_pred[s])
        for s in (resample(idx, replace=True, random_state=RANDOM_STATE + i) for i in range(n))
    ]
    return np.percentile(scores, 2.5), np.percentile(scores, 97.5)


def _md_table(df: pd.DataFrame, index_name: str) -> list[str]:
    cols = [index_name] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for idx, row in df.astype(object).iterrows():  # giữ int, iterrows mặc định ép về float
        lines.append("| " + " | ".join([str(idx)] + [str(v) for v in row.values]) + " |")
    return lines


def plot_tree_ordered(model: DecisionTreeClassifier, X: pd.DataFrame, y: pd.Series, path: Path, title: str):
    """Vẽ cây với `value` theo thứ tự Low, Mid, High (sklearn mặc định sắp lớp theo chữ cái: High, Low, Mid).

    Fit lại một cây cùng tham số trên nhãn đánh số "1_Low" < "2_Mid" < "3_High". Gini và cách chọn nhánh
    không phụ thuộc tên lớp nên cấu trúc cây giống hệt — có assert để chắc chắn.
    """
    order = {c: f"{i}_{c}" for i, c in enumerate(CLASSES, start=1)}
    twin = DecisionTreeClassifier(**model.get_params()).fit(X, y.map(order))
    assert (twin.tree_.feature == model.tree_.feature).all() and np.allclose(twin.tree_.threshold, model.tree_.threshold)

    fig = plt.figure(figsize=(15, 10))
    plot_tree(twin, feature_names=list(X.columns), class_names=CLASSES, filled=True, rounded=True, fontsize=10)
    plt.title(title)
    fig.text(0.5, 0.01,
             "value = number of jobs [Low, Mid, High]. Left branch = condition true "
             "(feature <= 0.5, i.e. the job does NOT have it); right branch = job has it.",
             ha="center", fontsize=11)
    plt.tight_layout(rect=(0, 0.04, 1, 1))
    plt.savefig(path)
    plt.close(fig)


def intern_junior_breakdown(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """Thành phần nhóm Intern/Junior trong các tin có lương: số tin và lương đại diện theo level gốc."""
    jobs = jobs_df[jobs_df["salary_status"] != "undisclosed"].copy()
    jobs["salary_mid"] = calculate_salary_mid(jobs)
    members = [lvl for lvl, grp in LEVEL_GROUPS.items() if grp == "Intern/Junior"]
    sub = jobs[jobs["level"].isin(members)]
    out = sub.groupby("level")["salary_mid"].agg(["count", "median", "min", "max"]).reindex(members).dropna(how="all")
    out.columns = ["Số tin", "Trung vị (triệu)", "Thấp nhất", "Cao nhất"]
    out["Số tin"] = out["Số tin"].astype(int)
    return out.round(1)


def run_classification():
    jobs_df, skills_df = load_and_verify_data()
    X, y, bins = build_dataset(jobs_df, skills_df)

    class_counts = y.value_counts().reindex(CLASSES).to_dict()
    if len(X) != EXPECTED_N or class_counts != EXPECTED_CLASS_COUNTS:
        raise ValueError(
            f"Dữ liệu lệch DECISIONS 01/10: {len(X)} tin, lớp {class_counts} "
            f"(kỳ vọng {EXPECTED_N}, {EXPECTED_CLASS_COUNTS})."
        )
    n_skills = X.shape[1] - len(LEVEL_COLUMNS) - 4
    print(f"X {X.shape} ({n_skills} kỹ năng + {len(LEVEL_COLUMNS)} level + 4 địa điểm); lớp {class_counts}")

    oof, folds = nested_cv(X, y)
    y_arr = y.to_numpy(dtype=object)
    acc = accuracy_score(y_arr, oof)
    macro_f1 = f1_score(y_arr, oof, average="macro")
    baseline = max(class_counts.values()) / len(y)
    ci_low, ci_high = bootstrap_ci(y_arr, oof)
    cm = confusion_matrix(y_arr, oof, labels=CLASSES)
    print(f"OOF accuracy {acc:.4f} (95% CI {ci_low:.4f}–{ci_high:.4f}), macro-F1 {macro_f1:.4f}, baseline {baseline:.4f}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    folds.to_csv(REPORT_DIR / "tree_cv_results.csv", index=False)

    ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASSES).plot(cmap=plt.cm.Blues)
    plt.title("Out-of-Fold Confusion Matrix")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "confusion_matrix.png")
    plt.close()

    # Mô hình cuối: fit trên đủ 172 tin với bộ tham số được chọn
    params = choose_final_params(list(zip(folds["max_depth"], folds["min_samples_leaf"])))
    model = DecisionTreeClassifier(
        criterion="gini", max_depth=int(params[0]), min_samples_leaf=int(params[1]), random_state=RANDOM_STATE
    )
    model.fit(X, y)
    importance = pd.Series(model.feature_importances_, index=X.columns)
    importance = importance[importance > 0].sort_values(ascending=False)

    plot_tree_ordered(model, X, y, FIG_DIR / "tree_viz.png", title=f"Decision Tree (max_depth={params[0]}, min_samples_leaf={params[1]})")

    # Lưu model + metadata (pickle chỉ dùng được với đúng version sklearn)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "tree_model.pkl", "wb") as f:
        pickle.dump(model, f)
    meta = {
        "sklearn_version": sklearn.__version__,
        "params": {"max_depth": int(params[0]), "min_samples_leaf": int(params[1]), "criterion": "gini"},
        "classes": list(model.classes_),
        "tertile_bounds_million_vnd": [round(float(bins[1]), 2), round(float(bins[2]), 2)],
        "features": list(X.columns),
        "n_samples": int(len(X)),
    }
    (MODEL_DIR / "tree_model_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Báo cáo
    lo, hi = bins[1], bins[2]
    cm_df = pd.DataFrame(cm, index=[f"Thật: {c}" for c in CLASSES], columns=[f"Dự đoán: {c}" for c in CLASSES])
    imp_df = importance.round(3).to_frame("Importance")
    breakdown = intern_junior_breakdown(jobs_df)
    n_ij = int(breakdown["Số tin"].sum())
    n_intern = int(breakdown["Số tin"].get("Intern", 0))
    fold_counts = Counter(zip(folds["max_depth"], folds["min_samples_leaf"]))
    lines = [
        "# Báo cáo phân lớp lương (Decision Tree)",
        "",
        "Sinh bởi `src/models/classification.py`. Chỉ dùng tin **có công bố lương** — xem `bias_analysis.md` về phạm vi áp dụng.",
        "",
        "## Dữ liệu",
        "",
        f"- **Số tin:** {len(X)} (left join `skill_matrix`, tin không bắt được kỹ năng nào điền 0)",
        f"- **Nhãn (tertile `salary_mid`, triệu VND/tháng):** Low < {lo:.1f} ≤ Mid < {hi:.1f} ≤ High",
        f"- **Số tin mỗi lớp:** Low {class_counts['Low']} / Mid {class_counts['Mid']} / High {class_counts['High']}",
        f"- **Feature:** {X.shape[1]} = {n_skills} kỹ năng (xuất hiện ≥ {MIN_SKILL_COUNT} lần) + {len(LEVEL_COLUMNS)} cấp bậc (one-hot, có `Unknown`) + 4 địa điểm (multi-hot)",
        "",
        "## Đánh giá (nested CV, dự đoán out-of-fold)",
        "",
        "Vòng ngoài 5 fold đánh giá, vòng trong 3 fold chọn `max_depth ∈ {3,4,5,6}`, `min_samples_leaf ∈ {5,10,15}`.",
        "",
        f"- **Accuracy:** {acc:.4f} (95% bootstrap CI: {ci_low:.4f} – {ci_high:.4f}, {N_BOOTSTRAP} lần)",
        f"- **Baseline** (luôn đoán lớp đông nhất): {baseline:.4f}",
        f"- **Macro-F1:** {macro_f1:.4f}",
        "",
        "### Confusion matrix (out-of-fold)",
        "",
        *_md_table(cm_df, ""),
        "",
        "### Tham số chọn ở từng fold",
        "",
        *_md_table(folds.set_index("fold"), "Fold"),
        "",
        "## Mô hình cuối",
        "",
        f"- **Tham số:** max_depth={params[0]}, min_samples_leaf={params[1]} — bộ được vòng trong chọn nhiều nhất "
        f"({fold_counts[params]}/5 fold); hoà thì chọn cây đơn giản hơn (nông hơn).",
        f"- **Cây:** độ sâu {model.get_depth()}, {model.get_n_leaves()} lá. Hình: `reports/figures/tree_viz.png`.",
        f"- **Model:** `models/tree_model.pkl` (sklearn {sklearn.__version__}; metadata ở `models/tree_model_meta.json`).",
        "",
        "### Feature importance (> 0)",
        "",
        *_md_table(imp_df, "Feature"),
        "",
        "### Nhóm cấp bậc `Intern/Junior`",
        "",
        "Intern, Fresher và Junior được gộp thành 1 nhóm (`LEVEL_GROUPS`) vì Junior thật rất ít. "
        "Trong các tin có lương, thành phần nhóm này:",
        "",
        *_md_table(breakdown, "Level gốc"),
        "",
        f"→ **{n_intern}/{n_ij} tin là thực tập sinh**; con số \"lương\" của họ là **phụ cấp thực tập**, không phải lương. "
        "Vì vậy nhánh `lvl_Intern/Junior` của cây (toàn bộ dự đoán Low) phản ánh \"thực tập sinh có thu nhập thấp\" — "
        "**không** được diễn giải thành \"Junior lương thấp\".",
        "",
        "## Nhận xét",
        "",
        f"- Accuracy out-of-fold {acc:.1%}, cận dưới CI {ci_low:.1%} vẫn cao hơn baseline {baseline:.1%} → mô hình học được tín hiệu thật.",
        "- Cấp bậc (suy từ tiêu đề) là feature quan trọng nhất. Tách quan trọng nhất là `lvl_Intern/Junior`, "
        "nhưng nhóm này chủ yếu là thực tập sinh (phụ cấp) nên kết luận gần như hiển nhiên; tín hiệu có giá trị hơn là "
        "Senior/Lead/Manager nghiêng về High và việc **không suy được** cấp bậc (`lvl_Unknown`) nghiêng về Low.",
        "- **Hạn chế:** phụ cấp thực tập nằm chung với lương trong dữ liệu (không tách được ở bước làm sạch); "
        "phương án loại tin thực tập khỏi mô hình lương sẽ đổi N = 172 và tertile đã chốt ở Mốc 2 nên không áp dụng.",
        "- Recall từng lớp: " + ", ".join(f"{c} {cm[i, i]}/{cm[i].sum()} ({cm[i, i] / cm[i].sum():.0%})" for i, c in enumerate(CLASSES))
        + " — lớp giữa khó tách nhất, thường bị nhầm sang hai lớp bên cạnh.",
        f"- Mẫu nhỏ ({len(X)} tin) nên CI rộng; kết luận chỉ áp dụng cho tin có công bố lương (25% tổng số tin, phần lớn ghi USD).",
    ]
    (REPORT_DIR / "classification_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report → {REPORT_DIR / 'classification_report.md'}")


if __name__ == "__main__":
    run_classification()
