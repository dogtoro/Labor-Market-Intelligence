"""Tests for data contract validation."""

import pandas as pd
import pytest

from src.contract import validate_clean, validate_parsed, validate_skills


class TestValidateParsed:
    def test_valid(self):
        df = pd.DataFrame([{
            "job_id": "j1", "url": "https://example.com/1", "title": "Data Engineer",
            "company": "ABC", "jd_text": "Some JD text", "crawled_at": "2026-09-25T10:00:00+07:00",
        }])
        validate_parsed(df)

    def test_missing_required_column(self):
        df = pd.DataFrame([{"job_id": "j1", "url": "https://example.com/1"}])
        with pytest.raises(ValueError, match="Thiếu cột bắt buộc"):
            validate_parsed(df)

    def test_duplicate_job_id(self):
        df = pd.DataFrame([
            {"job_id": "j1", "url": "u1", "title": "t1", "company": "c1", "jd_text": "jd1", "crawled_at": "ct1"},
            {"job_id": "j1", "url": "u2", "title": "t2", "company": "c2", "jd_text": "jd2", "crawled_at": "ct2"},
        ])
        with pytest.raises(ValueError, match="trùng"):
            validate_parsed(df)


class TestValidateClean:
    def _make_valid(self):
        return pd.DataFrame([{
            "job_id": "j1", "url": "https://example.com/1", "title": "Data Engineer",
            "company": "ABC", "jd_text": "text", "crawled_at": "2026-09-25T10:00:00+07:00",
            "salary_min": 15.0, "salary_max": 25.0, "salary_status": "full_range",
            "currency_original": "VND", "is_duplicate": False,
        }])

    def test_valid(self):
        validate_clean(self._make_valid())

    def test_zero_salary_rejected(self):
        df = self._make_valid()
        df.at[0, "salary_min"] = 0.0
        with pytest.raises(ValueError, match="salary_min phải > 0"):
            validate_clean(df)

    def test_full_range_order_rejected(self):
        df = self._make_valid()
        df.at[0, "salary_min"] = 30.0
        df.at[0, "salary_max"] = 20.0
        with pytest.raises(ValueError, match="salary_min .* > salary_max"):
            validate_clean(df)

    def test_one_sided_requires_exactly_one_bound(self):
        df = self._make_valid()
        df.at[0, "salary_status"] = "one_sided"
        with pytest.raises(ValueError, match="đúng một"):
            validate_clean(df)

    def test_undisclosed_must_have_null_bounds(self):
        df = self._make_valid()
        df.at[0, "salary_status"] = "undisclosed"
        with pytest.raises(ValueError, match="undisclosed"):
            validate_clean(df)

    def test_undisclosed_nulls_ok(self):
        df = self._make_valid()
        df.at[0, "salary_status"] = "undisclosed"
        df.at[0, "salary_min"] = None
        df.at[0, "salary_max"] = None
        df["salary_min"] = df["salary_min"].astype("float64")
        df["salary_max"] = df["salary_max"].astype("float64")
        validate_clean(df)


class TestValidateSkills:
    def test_valid(self):
        validate_skills(pd.DataFrame([{"job_id": "j1", "python": 1, "sql": 0}]))

    def test_invalid_values(self):
        with pytest.raises(ValueError, match="không hợp lệ"):
            validate_skills(pd.DataFrame([{"job_id": "j1", "python": 2, "sql": 0}]))
