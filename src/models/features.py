"""Chuẩn bị dữ liệu dùng chung cho clustering, decision tree và bias analysis (Task 0)."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "MANIFEST.json"

# Giá trị gốc của cột location (JSON-LD addressRegion của ITviec), nối bằng "; " khi tin có nhiều nơi
LOCATION_COLUMNS = {
    "Hồ Chí Minh": "loc_hcm",
    "Hà Nội": "loc_hn",
    "Đà Nẵng": "loc_dn",
    "Thành phố khác": "loc_other",
}

# Nhãn do src/parse/parser.py::infer_level sinh ra → nhóm dùng cho model
LEVEL_GROUPS = {
    "Intern": "Junior",
    "Fresher": "Junior",
    "Junior": "Junior",
    "Middle": "Middle",
    "Senior": "Senior",
    "Lead": "Lead",
    "Principal": "Lead",
    "Manager": "Manager",
    "Head": "Manager",
    "Director": "Manager",
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_and_verify_data(data_dir: Path = DATA_DIR, manifest_path: Path = MANIFEST_PATH):
    """Đọc jobs_clean + skill_matrix và kiểm SHA-256 với MANIFEST.

    Raises:
        FileNotFoundError: thiếu file dữ liệu (tải từ Drive về data/processed/).
        ValueError: hash lệch MANIFEST hoặc MANIFEST không có file đó.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    expected = {entry["filename"]: entry["sha256"] for entry in manifest["files"]}

    frames = []
    for name in ("jobs_clean.parquet", "skill_matrix.parquet"):
        path = Path(data_dir) / "processed" / name
        if not path.exists():
            raise FileNotFoundError(
                f"Thiếu {path}. Tải đúng bản trong MANIFEST từ Drive về data/processed/."
            )
        if name not in expected:
            raise ValueError(f"{manifest_path.name} không có {name} — chạy lại make_manifest.py.")
        actual = _sha256(path)
        if actual != expected[name]:
            raise ValueError(
                f"Hash {name} lệch MANIFEST: {actual[:16]}… ≠ {expected[name][:16]}…. "
                "Dùng đúng bản dữ liệu đã freeze."
            )
        frames.append(pd.read_parquet(path))

    return frames[0], frames[1]


def calculate_salary_mid(df: pd.DataFrame) -> pd.Series:
    """Lương đại diện (triệu VND/tháng) theo DECISIONS 01/10.

    full_range → trung bình 2 cận; one_sided → cận duy nhất; undisclosed → NaN.
    """
    s_mid = pd.Series(np.nan, index=df.index, dtype=float)

    full_mask = df["salary_status"] == "full_range"
    s_mid[full_mask] = (df.loc[full_mask, "salary_min"] + df.loc[full_mask, "salary_max"]) / 2.0

    one_mask = df["salary_status"] == "one_sided"
    s_mid[one_mask] = df.loc[one_mask, "salary_min"].fillna(df.loc[one_mask, "salary_max"])

    return s_mid


def extract_location_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Multi-hot: loc_hcm, loc_hn, loc_dn, loc_other. Thiếu location → tất cả 0.

    Raises:
        ValueError: gặp giá trị location ngoài LOCATION_COLUMNS.
    """
    columns = list(LOCATION_COLUMNS.values())
    flags = pd.DataFrame(0, index=df.index, columns=columns, dtype="int8")

    for idx, value in df["location"].items():
        if pd.isna(value) or not str(value).strip():
            continue
        for part in str(value).split(";"):
            part = part.strip()
            if part not in LOCATION_COLUMNS:
                raise ValueError(f"Location lạ: {part!r} (dòng {idx}). Bổ sung vào LOCATION_COLUMNS.")
            flags.at[idx, LOCATION_COLUMNS[part]] = 1

    return flags


def clean_level_feature(df: pd.DataFrame) -> pd.Series:
    """Gộp level: Intern/Fresher/Junior → Junior; Lead/Principal → Lead;
    Manager/Head/Director → Manager; thiếu → Unknown.

    Raises:
        ValueError: gặp nhãn level ngoài LEVEL_GROUPS.
    """
    levels = df["level"]
    unknown = sorted(set(levels.dropna()) - set(LEVEL_GROUPS))
    if unknown:
        raise ValueError(f"Level lạ: {unknown}. Bổ sung vào LEVEL_GROUPS.")
    return levels.map(LEVEL_GROUPS).fillna("Unknown")
