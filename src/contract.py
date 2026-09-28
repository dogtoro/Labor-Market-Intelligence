"""
Data contract validation — ném ValueError nếu DataFrame sai schema.

Dùng:
    from src.contract import validate_parsed, validate_clean, validate_skills
    validate_parsed(df)  # ném ValueError nếu sai
"""

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

PARSED_REQUIRED_COLS = {
    "job_id": "object",      # str
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_required_columns(df: pd.DataFrame, required: dict[str, str], layer: str) -> list[str]:
    """Return list of error messages for missing/wrong-type required columns."""
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
    """Return error if column has duplicates."""
    if col in df.columns and df[col].duplicated().any():
        n_dup = df[col].duplicated().sum()
        return [f"[{layer}] Cột '{col}' có {n_dup} giá trị trùng (phải unique)"]
    return []


def _check_enum(df: pd.DataFrame, col: str, valid: set[str], layer: str) -> list[str]:
    """Return error if column contains values outside the valid set."""
    if col not in df.columns:
        return []
    actual = set(df[col].dropna().unique())
    bad = actual - valid
    if bad:
        return [f"[{layer}] Cột '{col}' có giá trị không hợp lệ: {bad}. Chỉ chấp nhận: {valid}"]
    return []


# ---------------------------------------------------------------------------
# Public validators
# ---------------------------------------------------------------------------

def validate_parsed(df: pd.DataFrame) -> None:
    """Validate a parsed DataFrame against the Tầng 2 schema.

    Raises ValueError with all errors concatenated.
    """
    errors: list[str] = []
    errors += _check_required_columns(df, PARSED_REQUIRED_COLS, "parsed")
    errors += _check_unique(df, "job_id", "parsed")

    if errors:
        raise ValueError("Parsed data contract vi phạm:\n" + "\n".join(errors))


def validate_clean(df: pd.DataFrame) -> None:
    """Validate a clean DataFrame against the Tầng 3 schema.

    Raises ValueError with all errors concatenated.
    """
    errors: list[str] = []
    # Must have all parsed required cols + clean extras
    all_required = {**PARSED_REQUIRED_COLS, **CLEAN_EXTRA_REQUIRED}
    errors += _check_required_columns(df, all_required, "clean")
    errors += _check_unique(df, "job_id", "clean")
    errors += _check_enum(df, "salary_status", SALARY_STATUS_VALUES, "clean")

    # salary_min / salary_max should be float if present
    for col in ("salary_min", "salary_max"):
        if col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                if not pd.api.types.is_float_dtype(df[col]):
                    errors.append(f"[clean] Cột '{col}' phải là float64, hiện tại: {df[col].dtype}")

    if errors:
        raise ValueError("Clean data contract vi phạm:\n" + "\n".join(errors))


def validate_skills(df: pd.DataFrame) -> None:
    """Validate a skills matrix DataFrame against the Tầng 4 schema.

    Raises ValueError with all errors concatenated.
    """
    errors: list[str] = []

    if "job_id" not in df.columns:
        errors.append("[skills] Thiếu cột bắt buộc: 'job_id'")
    else:
        errors += _check_unique(df, "job_id", "skills")

    # All non-job_id columns must be numeric (0 or 1)
    skill_cols = [c for c in df.columns if c != "job_id"]
    if not skill_cols:
        errors.append("[skills] Không có cột kỹ năng nào ngoài 'job_id'")
    else:
        for col in skill_cols:
            vals = set(df[col].dropna().unique())
            bad = vals - {0, 1}
            if bad:
                errors.append(f"[skills] Cột '{col}' chứa giá trị không hợp lệ: {bad}. Chỉ chấp nhận 0/1")
                break  # Don't flood with errors for every column

    if errors:
        raise ValueError("Skills matrix contract vi phạm:\n" + "\n".join(errors))
