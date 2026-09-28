"""
make_manifest.py — Đếm số dòng và tính SHA-256 cho data/processed.

Xuất ra docs/MANIFEST.json. KHÔNG hardcode con số.
"""

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "MANIFEST.json"


def sha256_file(path: Path) -> str:
    """Tính SHA-256 hash của 1 file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def count_parquet_rows(path: Path) -> int:
    """Đếm số dòng trong file parquet."""
    try:
        import pandas as pd
        df = pd.read_parquet(path)
        return len(df)
    except Exception as e:
        print(f"  ⚠ Không đọc được {path.name}: {e}")
        return -1


def main():
    if not PROCESSED_DIR.exists():
        print(f"⚠ Thư mục {PROCESSED_DIR} chưa tồn tại. Tạo manifest rỗng.")
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps({"files": [], "note": "No processed data yet"}, indent=2, ensure_ascii=False))
        return

    files = sorted(PROCESSED_DIR.glob("*"))
    if not files:
        print("⚠ Không có file nào trong data/processed/.")
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps({"files": [], "note": "No processed data yet"}, indent=2, ensure_ascii=False))
        return

    manifest = {"files": []}
    for f in files:
        if f.is_file():
            entry = {
                "filename": f.name,
                "sha256": sha256_file(f),
                "size_bytes": f.stat().st_size,
            }
            if f.suffix == ".parquet":
                entry["row_count"] = count_parquet_rows(f)
            manifest["files"].append(entry)
            print(f"  ✓ {f.name}: {entry['sha256'][:16]}… ({entry['size_bytes']:,} bytes)")

    # Overall hash (hash of all individual hashes, sorted by filename)
    combined = "".join(e["sha256"] for e in sorted(manifest["files"], key=lambda x: x["filename"]))
    manifest["combined_sha256"] = hashlib.sha256(combined.encode()).hexdigest()

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✅ Manifest ghi vào {MANIFEST_PATH}")
    print(f"   Combined SHA-256: {manifest['combined_sha256']}")


if __name__ == "__main__":
    main()
