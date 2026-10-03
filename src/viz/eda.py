"""Biểu đồ EDA dùng chung cho notebooks và bước `figures` của pipeline.

Mọi hình đọc dữ liệu đã freeze (kiểm SHA-256 với docs/MANIFEST.json), chỉ vẽ số liệu
tổng hợp — không hiển thị nguyên văn JD (cam kết ToS, docs/DECISIONS.md 29/09).

Dùng:
    from src.viz.eda import load_data, FIGURES, save_figure
    jobs, skills = load_data()
    fig = FIGURES["top_skills"](jobs, skills)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.models.clustering import map_expertise_groups
from src.parse.salary import DEFAULT_USD_TO_VND
from src.models.features import (
    LOCATION_COLUMNS,
    calculate_salary_mid,
    clean_level_feature,
    extract_location_flags,
    load_and_verify_data,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIG_DIR = PROJECT_ROOT / "reports" / "figures"
EXPERTISE_MAP_PATH = PROJECT_ROOT / "src" / "models" / "expertise_groups.json"

SOURCE_NOTE = "Nguồn: ITviec, crawl 29/09/2026"
LEVEL_ORDER = ["Intern/Junior", "Middle", "Senior", "Lead", "Manager", "Unknown"]
CITY_LABELS = {"loc_hcm": "TP.HCM", "loc_hn": "Hà Nội", "loc_dn": "Đà Nẵng", "loc_other": "Khác"}
SALARY_CLASSES = ["Low", "Mid", "High"]
TRAIN_FRAC = 0.7  # khớp src/models/apriori.py::chronological_split

STYLE = {
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "figure.dpi": 100,
    "axes.spines.top": False,
    "axes.spines.right": False,
}
COLOR = "#2b6cb0"
COLOR_2 = "#dd6b20"


# ---------------------------------------------------------------------------
# Dữ liệu
# ---------------------------------------------------------------------------

def load_data(data_dir: Path | None = None):
    """Đọc jobs_clean + skill_matrix (đã kiểm hash) và thêm các cột dẫn xuất cho EDA.

    Returns:
        jobs: 688 tin, thêm salary_mid, has_salary, level_group, expertise_group,
              loc_* (multi-hot), posted_date (datetime).
        skills: ma trận nhị phân 688 × kỹ năng, index = job_id; tin không bắt được
              kỹ năng nào (bị loại khỏi skill_matrix) điền 0.
    """
    kwargs = {"data_dir": data_dir} if data_dir else {}
    jobs, skills = load_and_verify_data(**kwargs)
    jobs = jobs.copy()
    jobs["salary_mid"] = calculate_salary_mid(jobs)
    jobs["has_salary"] = jobs["salary_status"] != "undisclosed"
    jobs["level_group"] = clean_level_feature(jobs)
    with open(EXPERTISE_MAP_PATH, encoding="utf-8") as f:
        jobs["expertise_group"] = map_expertise_groups(jobs["category"], json.load(f))
    jobs = jobs.join(extract_location_flags(jobs))
    jobs["posted_date"] = pd.to_datetime(jobs["posted_date"])
    jobs = jobs.set_index("job_id")

    skills = skills.set_index("job_id").reindex(jobs.index, fill_value=0).astype(int)
    return jobs, skills


def salary_tertiles(jobs: pd.DataFrame):
    """Nhãn tertile Low/Mid/High cho tin có lương (DECISIONS Mốc 2) và 2 ranh giới (triệu VND)."""
    paid = jobs.loc[jobs["has_salary"], "salary_mid"]
    labels, bins = pd.qcut(paid, q=3, labels=SALARY_CLASSES, retbins=True)
    return labels.astype(str), (bins[1], bins[2])


def skill_share(skills: pd.DataFrame) -> pd.Series:
    """Tỷ lệ tin (trên toàn bộ 688 tin) có từng kỹ năng, giảm dần; hoà thì theo tên."""
    share = skills.mean()
    order = sorted(share.index, key=lambda s: (-share[s], s))
    return share[order]


# ---------------------------------------------------------------------------
# Tiện ích vẽ
# ---------------------------------------------------------------------------

def _new_fig(figsize=(10, 6)):
    plt.rcParams.update(STYLE)
    return plt.subplots(figsize=figsize)


def _finish(fig, note: str = SOURCE_NOTE):
    fig.text(0.01, 0.01, note, fontsize=10, color="#555555", ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return fig


def _label_bars(ax, bars, fmt="{:,.0f}", horizontal=False):
    for bar in bars:
        value = bar.get_width() if horizontal else bar.get_height()
        if horizontal:
            ax.text(value, bar.get_y() + bar.get_height() / 2, " " + fmt.format(value),
                    va="center", ha="left", fontsize=11)
        else:
            ax.text(bar.get_x() + bar.get_width() / 2, value, fmt.format(value),
                    va="bottom", ha="center", fontsize=11)


def save_figure(fig, name: str, fig_dir: Path = FIG_DIR) -> Path:
    fig_dir.mkdir(parents=True, exist_ok=True)
    path = fig_dir / f"eda_{name}.png"
    fig.savefig(path, dpi=150)
    return path


# ---------------------------------------------------------------------------
# Biểu đồ
# ---------------------------------------------------------------------------

def plot_pipeline_funnel(jobs, skills):
    """Số tin còn lại qua từng bước pipeline."""
    clustered = PROJECT_ROOT / "data" / "processed" / "cluster_labels.csv"
    steps = [
        ("HTML crawl", len(jobs)),
        ("Parse + làm sạch", len(jobs)),
        ("Có ≥1 kỹ năng", int((skills.sum(axis=1) > 0).sum())),
        ("Dùng để phân cụm", len(pd.read_csv(clustered)) if clustered.exists() else 0),
        ("Có công bố lương", int(jobs["has_salary"].sum())),
    ]
    fig, ax = _new_fig()
    names, values = zip(*steps)
    bars = ax.barh(names[::-1], values[::-1], color=COLOR)
    _label_bars(ax, bars, horizontal=True)
    ax.set_xlabel("Số tin tuyển dụng")
    ax.set_title("Phễu dữ liệu qua các bước pipeline")
    ax.set_xlim(0, max(values) * 1.12)
    return _finish(fig)


def plot_salary_disclosure(jobs, skills):
    order = ["full_range", "one_sided", "undisclosed"]
    names = {"full_range": "Có đủ khoảng lương", "one_sided": "Chỉ 1 cận", "undisclosed": "Không công bố"}
    counts = jobs["salary_status"].value_counts().reindex(order, fill_value=0)
    fig, ax = _new_fig((9, 6))
    bars = ax.bar([names[s] for s in order], counts.values, color=[COLOR, COLOR, "#a0aec0"])
    for bar, n in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, n, f"{n} ({n / len(jobs):.0%})",
                ha="center", va="bottom", fontsize=12)
    ax.set_ylabel("Số tin")
    ax.set_title("Tình trạng công bố lương (lương lấy từ JSON-LD baseSalary)")
    return _finish(fig)


def plot_salary_distribution(jobs, skills):
    paid = jobs.loc[jobs["has_salary"], "salary_mid"]
    _, (low, high) = salary_tertiles(jobs)
    fig, ax = _new_fig()
    ax.hist(paid, bins=np.arange(0, paid.max() + 10, 5), color=COLOR, edgecolor="white")
    top = ax.get_ylim()[1]
    # nhãn ranh giới dưới đặt bên trái đường, ranh giới trên đặt bên phải → không chồng nhau
    for cut, label, ha in [(low, "Low | Mid", "right"), (high, "Mid | High", "left")]:
        ax.axvline(cut, color=COLOR_2, linestyle="--", linewidth=2)
        pad = " " if ha == "left" else ""
        ax.text(cut, top * 0.97, f"{pad}{label} {pad}\n{pad}{cut:.1f} tr {pad}", color=COLOR_2,
                va="top", ha=ha, fontsize=11)
    ax.set_xlabel("Lương đại diện (triệu VND/tháng)")
    ax.set_ylabel("Số tin")
    ax.set_title(f"Phân phối lương — {len(paid)} tin có công bố (đường đứt: ranh giới tertile)")
    return _finish(fig, SOURCE_NOTE + f"; tỷ giá {DEFAULT_USD_TO_VND:,} VND/USD; one_sided dùng cận duy nhất".replace(",", "."))


def plot_currency(jobs, skills):
    counts = jobs.loc[jobs["has_salary"], "currency_original"].value_counts()
    fig, ax = _new_fig((8, 5))
    bars = ax.bar(counts.index, counts.values, color=COLOR)
    for bar, n in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, n, f"{n} ({n / counts.sum():.0%})",
                ha="center", va="bottom", fontsize=12)
    ax.set_xlabel("Đơn vị tiền gốc")
    ax.set_ylabel("Số tin có lương")
    ax.set_title("Đơn vị tiền của lương được công bố")
    return _finish(fig)


def plot_top_skills(jobs, skills, n=20):
    share = skill_share(skills).head(n)
    fig, ax = _new_fig((10, 8))
    bars = ax.barh(share.index[::-1], share.values[::-1] * 100, color=COLOR)
    _label_bars(ax, bars, fmt="{:.0f}%", horizontal=True)
    ax.set_xlabel("% số tin yêu cầu kỹ năng")
    ax.set_title(f"Top {n} kỹ năng được yêu cầu nhiều nhất")
    ax.set_xlim(0, share.max() * 115)
    return _finish(fig, SOURCE_NOTE + f"; {len(jobs)} tin; trích bằng từ điển kỹ năng (độ phủ: ASSUMPTIONS A7)")


def plot_locations(jobs, skills):
    counts = pd.Series({CITY_LABELS[c]: int(jobs[c].sum()) for c in LOCATION_COLUMNS.values()})
    missing = int((jobs[list(LOCATION_COLUMNS.values())].sum(axis=1) == 0).sum())
    fig, ax = _new_fig((9, 6))
    bars = ax.bar(counts.index, counts.values, color=COLOR)
    _label_bars(ax, bars)
    ax.set_ylabel("Số tin")
    ax.set_title("Địa điểm làm việc")
    return _finish(fig, SOURCE_NOTE + f"; 1 tin có thể ở nhiều nơi; {missing} tin không ghi địa điểm")


def plot_levels(jobs, skills):
    counts = jobs["level_group"].value_counts().reindex(LEVEL_ORDER, fill_value=0)
    fig, ax = _new_fig()
    bars = ax.bar(counts.index, counts.values, color=[COLOR] * 5 + ["#a0aec0"])
    _label_bars(ax, bars)
    ax.set_ylabel("Số tin")
    ax.set_xlabel("Cấp bậc (suy từ tiêu đề tin)")
    ax.set_title("Cấp bậc tuyển dụng")
    return _finish(fig, SOURCE_NOTE + "; Unknown = tiêu đề không nêu cấp bậc (A17)")


def plot_timeline(jobs, skills):
    weekly = jobs["posted_date"].dt.to_period("W-SUN").dt.start_time.value_counts().sort_index()
    ordered = jobs.reset_index().sort_values(["posted_date", "job_id"], kind="mergesort")
    split_date = ordered["posted_date"].iloc[int(len(ordered) * TRAIN_FRAC)]
    fig, ax = _new_fig()
    ax.bar(weekly.index, weekly.values, width=5, color=COLOR)
    ax.axvline(split_date, color=COLOR_2, linestyle="--", linewidth=2)
    ax.text(split_date, ax.get_ylim()[1] * 0.95, f" mốc 70% train / 30% test\n {split_date:%d/%m}",
            color=COLOR_2, va="top", fontsize=11)
    ax.set_xlabel("Tuần đăng tin (datePosted)")
    ax.set_ylabel("Số tin")
    ax.set_title("Thời điểm đăng của các tin còn tuyển ngày 29/09")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    fig.autofmt_xdate()
    return _finish(fig, SOURCE_NOTE + "; snapshot — tin cũ đã hết hạn không còn trên site")


def _boxplot_by(jobs, column, order, title, xlabel):
    paid = jobs[jobs["has_salary"]]
    groups = [(g, paid.loc[paid[column] == g, "salary_mid"]) for g in order]
    groups = [(g, s) for g, s in groups if len(s) > 0]
    fig, ax = _new_fig()
    ax.boxplot([s.values for _, s in groups])
    ax.set_xticks(range(1, len(groups) + 1), [f"{g}\n(n={len(s)})" for g, s in groups])
    ax.set_ylabel("Lương đại diện (triệu VND/tháng)")
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    return _finish(fig, SOURCE_NOTE + "; chỉ tin có công bố lương")


def plot_salary_by_level(jobs, skills):
    return _boxplot_by(jobs, "level_group", LEVEL_ORDER, "Lương theo cấp bậc", "Cấp bậc")


def plot_salary_by_location(jobs, skills):
    paid = jobs[jobs["has_salary"]].copy()
    rows = []
    for col, name in CITY_LABELS.items():
        s = paid.loc[paid[col] == 1, "salary_mid"]
        if len(s):
            rows.append((name, s))
    fig, ax = _new_fig((9, 6))
    ax.boxplot([s.values for _, s in rows])
    ax.set_xticks(range(1, len(rows) + 1), [f"{n}\n(n={len(s)})" for n, s in rows])
    ax.set_ylabel("Lương đại diện (triệu VND/tháng)")
    ax.set_title("Lương theo địa điểm")
    return _finish(fig, SOURCE_NOTE + "; chỉ tin có công bố lương; 1 tin có thể ở nhiều nơi")


def plot_expertise_groups(jobs, skills):
    total = jobs["expertise_group"].value_counts()
    order = sorted(total.index, key=lambda g: (-total[g], g))
    paid = jobs.loc[jobs["has_salary"], "expertise_group"].value_counts().reindex(order, fill_value=0)
    fig, ax = _new_fig((10, 7))
    y = np.arange(len(order))
    ax.barh(y, total[order].values, color="#a0aec0", label="Tất cả tin")
    ax.barh(y, paid.values, color=COLOR, label="Có công bố lương")
    for i, g in enumerate(order):
        ax.text(total[g], i, f" {total[g]} ({paid[g] / total[g]:.0%} có lương)", va="center", fontsize=11)
    ax.set_yticks(y, order)
    ax.invert_yaxis()
    ax.set_xlabel("Số tin")
    ax.set_xlim(0, total.max() * 1.35)
    ax.set_title(f"Nhóm nghề ({jobs['category'].nunique()} giá trị \"Job Expertise\" gộp thành {len(order)} nhóm — A16)")
    ax.legend(loc="lower right")
    return _finish(fig)


def plot_skills_per_job(jobs, skills):
    per_job = skills.sum(axis=1)
    fig, ax = _new_fig()
    ax.hist(per_job, bins=np.arange(0, per_job.max() + 2) - 0.5, color=COLOR, edgecolor="white")
    ax.axvline(per_job.median(), color=COLOR_2, linestyle="--", linewidth=2)
    ax.text(per_job.median(), ax.get_ylim()[1] * 0.95, f" trung vị = {per_job.median():.0f}",
            color=COLOR_2, va="top")
    ax.set_xlabel("Số kỹ năng trích được trong 1 tin")
    ax.set_ylabel("Số tin")
    ax.set_title("Số kỹ năng mỗi tin tuyển dụng yêu cầu")
    return _finish(fig, SOURCE_NOTE + f"; {int((per_job == 0).sum())} tin không bắt được kỹ năng nào")


def skill_lift_matrix(skills, top=15):
    """Lift giữa từng cặp trong top kỹ năng: P(a,b) / (P(a)·P(b)) trên toàn bộ tin."""
    cols = list(skill_share(skills).head(top).index)
    X = skills[cols].to_numpy(dtype=float)
    p = X.mean(axis=0)
    joint = (X.T @ X) / len(X)
    lift = joint / np.outer(p, p)
    np.fill_diagonal(lift, np.nan)
    return pd.DataFrame(lift, index=cols, columns=cols)


def plot_cooccurrence(jobs, skills, top=15):
    lift = skill_lift_matrix(skills, top)
    fig, ax = _new_fig((11, 9))
    im = ax.imshow(lift.values, cmap="RdBu_r", vmin=0, vmax=2)
    ax.set_xticks(range(len(lift)), lift.columns, rotation=60, ha="right")
    ax.set_yticks(range(len(lift)), lift.index)
    for i in range(len(lift)):
        for j in range(len(lift)):
            v = lift.iat[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=9,
                        color="white" if abs(v - 1) > 0.6 else "black")
    fig.colorbar(im, ax=ax, label="Lift (>1: hay đi cùng nhau, <1: ít đi cùng)")
    ax.set_title(f"Mức độ đi kèm giữa {top} kỹ năng phổ biến nhất (lift)")
    return _finish(fig, SOURCE_NOTE + f"; lift tính trên toàn bộ {len(jobs)} tin")


def plot_skills_by_group(jobs, skills, top=12):
    cols = list(skill_share(skills).head(top).index)
    groups = jobs["expertise_group"].value_counts()
    order = sorted(groups.index, key=lambda g: (-groups[g], g))
    table = skills[cols].groupby(jobs["expertise_group"]).mean().reindex(order) * 100
    fig, ax = _new_fig((12, 7))
    im = ax.imshow(table.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(cols)), cols, rotation=45, ha="right")
    ax.set_yticks(range(len(order)), [f"{g} (n={groups[g]})" for g in order])
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            v = table.iat[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=9,
                    color="white" if v > 55 else "black")
    fig.colorbar(im, ax=ax, label="% số tin trong nhóm nghề")
    ax.set_title(f"Top {top} kỹ năng theo nhóm nghề")
    return _finish(fig)


FIGURES = {
    "pipeline_funnel": plot_pipeline_funnel,
    "salary_disclosure": plot_salary_disclosure,
    "salary_distribution": plot_salary_distribution,
    "currency": plot_currency,
    "top_skills": plot_top_skills,
    "locations": plot_locations,
    "levels": plot_levels,
    "timeline": plot_timeline,
    "salary_by_level": plot_salary_by_level,
    "salary_by_location": plot_salary_by_location,
    "expertise_groups": plot_expertise_groups,
    "skills_per_job": plot_skills_per_job,
    "cooccurrence": plot_cooccurrence,
    "skills_by_group": plot_skills_by_group,
}


def save_all(fig_dir: Path = FIG_DIR) -> list[Path]:
    jobs, skills = load_data()
    paths = []
    for name, func in FIGURES.items():
        fig = func(jobs, skills)
        paths.append(save_figure(fig, name, fig_dir))
        plt.close(fig)
    return paths
