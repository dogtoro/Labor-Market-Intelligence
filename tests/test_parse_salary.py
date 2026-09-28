"""
Tests for salary parsing — các dạng lương phổ biến trên TopCV.
"""

import pytest
from src.parse.salary import parse_salary, DEFAULT_USD_TO_VND


class TestSalaryFullRange:
    """Dải lương đầy đủ (có cận trên và cận dưới)."""

    def test_trieu_range(self):
        r = parse_salary("15 - 25 triệu")
        assert r.salary_status == "full_range"
        assert r.salary_min == pytest.approx(15.0)
        assert r.salary_max == pytest.approx(25.0)
        assert r.currency_original == "VND"

    def test_trieu_range_spacing(self):
        r = parse_salary("15-25 triệu")
        assert r.salary_status == "full_range"
        assert r.salary_min == pytest.approx(15.0)
        assert r.salary_max == pytest.approx(25.0)

    def test_usd_range_with_commas(self):
        r = parse_salary("1,500 - 2,500 USD")
        assert r.salary_status == "full_range"
        assert r.currency_original == "USD"
        expected_min = 1500 * DEFAULT_USD_TO_VND / 1_000_000
        expected_max = 2500 * DEFAULT_USD_TO_VND / 1_000_000
        assert r.salary_min == pytest.approx(expected_min)
        assert r.salary_max == pytest.approx(expected_max)

    def test_raw_vnd_range(self):
        r = parse_salary("15,000,000 - 25,000,000 VND")
        assert r.salary_status == "full_range"
        assert r.salary_min == pytest.approx(15.0)
        assert r.salary_max == pytest.approx(25.0)

    def test_min_max_order(self):
        """Luôn đảm bảo min <= max."""
        r = parse_salary("40 - 25 triệu")
        assert r.salary_min <= r.salary_max


class TestSalaryOneSided:
    """Chỉ có cận trên hoặc cận dưới."""

    def test_len_den(self):
        r = parse_salary("Lên đến 2000 USD")
        assert r.salary_status == "one_sided"
        assert r.salary_min is None
        assert r.salary_max is not None
        assert r.currency_original == "USD"
        expected = 2000 * DEFAULT_USD_TO_VND / 1_000_000
        assert r.salary_max == pytest.approx(expected)

    def test_tu_trieu(self):
        r = parse_salary("Từ 10 triệu")
        assert r.salary_status == "one_sided"
        assert r.salary_min == pytest.approx(10.0)
        assert r.salary_max is None
        assert r.currency_original == "VND"

    def test_up_to_english(self):
        r = parse_salary("Up to 3000 USD")
        assert r.salary_status == "one_sided"
        assert r.salary_min is None
        assert r.salary_max is not None


class TestSalaryUndisclosed:
    """Lương không công khai."""

    def test_thoa_thuan(self):
        r = parse_salary("Thỏa thuận")
        assert r.salary_status == "undisclosed"
        assert r.salary_min is None
        assert r.salary_max is None

    def test_canh_tranh(self):
        r = parse_salary("Cạnh tranh")
        assert r.salary_status == "undisclosed"
        assert r.salary_min is None
        assert r.salary_max is None

    def test_none(self):
        r = parse_salary(None)
        assert r.salary_status == "undisclosed"

    def test_empty_string(self):
        r = parse_salary("")
        assert r.salary_status == "undisclosed"

    def test_whitespace(self):
        r = parse_salary("   ")
        assert r.salary_status == "undisclosed"

    def test_negotiable(self):
        r = parse_salary("Negotiable")
        assert r.salary_status == "undisclosed"
