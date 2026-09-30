"""Tests for salary parsing, including real ITviec edge cases."""

import pytest

from src.parse.salary import (
    DEFAULT_USD_TO_VND,
    DEFAULT_WORKING_DAYS_PER_MONTH,
    parse_salary,
)


class TestSalaryFullRange:
    def test_trieu_range(self):
        r = parse_salary("15 - 25 triệu")
        assert r.salary_status == "full_range"
        assert r.salary_min == pytest.approx(15.0)
        assert r.salary_max == pytest.approx(25.0)
        assert r.currency_original == "VND"

    def test_usd_range_with_commas(self):
        r = parse_salary("1,500 - 2,500 USD")
        assert r.salary_status == "full_range"
        assert r.currency_original == "USD"
        assert r.salary_min == pytest.approx(1500 * DEFAULT_USD_TO_VND / 1_000_000)
        assert r.salary_max == pytest.approx(2500 * DEFAULT_USD_TO_VND / 1_000_000)

    def test_itviec_usd_range(self):
        r = parse_salary("1,000 - 2,000 USD")
        assert r.salary_min == pytest.approx(25.78)
        assert r.salary_max == pytest.approx(51.56)

    def test_raw_vnd_range(self):
        r = parse_salary("30,000,000 - 50,000,000đ")
        assert r.salary_status == "full_range"
        assert r.salary_min == pytest.approx(30.0)
        assert r.salary_max == pytest.approx(50.0)

    def test_min_max_order(self):
        r = parse_salary("40 - 25 triệu")
        assert r.salary_min <= r.salary_max


class TestSalaryOneSided:
    def test_up_to_35m(self):
        r = parse_salary("Up To 35M")
        assert r.salary_status == "one_sided"
        assert r.salary_min is None
        assert r.salary_max == pytest.approx(35.0)

    def test_tu_trieu(self):
        r = parse_salary("Từ 10 triệu")
        assert r.salary_status == "one_sided"
        assert r.salary_min == pytest.approx(10.0)
        assert r.salary_max is None

    def test_daily_usd_converted_to_month(self):
        r = parse_salary("Từ $100/ngày")
        expected = 100 * DEFAULT_USD_TO_VND / 1_000_000 * DEFAULT_WORKING_DAYS_PER_MONTH
        assert r.salary_status == "one_sided"
        assert r.salary_min == pytest.approx(expected)
        assert r.salary_max is None
        assert expected == pytest.approx(51.56)

    def test_zero_lower_bound_becomes_one_sided(self):
        r = parse_salary("0 - 200 USD")
        assert r.salary_status == "one_sided"
        assert r.salary_min is None
        assert r.salary_max == pytest.approx(200 * DEFAULT_USD_TO_VND / 1_000_000)


class TestSalaryUndisclosed:
    @pytest.mark.parametrize("raw", ["Thỏa thuận", "Cạnh tranh", "Negotiable", "You'll love it", None, "", "   "])
    def test_undisclosed_values(self, raw):
        r = parse_salary(raw)
        assert r.salary_status == "undisclosed"
        assert r.salary_min is None
        assert r.salary_max is None

    def test_zero_only_is_undisclosed(self):
        r = parse_salary("0 USD")
        assert r.salary_status == "undisclosed"
        assert r.salary_min is None
        assert r.salary_max is None
