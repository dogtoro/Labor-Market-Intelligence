"""
Data contract validation — ném ValueError nếu DataFrame sai schema.

Dùng:
    from src.contract import validate_parsed, validate_clean, validate_skills
    validate_parsed(df)  # ném ValueError nếu sai
"""

from __future__ import annotations

import pandas as pd

PARSED_REQUIRED_COLS = {
    "job_id": "object",
    "url": "object",
    "title": "object",
    "company": "object",
    "jd_text": "object",
    "crawled_at": "object",
}

PARSED_OPTIONAL_COLS = {
    "level": "object",
    "location": "object",
    "posted_date": "object",
    "category": "object",
    "salary_raw": "object",
}

CLEAN_EXTRA_REQUIRED = {
    "salary_status": "object",
    "is_duplicate": "bool",
}

CLEAN_EXTRA_OPTIONAL = {
    "salary_min": "float64",
    "salary_max": "float64",
    "currency_original": "object",
}

SALARY_STATUS_VALUES = {"full_range", "one_sided", "undisclosed"}


def _check_required_columns(df: pd.DataFrame, required: dict[str, str], layer: str) -> list[str]:
    errors: list[str] = []
    for col, expected_dtype in required.items():
        if col not in df.columns:
            errors.append(f"[{layer}] Thiếu cột bắt buộc: '{col}'")
        elif not df[col].notna().all():
            null_rows = df.index[df[col].isna()].tolist()
            sample = null_rows[:5]
            errors.append(
                f"[{layer}] Cột bắt buộc '{col}' có {len(null_rows)} giá trị null "
                f"(ví dụ dòng: {sample})"
            )
    return errors


def _check_unique(df: pd.DataFrame, col: str, layer: str) -> list[str]:
    if col in df.columns and df[col].duplicated().any():
        n_dup = df[col].duplicated().sum()
        return [f"[{layer}] Cột '{col}' có {n_dup} giá trị trùng (phải unique)"]
    return []


def _check_enum(df: pd.DataFrame, col: str, valid: set[str], layer: str) -> list[str]:
    if col not in df.columns:
        return []
    actual = set(df[col].dropna().unique())
    bad = actual - valid
    if bad:
        return [f"[{layer}] Cột '{col}' có giá trị không hợp lệ: {bad}. Chỉ chấp nhận: {valid}"]
    return []


def _check_salary_semantics(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if not {"salary_status", "salary_min", "salary_max"}.issubset(df.columns):
        return errors

    for idx, row in df[["salary_status", "salary_min", "salary_max"]].iterrows():
        status = row["salary_status"]
        lo = row["salary_min"]
        hi = row["salary_max"]
        has_lo = pd.notna(lo)
        has_hi = pd.notna(hi)

        if has_lo and lo <= 0:
            errors.append(f"[clean] Dòng {idx}: salary_min phải > 0, hiện tại: {lo}")
        if has_hi and hi <= 0:
            errors.append(f"[clean] Dòng {idx}: salary_max phải > 0, hiện tại: {hi}")

        if status == "full_range":
            if not (has_lo and has_hi):
                errors.append(f"[clean] Dòng {idx}: full_range phải có cả salary_min và salary_max")
            elif lo > hi:
                errors.append(f"[clean] Dòng {idx}: salary_min ({lo}) > salary_max ({hi})")
        elif status == "one_sided":
            if has_lo == has_hi:
                errors.append(
                    f"[clean] Dòng {idx}: one_sided phải có đúng một trong salary_min/salary_max"
                )
        elif status == "undisclosed":
            if has_lo or has_hi:
                errors.append(
                    f"[clean] Dòng {idx}: undisclosed phải có salary_min và salary_max là null"
                )

    return errors


def validate_parsed(df: pd.DataFrame) -> None:
    errors: list[str] = []
    errors += _check_required_columns(df, PARSED_REQUIRED_COLS, "parsed")
    errors += _check_unique(df, "job_id", "parsed")

    if errors:
        raise ValueError("Parsed data contract vi phạm:\n" + "\n".join(errors))


def validate_clean(df: pd.DataFrame) -> None:
    errors: list[str] = []
    all_required = {**PARSED_REQUIRED_COLS, **CLEAN_EXTRA_REQUIRED}
    errors += _check_required_columns(df, all_required, "clean")
    errors += _check_unique(df, "job_id", "clean")
    errors += _check_enum(df, "salary_status", SALARY_STATUS_VALUES, "clean")

    for col in ("salary_min", "salary_max"):
        if col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0 and not pd.api.types.is_float_dtype(df[col]):
                errors.append(f"[clean] Cột '{col}' phải là float64, hiện tại: {df[col].dtype}")

    errors += _check_salary_semantics(df)

    if errors:
        raise ValueError("Clean data contract vi phạm:\n" + "\n".join(errors))


def validate_skills(df: pd.DataFrame) -> None:
    errors: list[str] = []

    if "job_id" not in df.columns:
        errors.append("[skills] Thiếu cột bắt buộc: 'job_id'")
    else:
        errors += _check_unique(df, "job_id", "skills")

    skill_cols = [c for c in df.columns if c != "job_id"]
    if not skill_cols:
        errors.append("[skills] Không có cột kỹ năng nào ngoài 'job_id'")
    else:
        for col in skill_cols:
            vals = set(df[col].dropna().unique())
            bad = vals - {0, 1}
            if bad:
                errors.append(f"[skills] Cột '{col}' chứa giá trị không hợp lệ: {bad}. Chỉ chấp nhận 0/1")
                break

    if errors:
        raise ValueError("Skills matrix contract vi phạm:\n" + "\n".join(errors))
