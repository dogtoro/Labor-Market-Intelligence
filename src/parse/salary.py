"""Salary parsing and normalization for ITviec salary strings.

All numeric outputs are in million VND/month.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_USD_TO_VND = 25_780
DEFAULT_JPY_TO_VND = 170
DEFAULT_WORKING_DAYS_PER_MONTH = 20


@dataclass
class SalaryResult:
    salary_min: float | None
    salary_max: float | None
    salary_status: str
    currency_original: str | None


_UNDISCLOSED_PATTERNS = [
    re.compile(r"thỏa\s*thuận", re.IGNORECASE),
    re.compile(r"th(oa|oả)\s*thu(ậ|a)n", re.IGNORECASE),
    re.compile(r"cạnh\s*tranh", re.IGNORECASE),
    re.compile(r"competitive", re.IGNORECASE),
    re.compile(r"negotiable", re.IGNORECASE),
]

_NUMBER_RE = re.compile(r"[\d]+(?:[.,]\d{3})*(?:\.\d+)?")
_DAILY_RE = re.compile(
    r"(?:/\s*(?:ng[aà]y|day)\b|per\s+day\b|mỗi\s+ng[aà]y\b|h[aằ]ng\s+ng[aà]y\b)",
    re.IGNORECASE,
)


def _clean_number(s: str) -> float:
    cleaned = s.replace(",", "")
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts)
    elif len(parts) == 2 and len(parts[1]) == 3:
        cleaned = "".join(parts)
    return float(cleaned)


def _detect_currency(text: str) -> tuple[str, float]:
    text_upper = text.upper()
    if "USD" in text_upper or "$" in text_upper:
        return "USD", DEFAULT_USD_TO_VND / 1_000_000
    if "JPY" in text_upper or "¥" in text_upper:
        return "JPY", DEFAULT_JPY_TO_VND / 1_000_000
    return "VND", 1.0


def _period_multiplier(text: str) -> float:
    """Convert a pay-period value to monthly.

    ITviec occasionally contains daily salary strings such as ``Từ $100/ngày``.
    We use 20 working days/month; this assumption must be documented in
    ASSUMPTIONS.md.
    """
    if _DAILY_RE.search(text):
        return float(DEFAULT_WORKING_DAYS_PER_MONTH)
    return 1.0


def _to_million_vnd(value: float, currency: str, conversion_factor: float) -> float:
    if currency == "VND":
        if value > 1_000_000:
            return value / 1_000_000
        if value > 1000:
            return value / 1_000_000
        return value
    return value * conversion_factor


def _convert_value(
    value: float,
    *,
    currency: str,
    conversion_factor: float,
    has_trieu: bool,
    period_multiplier: float,
) -> float | None:
    if has_trieu:
        converted = value
    else:
        converted = _to_million_vnd(value, currency, conversion_factor)
    converted *= period_multiplier
    if converted <= 0:
        return None
    return converted


def parse_salary(raw: str | None) -> SalaryResult:
    if not raw or not raw.strip():
        return SalaryResult(None, None, "undisclosed", None)

    text = raw.strip()

    for pattern in _UNDISCLOSED_PATTERNS:
        if pattern.search(text):
            return SalaryResult(None, None, "undisclosed", None)

    currency, conv = _detect_currency(text)
    has_trieu = bool(re.search(r"tri[eệ]u", text, re.IGNORECASE))
    period_multiplier = _period_multiplier(text)

    numbers = _NUMBER_RE.findall(text)
    if not numbers:
        return SalaryResult(None, None, "undisclosed", None)
    parsed_nums = [_clean_number(n) for n in numbers]

    def cv(v: float) -> float | None:
        return _convert_value(
            v,
            currency=currency,
            conversion_factor=conv,
            has_trieu=has_trieu,
            period_multiplier=period_multiplier,
        )

    if re.search(r"lên\s*đến|up\s*to|tối\s*đa|<=", text, re.IGNORECASE):
        value = cv(parsed_nums[0])
        if value is None:
            return SalaryResult(None, None, "undisclosed", None)
        return SalaryResult(None, value, "one_sided", currency)

    if re.search(r"^từ\s|from\s|tối\s*thiểu|>=", text, re.IGNORECASE):
        value = cv(parsed_nums[0])
        if value is None:
            return SalaryResult(None, None, "undisclosed", None)
        return SalaryResult(value, None, "one_sided", currency)

    if len(parsed_nums) >= 2:
        lo_c, hi_c = cv(parsed_nums[0]), cv(parsed_nums[1])

        if lo_c is None and hi_c is None:
            return SalaryResult(None, None, "undisclosed", None)
        if lo_c is None:
            return SalaryResult(None, hi_c, "one_sided", currency)
        if hi_c is None:
            return SalaryResult(lo_c, None, "one_sided", currency)

        if lo_c > hi_c:
            lo_c, hi_c = hi_c, lo_c
        return SalaryResult(lo_c, hi_c, "full_range", currency)

    value = cv(parsed_nums[0])
    if value is None:
        return SalaryResult(None, None, "undisclosed", None)
    return SalaryResult(value, None, "one_sided", currency)
