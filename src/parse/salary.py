"""
Salary parsing — chuẩn hóa chuỗi lương thô từ TopCV.

Hỗ trợ:
  - "15 - 25 triệu"         → (15.0, 25.0, "full_range", "VND")
  - "Lên đến 2000 USD"      → (None, 2000*rate, "one_sided", "USD")
  - "Từ 10 triệu"           → (10.0, None, "one_sided", "VND")
  - "Thỏa thuận"            → (None, None, "undisclosed", None)
  - "Cạnh tranh"            → (None, None, "undisclosed", None)
  - None / ""               → (None, None, "undisclosed", None)
  - "1,500 - 2,500 USD"     → (1500*rate, 2500*rate, "full_range", "USD")
  - "15,000,000 - 25,000,000 VND" → (15.0, 25.0, "full_range", "VND")
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Tỷ giá mặc định — GHI RÕ TRONG ASSUMPTIONS.md
# Giả định: 1 USD ≈ 25,500 VND (tỷ giá tham khảo, cập nhật khi có dữ liệu thật)
DEFAULT_USD_TO_VND = 25_500
DEFAULT_JPY_TO_VND = 170


@dataclass
class SalaryResult:
    """Kết quả chuẩn hóa lương."""
    salary_min: float | None       # triệu VND/tháng
    salary_max: float | None       # triệu VND/tháng
    salary_status: str             # full_range | one_sided | undisclosed
    currency_original: str | None  # VND, USD, JPY, ...


# Patterns for undisclosed salary
_UNDISCLOSED_PATTERNS = [
    re.compile(r"thỏa\s*thuận", re.IGNORECASE),
    re.compile(r"th(oa|oả)\s*thu(ậ|a)n", re.IGNORECASE),
    re.compile(r"cạnh\s*tranh", re.IGNORECASE),
    re.compile(r"competitive", re.IGNORECASE),
    re.compile(r"negotiable", re.IGNORECASE),
]

# Extract numbers (with commas/dots as thousand separators)
_NUMBER_RE = re.compile(r"[\d]+(?:[.,]\d{3})*(?:\.\d+)?")


def _clean_number(s: str) -> float:
    """Parse a number string, handling thousand separators."""
    # Remove thousand separators (commas in "1,500" or dots in "1.500.000")
    cleaned = s.replace(",", "")
    # If multiple dots remain, they're thousand separators (e.g., "1.500.000")
    parts = cleaned.split(".")
    if len(parts) > 2:
        # All dots are thousand separators
        cleaned = "".join(parts)
    elif len(parts) == 2 and len(parts[1]) == 3:
        # Dot is a thousand separator (e.g., "1.500")
        cleaned = "".join(parts)
    return float(cleaned)


def _detect_currency(text: str) -> tuple[str, float]:
    """Detect currency and return (currency_code, conversion_to_million_vnd)."""
    text_upper = text.upper()
    if "USD" in text_upper or "$" in text_upper:
        return "USD", DEFAULT_USD_TO_VND / 1_000_000
    if "JPY" in text_upper or "¥" in text_upper:
        return "JPY", DEFAULT_JPY_TO_VND / 1_000_000
    # Default: VND
    return "VND", 1.0


def _to_million_vnd(value: float, currency: str, conversion_factor: float) -> float:
    """Convert a raw number to triệu VND/tháng."""
    if currency == "VND":
        if value > 1_000_000:
            # Raw VND (e.g., 15,000,000) → triệu
            return value / 1_000_000
        elif value > 1000:
            # Possibly thousand VND? Unlikely for salary, treat as raw
            return value / 1_000_000
        else:
            # Already in triệu (e.g., "15 triệu")
            return value
    else:
        # Foreign currency × conversion factor
        return value * conversion_factor


def parse_salary(raw: str | None) -> SalaryResult:
    """Parse a raw salary string into structured components.

    Returns:
        SalaryResult with salary_min/max in triệu VND/tháng.
    """
    if not raw or not raw.strip():
        return SalaryResult(None, None, "undisclosed", None)

    text = raw.strip()

    # Check undisclosed patterns
    for pattern in _UNDISCLOSED_PATTERNS:
        if pattern.search(text):
            return SalaryResult(None, None, "undisclosed", None)

    # Detect currency
    currency, conv = _detect_currency(text)

    # Check for "triệu" keyword — numbers are already in millions
    has_trieu = bool(re.search(r"tri[eệ]u", text, re.IGNORECASE))

    # Extract all numbers
    numbers = _NUMBER_RE.findall(text)
    if not numbers:
        return SalaryResult(None, None, "undisclosed", None)

    parsed_nums = [_clean_number(n) for n in numbers]

    # "Lên đến" / "Up to" / "Tối đa" → one_sided (max only)
    if re.search(r"lên\s*đến|up\s*to|tối\s*đa|<=", text, re.IGNORECASE):
        val = parsed_nums[0]
        if has_trieu:
            converted = val  # Already in triệu
        else:
            converted = _to_million_vnd(val, currency, conv)
        return SalaryResult(None, converted, "one_sided", currency)

    # "Từ" / "From" / "Tối thiểu" → one_sided (min only)
    if re.search(r"^từ\s|from\s|tối\s*thiểu|>=", text, re.IGNORECASE):
        val = parsed_nums[0]
        if has_trieu:
            converted = val
        else:
            converted = _to_million_vnd(val, currency, conv)
        return SalaryResult(converted, None, "one_sided", currency)

    # Two numbers → full_range
    if len(parsed_nums) >= 2:
        lo, hi = parsed_nums[0], parsed_nums[1]
        if has_trieu:
            lo_c, hi_c = lo, hi
        else:
            lo_c = _to_million_vnd(lo, currency, conv)
            hi_c = _to_million_vnd(hi, currency, conv)
        # Ensure lo <= hi
        if lo_c > hi_c:
            lo_c, hi_c = hi_c, lo_c
        return SalaryResult(lo_c, hi_c, "full_range", currency)

    # Single number, no directional keyword → treat as one_sided (roughly)
    val = parsed_nums[0]
    if has_trieu:
        converted = val
    else:
        converted = _to_million_vnd(val, currency, conv)
    return SalaryResult(converted, None, "one_sided", currency)
