"""
Tests for data contract validation.
"""

import pandas as pd
import pytest
from src.contract import validate_parsed, validate_clean, validate_skills


class TestValidateParsed:
    def test_valid(self):
        """DataFrame hợp lệ không ném lỗi."""
        df = pd.DataFrame([{
            "job_id": "j1",
            "url": "https://example.com/1",
            "title": "Data Engineer",
            "company": "ABC",
            "jd_text": "Some JD text",
            "crawled_at": "2026-09-25T10:00:00+07:00",
        }])
        validate_parsed(df)  # should not raise

    def test_missing_required_column(self):
        df = pd.DataFrame([{
            "job_id": "j1",
            "url": "https://example.com/1",
            # missing title, company, jd_text, crawled_at
        }])
        with pytest.raises(ValueError, match="Thiếu cột bắt buộc"):
            validate_parsed(df)

    def test_null_in_required_column(self):
        df = pd.DataFrame([{
            "job_id": "j1",
            "url": "https://example.com/1",
            "title": None,  # null in required
            "company": "ABC",
            "jd_text": "text",
            "crawled_at": "2026-09-25T10:00:00+07:00",
        }])
        with pytest.raises(ValueError, match="null"):
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
            "job_id": "j1",
            "url": "https://example.com/1",
            "title": "Data Engineer",
            "company": "ABC",
            "jd_text": "text",
            "crawled_at": "2026-09-25T10:00:00+07:00",
            "salary_min": 15.0,
            "salary_max": 25.0,
            "salary_status": "full_range",
            "currency_original": "VND",
            "is_duplicate": False,
        }])

    def test_valid(self):
        df = self._make_valid()
        validate_clean(df)  # should not raise

    def test_invalid_salary_status(self):
        df = self._make_valid()
        df.at[0, "salary_status"] = "invalid_value"
        with pytest.raises(ValueError, match="không hợp lệ"):
            validate_clean(df)

    def test_missing_salary_status(self):
        df = self._make_valid()
        df = df.drop(columns=["salary_status"])
        with pytest.raises(ValueError, match="Thiếu cột bắt buộc"):
            validate_clean(df)

    def test_undisclosed_nulls_ok(self):
        """Lương undisclosed với min/max null là hợp lệ."""
        df = pd.DataFrame([{
            "job_id": "j1",
            "url": "u1",
            "title": "t1",
            "company": "c1",
            "jd_text": "jd",
            "crawled_at": "ct",
            "salary_min": None,
            "salary_max": None,
            "salary_status": "undisclosed",
            "currency_original": None,
            "is_duplicate": False,
        }])
        # Ensure float dtype
        df["salary_min"] = df["salary_min"].astype("float64")
        df["salary_max"] = df["salary_max"].astype("float64")
        validate_clean(df)  # should not raise


class TestValidateSkills:
    def test_valid(self):
        df = pd.DataFrame([
            {"job_id": "j1", "python": 1, "sql": 0},
            {"job_id": "j2", "python": 0, "sql": 1},
        ])
        validate_skills(df)  # should not raise

    def test_missing_job_id(self):
        df = pd.DataFrame([
            {"python": 1, "sql": 0},
        ])
        with pytest.raises(ValueError, match="job_id"):
            validate_skills(df)

    def test_invalid_values(self):
        df = pd.DataFrame([
            {"job_id": "j1", "python": 2, "sql": 0},  # 2 is invalid
        ])
        with pytest.raises(ValueError, match="không hợp lệ"):
            validate_skills(df)

    def test_no_skill_columns(self):
        df = pd.DataFrame([{"job_id": "j1"}])
        with pytest.raises(ValueError, match="Không có cột kỹ năng"):
            validate_skills(df)
