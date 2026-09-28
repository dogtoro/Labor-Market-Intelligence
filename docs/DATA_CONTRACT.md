# DATA CONTRACT — Schema các tầng dữ liệu

> **Quy ước:** Sau khi dữ liệu freeze (tối 01/10/2026), KHÔNG ai được thay đổi schema
> mà không ghi vào `DECISIONS.md` và được ≥2 người đồng ý.

---

## Tầng 1: Raw (HTML thô)

| Thuộc tính | Giá trị |
|---|---|
| Vị trí | `data/raw/{job_id}.html` |
| Format | HTML text, UTF-8 |
| Naming | `job_id` lấy từ URL hoặc slug của tin tuyển dụng |
| Git | **KHÔNG commit** — chỉ lưu local + backup Google Drive |

---

## Tầng 2: Parsed — `data/interim/jobs_parsed.parquet`

| Cột | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| `job_id` | `str` | ✅ | ID duy nhất, lấy từ URL |
| `url` | `str` | ✅ | URL đầy đủ của tin |
| `title` | `str` | ✅ | Tiêu đề vị trí tuyển dụng |
| `company` | `str` | ✅ | Tên công ty |
| `level` | `str` | ❌ | Cấp bậc (Intern, Junior, Senior, Manager, …) |
| `location` | `str` | ❌ | Địa điểm làm việc |
| `posted_date` | `str` | ❌ | Ngày đăng, ISO 8601 (YYYY-MM-DD) |
| `category` | `str` | ❌ | Danh mục nghề trên TopCV (nếu có) |
| `salary_raw` | `str` | ❌ | Chuỗi lương gốc, giữ nguyên từ HTML |
| `jd_text` | `str` | ✅ | Nội dung JD đã strip HTML tags |
| `crawled_at` | `str` | ✅ | Thời điểm crawl, ISO 8601 với timezone UTC+7 |

**Primary key:** `job_id` (unique, không null).

---

## Tầng 3: Clean — `data/processed/jobs_clean.parquet`

Giữ nguyên tất cả cột Tầng 2, thêm:

| Cột | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| `salary_min` | `float64` | ❌ | Cận dưới lương, đơn vị: **triệu VND/tháng**. Null nếu không có |
| `salary_max` | `float64` | ❌ | Cận trên lương, đơn vị: **triệu VND/tháng**. Null nếu không có |
| `salary_status` | `str` | ✅ | Enum: `full_range` \| `one_sided` \| `undisclosed` |
| `currency_original` | `str` | ❌ | Đơn vị tiền gốc trước quy đổi: `VND`, `USD`, `JPY`, … |
| `is_duplicate` | `bool` | ✅ | `True` = bản trùng đã bị loại. Bản giữ lại = `False` |

### Enum `salary_status`

| Giá trị | Ý nghĩa | Ví dụ salary_raw |
|---------|---------|-------------------|
| `full_range` | Có cả cận trên và cận dưới | "15 - 25 triệu" |
| `one_sided` | Chỉ có một cận | "Lên đến 2000 USD", "Từ 10 triệu" |
| `undisclosed` | Không công khai | "Thỏa thuận", "Cạnh tranh", null |

### Quy đổi lương

- Đơn vị cuối cùng: **triệu VND/tháng**.
- Tỷ giá USD→VND: ghi rõ tỷ giá + ngày tra cứu trong `ASSUMPTIONS.md`.
- Giả định gross/net: ghi rõ trong `ASSUMPTIONS.md`.

---

## Tầng 4: Skills Matrix — `data/processed/skill_matrix.parquet`

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `job_id` | `str` | Khớp với `job_id` ở Tầng 3 |
| `<skill_name>` | `int8` | `1` nếu JD chứa kỹ năng, `0` nếu không. Tên cột = tên chuẩn (lowercase, không dấu) |

- Từ điển kỹ năng: `src/skills/skill_dict.json`.
- Mỗi kỹ năng có bảng alias (ví dụ: `"power_bi": ["Power BI", "PowerBI", "power bi"]`).
- Chỉ giữ kỹ năng xuất hiện ≥ 5 tin.

---

## Validation

Import và gọi hàm validate trong code:

```python
from src.contract import validate_parsed, validate_clean, validate_skills

validate_parsed(df)   # ném ValueError nếu sai schema
validate_clean(df)
validate_skills(df)
```

Test: `pytest tests/test_contract.py -v`
