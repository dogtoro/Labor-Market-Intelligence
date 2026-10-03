"""Xuất toàn bộ biểu đồ EDA → reports/figures/eda_*.png (bước `figures` của pipeline)."""
import matplotlib

matplotlib.use("Agg")

from src.viz.eda import save_all  # noqa: E402

if __name__ == "__main__":
    for path in save_all():
        print(f"Saved {path}")
