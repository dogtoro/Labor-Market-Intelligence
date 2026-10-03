"""Kiểm chứng A7 — độ phủ của từ điển kỹ năng trên 20 JD ngẫu nhiên.

Dùng đúng extractor của pipeline (src/skills/extractor.py) để kết quả khớp skill_matrix.
Chỉ ghi tên vị trí/công ty và tên kỹ năng — không chép nguyên văn JD (cam kết ToS ITviec).

Usage:
    python scripts/verify_a7.py --template   # tạo reports/a7_manual_labels.csv (cột skills_manual để trống)
    python scripts/verify_a7.py --show N     # in JD thứ N (0–19) ra terminal để gán nhãn, không lưu file
    python scripts/verify_a7.py              # đọc nhãn tay, tính độ phủ -> reports/A7_evaluation.md

Quy ước nhãn tay (cột skills_manual): tên kỹ năng ngăn cách bằng ";".
Kỹ năng có trong từ điển ghi đúng key (vd. power_bi); kỹ năng không có trong từ điển
vẫn ghi vào (vd. trino) — được tính là bị sót, vì A7 đo độ phủ của chính từ điển.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.skills.extractor import _build_patterns, extract_skills, load_skill_dict  # noqa: E402

CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "jobs_clean.parquet"
LABELS_PATH = PROJECT_ROOT / "reports" / "a7_manual_labels.csv"
OUT_PATH = PROJECT_ROOT / "reports" / "A7_evaluation.md"
SAMPLE_SIZE = 20
SEED = 42
TARGET = 0.80


def load_sample(seed: int = SEED, path: Path = CLEAN_PATH) -> pd.DataFrame:
    """20 JD ngẫu nhiên. Seed khác SEED → loại các JD đã có trong mẫu gốc (bộ kiểm tra độc lập)."""
    df = pd.read_parquet(path)
    if seed != SEED:
        base_ids = set(df.sample(SAMPLE_SIZE, random_state=SEED)["job_id"])
        df = df[~df["job_id"].isin(base_ids)]
    return df.sample(SAMPLE_SIZE, random_state=seed).reset_index(drop=True)


def paths_for_seed(seed: int) -> tuple[Path, Path]:
    """(file nhãn, file báo cáo) theo seed; seed gốc giữ tên file cũ."""
    if seed == SEED:
        return LABELS_PATH, OUT_PATH
    return (
        PROJECT_ROOT / "reports" / f"a7_manual_labels_seed{seed}.csv",
        PROJECT_ROOT / "reports" / f"A7_evaluation_seed{seed}.md",
    )


def _split_skills(value) -> set[str]:
    if value is None or pd.isna(value):
        return set()
    return {s.strip().lower() for s in str(value).split(";") if s.strip()}


def compute_coverage(labels: pd.DataFrame):
    """Compare manual labels with extracted skills.

    Args:
        labels: DataFrame with columns ``skills_extracted`` and ``skills_manual``
            (both ";"-separated skill names).

    Returns:
        (per_job, overall, missed_counter) where ``per_job`` has n_manual, n_hit,
        coverage and missed per row; ``overall`` is the micro coverage
        (total hits / total manual skills); ``missed_counter`` counts missed skills.
        Rows with no manual skills get coverage NaN and do not affect the total.
    """
    rows = []
    missed_counter: Counter = Counter()
    total_manual = total_hit = 0

    for _, row in labels.iterrows():
        manual = _split_skills(row["skills_manual"])
        extracted = _split_skills(row["skills_extracted"])
        hit = manual & extracted
        missed = manual - extracted
        missed_counter.update(missed)
        total_manual += len(manual)
        total_hit += len(hit)
        rows.append({
            "n_manual": len(manual),
            "n_hit": len(hit),
            "coverage": len(hit) / len(manual) if manual else float("nan"),
            "missed": "; ".join(sorted(missed)),
        })

    per_job = pd.DataFrame(rows, index=labels.index)
    overall = total_hit / total_manual if total_manual else float("nan")
    return per_job, overall, missed_counter


def _extract_joined(text: str, patterns) -> str:
    found = extract_skills(str(text), patterns)
    return "; ".join(s for s, hit in found.items() if hit)


def refresh_extracted(labels: pd.DataFrame, sample: pd.DataFrame) -> pd.DataFrame:
    """Recompute skills_extracted with the current extractor (keeps manual labels)."""
    patterns = _build_patterns(load_skill_dict())
    jd_by_id = sample.set_index("job_id")["jd_text"]
    out = labels.copy()
    out["skills_extracted"] = out["job_id"].map(lambda j: _extract_joined(jd_by_id[j], patterns))
    return out


def write_template(sample: pd.DataFrame, path: Path = LABELS_PATH) -> None:
    patterns = _build_patterns(load_skill_dict())
    records = []
    for i, row in sample.iterrows():
        records.append({
            "idx": i,
            "job_id": row["job_id"],
            "title": row["title"],
            "company": row["company"],
            "skills_extracted": _extract_joined(row["jd_text"], patterns),
            "skills_manual": "",
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(path, index=False, encoding="utf-8")
    print(f"Template -> {path}. Điền cột skills_manual (dùng --show N để đọc JD).")


def show_jd(sample: pd.DataFrame, n: int) -> None:
    row = sample.iloc[n]
    print(f"[{n}] {row['title']} — {row['company']}\n{'-' * 60}\n{row['jd_text']}")


def write_report(labels: pd.DataFrame, path: Path = OUT_PATH, seed: int = SEED,
                 labels_path: Path = LABELS_PATH, note: str = "") -> float:
    per_job, overall, missed_counter = compute_coverage(labels)
    labelled = per_job["n_manual"] > 0

    lines = [
        "# A7 Evaluation — Độ phủ từ điển kỹ năng trên 20 JD ngẫu nhiên",
        "",
        f"Sinh bởi `scripts/verify_a7.py` (mẫu {SAMPLE_SIZE} JD, seed={seed}). "
        f"Nhãn tay ở `reports/{labels_path.name}`.",
        "",
        *([note, ""] if note else []),
        f"- JD đã gán nhãn: **{int(labelled.sum())}/{len(labels)}**",
        f"- Tổng kỹ năng thực tế (nhãn tay): **{int(per_job['n_manual'].sum())}**",
        f"- Extractor bắt đúng: **{int(per_job['n_hit'].sum())}**",
        f"- **Độ phủ (micro): {overall:.1%}** — ngưỡng A7: {TARGET:.0%} → "
        f"**{'ĐẠT' if overall >= TARGET else 'CHƯA ĐẠT'}**",
        "",
        "## Kỹ năng bị sót nhiều nhất",
        "",
    ]
    if missed_counter:
        lines += ["| Kỹ năng | Số JD bị sót |", "|---|---|"]
        # Sắp theo (số lần giảm dần, tên) — most_common() để hoà theo thứ tự chèn từ set, đổi theo PYTHONHASHSEED
        top_missed = sorted(missed_counter.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
        lines += [f"| {skill} | {count} |" for skill, count in top_missed]
    else:
        lines.append("Không có kỹ năng nào bị sót.")

    lines += [
        "",
        "## Chi tiết từng JD",
        "",
        "| # | Vị trí (Công ty) | Nhãn tay | Bắt đúng | Độ phủ | Bị sót |",
        "|---|---|---|---|---|---|",
    ]
    for i, row in labels.iterrows():
        r = per_job.loc[i]
        cov = "—" if pd.isna(r["coverage"]) else f"{r['coverage']:.0%}"
        lines.append(
            f"| {row['idx']} | {row['title']} ({row['company']}) | {r['n_manual']} | "
            f"{r['n_hit']} | {cov} | {r['missed']} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Độ phủ: {overall:.1%} -> {path}")
    return overall


def main():
    parser = argparse.ArgumentParser(description="Kiểm chứng A7 — độ phủ từ điển kỹ năng")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--template", action="store_true", help="tạo file nhãn tay")
    group.add_argument("--show", type=int, metavar="N", help="in JD thứ N ra terminal")
    parser.add_argument("--seed", type=int, default=SEED,
                        help=f"seed lấy mẫu (mặc định {SEED}); seed khác = bộ kiểm tra độc lập, không trùng mẫu gốc")
    args = parser.parse_args()
    labels_path, out_path = paths_for_seed(args.seed)

    if args.template:
        write_template(load_sample(args.seed), path=labels_path)
    elif args.show is not None:
        show_jd(load_sample(args.seed), args.show)
    else:
        if not labels_path.exists():
            sys.exit(f"Chưa có {labels_path}. Chạy --template rồi điền nhãn tay trước.")
        labels = refresh_extracted(pd.read_csv(labels_path, encoding="utf-8"), load_sample(args.seed))
        labels.to_csv(labels_path, index=False, encoding="utf-8")
        note = "" if args.seed == SEED else (
            "> **Bộ kiểm tra độc lập:** 20 JD không trùng mẫu seed=42; từ điển **không** được chỉnh "
            "theo bộ này, nên con số ở đây không bị thiên lệch do chọn alias."
        )
        write_report(labels, path=out_path, seed=args.seed, labels_path=labels_path, note=note)


if __name__ == "__main__":
    main()
