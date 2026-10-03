import math

import pandas as pd

from scripts.verify_a7 import compute_coverage


def test_compute_coverage_basic():
    labels = pd.DataFrame({
        "skills_extracted": ["python; sql; docker", "java", ""],
        # trino không có trong từ điển → tính là bị sót
        "skills_manual": ["python; sql; trino", "java; spring", "python"],
    })
    per_job, overall, missed = compute_coverage(labels)

    assert list(per_job["n_manual"]) == [3, 2, 1]
    assert list(per_job["n_hit"]) == [2, 1, 0]
    assert per_job.loc[0, "missed"] == "trino"
    # micro: (2 + 1 + 0) / (3 + 2 + 1) = 0.5
    assert overall == 0.5
    assert missed == {"trino": 1, "spring": 1, "python": 1}


def test_compute_coverage_ignores_unlabelled_rows():
    labels = pd.DataFrame({
        "skills_extracted": ["python", "sql"],
        "skills_manual": ["python", None],
    })
    per_job, overall, _ = compute_coverage(labels)

    assert math.isnan(per_job.loc[1, "coverage"])
    assert overall == 1.0


def test_compute_coverage_normalises_case_and_spaces():
    labels = pd.DataFrame({
        "skills_extracted": ["power_bi;sql"],
        "skills_manual": [" Power_BI ; SQL "],
    })
    _, overall, missed = compute_coverage(labels)

    assert overall == 1.0
    assert not missed
