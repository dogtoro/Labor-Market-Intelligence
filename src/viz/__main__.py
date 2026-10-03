"""Export all EDA charts → reports/figures/eda_*.png (the pipeline's `figures` step)."""
import matplotlib

matplotlib.use("Agg")

from src.viz.eda import save_all  # noqa: E402

if __name__ == "__main__":
    for path in save_all():
        print(f"Saved {path}")
