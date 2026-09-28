"""
run_pipeline.py — Điều phối pipeline từng bước.

Usage:
    python scripts/run_pipeline.py <step>

Steps: pilot, crawl, parse, clean, skills, rules, cluster, classify, figures, all, test, manifest
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STEPS = {
    "pilot": "Crawl thử 10 tin (pilot test)",
    "crawl": "Crawl đầy đủ từ TopCV sitemap",
    "parse": "Parse HTML → data/interim/jobs_parsed.parquet",
    "clean": "Dedup + chuẩn hóa lương → data/processed/jobs_clean.parquet",
    "skills": "Trích kỹ năng → data/processed/skill_matrix.parquet",
    "rules": "Chạy Apriori association rules",
    "cluster": "Chạy hierarchical clustering (Jaccard)",
    "classify": "Chạy decision tree phân lớp lương (tùy chọn)",
    "figures": "Xuất hình vẽ → reports/figures/",
    "all": "Chạy toàn bộ pipeline",
    "test": "Chạy pytest",
    "manifest": "Tạo SHA-256 manifest",
}


def run_step(step: str):
    """Run a single pipeline step."""
    print(f"\n{'='*60}")
    print(f"▶ {step}: {STEPS.get(step, '???')}")
    print(f"{'='*60}\n")

    if step == "test":
        subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=PROJECT_ROOT, check=True)
        return

    if step == "manifest":
        subprocess.run([sys.executable, "scripts/make_manifest.py"], cwd=PROJECT_ROOT, check=True)
        return

    if step == "all":
        for s in ["parse", "clean", "skills", "rules", "cluster", "figures", "manifest"]:
            run_step(s)
        return

    # Each step will have its own script in src/<module>/
    # For now, print a placeholder
    print(f"⚠ Step '{step}' chưa được implement.")
    print(f"  → Người phụ trách cần viết logic trong src/ tương ứng.")
    print(f"  → Xem docs/tasks/ để biết đầu vào/đầu ra mong đợi.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_pipeline.py <step>")
        print("\nCác step có sẵn:")
        for step, desc in STEPS.items():
            print(f"  {step:12s}  {desc}")
        sys.exit(1)

    step = sys.argv[1].lower()
    if step not in STEPS:
        print(f"❌ Step không hợp lệ: '{step}'")
        print(f"Các step hợp lệ: {', '.join(STEPS.keys())}")
        sys.exit(1)

    run_step(step)


if __name__ == "__main__":
    main()
