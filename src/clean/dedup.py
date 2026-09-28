"""
Dedup — loại tin tuyển dụng trùng lặp.

Tiêu chí: cùng công ty + tiêu đề tương tự (≥ ngưỡng) + ngày đăng cách nhau ≤ N ngày.
Dùng SequenceMatcher thay vì TF-IDF/cosine để tránh thêm phụ thuộc.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from datetime import datetime, timedelta

import pandas as pd


def title_similarity(a: str, b: str) -> float:
    """Tính độ tương tự giữa 2 tiêu đề (0.0–1.0) bằng SequenceMatcher."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_duplicates(
    df: pd.DataFrame,
    *,
    title_threshold: float = 0.85,
    date_window_days: int = 7,
) -> pd.Series:
    """Đánh dấu các tin trùng lặp.

    Args:
        df: DataFrame có cột 'company', 'title', 'posted_date' (ISO str hoặc NaT).
        title_threshold: Ngưỡng tương tự tiêu đề (0–1). Mặc định 0.85.
        date_window_days: Khoảng cách ngày tối đa để coi là trùng.

    Returns:
        pd.Series[bool]: True = bản trùng (nên loại), False = bản giữ lại.
    """
    is_dup = pd.Series(False, index=df.index)

    # Parse dates safely
    dates = pd.to_datetime(df.get("posted_date"), errors="coerce")

    # Group by company for efficiency
    grouped = df.groupby("company", sort=False)

    for _company, group in grouped:
        if len(group) < 2:
            continue

        indices = group.index.tolist()
        for i in range(len(indices)):
            if is_dup[indices[i]]:
                continue  # already marked
            for j in range(i + 1, len(indices)):
                if is_dup[indices[j]]:
                    continue

                idx_i, idx_j = indices[i], indices[j]

                # Title similarity
                sim = title_similarity(
                    df.at[idx_i, "title"],
                    df.at[idx_j, "title"],
                )
                if sim < title_threshold:
                    continue

                # Date proximity
                d_i, d_j = dates[idx_i], dates[idx_j]
                if pd.notna(d_i) and pd.notna(d_j):
                    if abs((d_i - d_j).days) > date_window_days:
                        continue

                # Mark the later one (j) as duplicate
                is_dup[idx_j] = True

    return is_dup
