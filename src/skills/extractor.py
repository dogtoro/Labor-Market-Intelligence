"""
Skill extractor — trích kỹ năng từ JD text bằng từ điển.

KHÔNG dùng NLP. Chỉ string matching (case-insensitive, word boundary).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

# Default path to skill dictionary
_DEFAULT_DICT_PATH = Path(__file__).parent / "skill_dict.json"


def load_skill_dict(path: str | Path | None = None) -> dict[str, list[str]]:
    """Load skill dictionary from JSON.

    Format: {"skill_name": ["alias1", "Alias2", ...], ...}

    Returns:
        dict mapping canonical skill name → list of aliases.
    """
    p = Path(path) if path else _DEFAULT_DICT_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# Alias mơ hồ (trùng từ tiếng Anh thông thường) → chỉ khớp đúng chữ hoa/thường.
# Giá trị là lookahead loại trừ thêm (rỗng nếu không cần), vd. "Go" không khớp "Go-live", "Go to".
CASE_SENSITIVE_ALIASES = {
    "React": "",
    "Spring": "",
    "Excel": "",
    "Swift": "",  # SWIFT viết hoa toàn bộ là chuẩn ngân hàng, không phải ngôn ngữ iOS
    "Go": r"(?![- ](?:live|to)\b)",
}


def _build_patterns(skill_dict: dict[str, list[str]]) -> dict[str, re.Pattern]:
    """Build compiled regex patterns for each skill.

    Each pattern matches any alias as a whole word (case-insensitive by default).
    Aliases listed in CASE_SENSITIVE_ALIASES are matched case-sensitively
    via ``(?-i:...)`` to avoid false positives on common English words,
    followed by an optional exclusion lookahead.
    """
    patterns = {}
    for skill, aliases in skill_dict.items():
        parts = []
        for a in aliases:
            escaped = re.escape(a)
            if a in CASE_SENSITIVE_ALIASES:
                parts.append(f"(?-i:{escaped}){CASE_SENSITIVE_ALIASES[a]}")
            else:
                parts.append(escaped)
        pat = "|".join(parts)
        patterns[skill] = re.compile(rf"(?<![\w+#.])(?:{pat})(?![\w+#])", re.IGNORECASE)
    return patterns


def extract_skills(text: str, patterns: dict[str, re.Pattern]) -> dict[str, int]:
    """Extract skills from a single JD text.

    Returns:
        dict mapping skill name → 1 (present) or 0 (absent).
    """
    result = {}
    for skill, pattern in patterns.items():
        result[skill] = 1 if pattern.search(text) else 0
    return result


def build_skill_matrix(
    df: pd.DataFrame,
    skill_dict: dict[str, list[str]] | None = None,
    dict_path: str | Path | None = None,
    min_count: int = 5,
) -> pd.DataFrame:
    """Build binary skill matrix from a DataFrame with 'job_id' and 'jd_text' columns.

    Args:
        df: DataFrame with 'job_id' and 'jd_text' columns.
        skill_dict: Pre-loaded skill dictionary. If None, loads from dict_path or default.
        dict_path: Path to skill_dict.json (used if skill_dict is None).
        min_count: Minimum number of jobs a skill must appear in to be kept.

    Returns:
        DataFrame with 'job_id' + one column per skill (0/1 int8).
    """
    if skill_dict is None:
        skill_dict = load_skill_dict(dict_path)

    patterns = _build_patterns(skill_dict)

    rows = []
    for _, row in df.iterrows():
        skills = extract_skills(str(row.get("jd_text", "")), patterns)
        skills["job_id"] = row["job_id"]
        rows.append(skills)

    matrix = pd.DataFrame(rows)

    # Move job_id to first column
    cols = ["job_id"] + [c for c in matrix.columns if c != "job_id"]
    matrix = matrix[cols]

    # Filter skills with < min_count occurrences
    skill_cols = [c for c in matrix.columns if c != "job_id"]
    counts = matrix[skill_cols].sum()
    keep = counts[counts >= min_count].index.tolist()
    drop = counts[counts < min_count].index.tolist()

    if drop:
        matrix = matrix.drop(columns=drop)

    # Convert to int8 for efficiency
    skill_cols = [c for c in matrix.columns if c != "job_id"]
    matrix[skill_cols] = matrix[skill_cols].astype("int8")

    return matrix
