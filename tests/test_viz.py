"""Smoke tests for src/viz/eda.py — need the frozen data (from Drive); skipped otherwise."""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from src.viz import eda  # noqa: E402


@pytest.fixture(scope="module")
def data():
    try:
        return eda.load_data()
    except FileNotFoundError:
        pytest.skip("data/processed/*.parquet missing (download from Drive)")


def test_load_data_shapes(data):
    jobs, skills = data
    assert len(jobs) == len(skills)                      # skill_matrix reindexed to every job
    assert set(skills.to_numpy().ravel()) <= {0, 1}
    assert jobs["expertise_group"].notna().all()
    assert set(jobs["level_group"]) <= set(eda.LEVEL_ORDER)


def test_salary_tertiles_match_decision(data):
    jobs, _ = data
    labels, _ = eda.salary_tertiles(jobs)
    assert labels.value_counts().reindex(eda.SALARY_CLASSES).tolist() == [60, 55, 57]  # DECISIONS milestone 2


def test_skill_lift_matrix_symmetric(data):
    _, skills = data
    lift = eda.skill_lift_matrix(skills, top=5)
    assert lift.shape == (5, 5)
    assert (lift.fillna(0).to_numpy() == lift.fillna(0).to_numpy().T).all()


@pytest.mark.parametrize("name", list(eda.FIGURES))
def test_every_figure_renders(data, name):
    jobs, skills = data
    fig = eda.FIGURES[name](jobs, skills)
    assert fig.axes and fig.axes[0].get_title()
    plt.close(fig)
