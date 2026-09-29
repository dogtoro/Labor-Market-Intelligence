# TASK BRIEF — Parser + Làm sạch (Người 2)

## Mục tiêu
Biến HTML thô thành bảng có cấu trúc, loại tin trùng, chuẩn hóa lương về triệu VND/tháng.

## Đầu vào
- `data/raw/*.html` (từ Người 1, có mẫu thử tối 29/09, đầy đủ trưa 30/09)
- `docs/DATA_CONTRACT.md` (schema Tầng 2 + 3)

## Đầu ra

| File | Đường dẫn | Mô tả |
|------|-----------|-------|
| Parser script | `src/parse/parser.py` | HTML → 11 cột (`docs/DATA_CONTRACT.md` Tầng 2) |
| Parsed data | `data/interim/jobs_parsed.parquet` | Schema Tầng 2 |
| Dedup script | `src/clean/dedup.py` | Logic loại tin trùng |
| Salary script | `src/parse/salary.py` | Chuẩn hóa lương |
| Clean data | `data/processed/jobs_clean.parquet` | Schema Tầng 3 |
| Dedup report | `reports/dedup_report.md` | Số tin loại, tiêu chí |
| Data funnel | `reports/figures/data_funnel.png` | Phễu chất lượng dữ liệu |

## Hạn chót

| Việc | Hạn |
|------|-----|
| Parser v1 trên HTML mẫu | Trưa 30/09 |
| Parse toàn bộ | Chiều 30/09 |
| Dedup | Sáng 01/10 |
| Chuẩn hóa lương + giao `jobs_clean.parquet` | Tối 01/10 (Mốc 2) |

## Definition of Done
- [ ] `jobs_parsed.parquet` qua `validate_parsed()` không lỗi
- [ ] `jobs_clean.parquet` qua `validate_clean()` không lỗi
- [ ] Parse thành công ≥90% HTML (phần lỗi được log vào `reports/parse_errors.csv`)
- [ ] Dedup report ghi rõ logic + số tin loại
- [ ] Lương quy về triệu VND/tháng, tỷ giá + giả định ghi trong `ASSUMPTIONS.md`
- [ ] `data_funnel.png` có ≥4 tầng với số liệu

## Ghi chú từ pilot ITviec (29/09, 20 tin — `docs/tos_review.md` mục 10)
Mẫu HTML: `data/raw/*.html` (20 file, xin Trưởng nhóm/Người 1 qua Drive — không có trong git).

| Cột | Lấy ở đâu |
|-----|-----------|
| `job_id` | Tên file / toàn bộ slug URL (KHÔNG dùng 4 số cuối — không unique) |
| `title`, `company` | JSON-LD `JobPosting` (`title`, `hiringOrganization.name`) hoặc `<title>` "… at <Công ty> \| ITviec" |
| `salary_raw` | JSON-LD `baseSalary.value.value` — số thật chỉ có ở đây (giao diện luôn hiện "Sign in to view salary"). `"You'll love it"` = không công khai |
| `posted_date` | JSON-LD `datePosted` (YYYY-MM-DD). KHÔNG dùng "Posted X ago" — lệch vì tin được đẩy lại |
| `location` | JSON-LD `jobLocation[].address.addressRegion` (có thể nhiều địa điểm) |
| `category` | Khối "Job Expertise:" trên trang |
| `level` | Không có trường riêng → suy từ `title` (A17) |
| `jd_text` | Khối "Job description" + "Your skills and experience" (JD lẫn tiếng Việt/Anh) |

Lưu ý:
- Mỗi trang có khối "More jobs for you" chứa tin khác (tên, lương, skill của tin khác) → chỉ parse khối chính, đừng quét toàn trang.
- `salary.py` hiện đã trả `undisclosed` cho `"You'll love it"` (nhờ nhánh "không có số"), và parse đúng "1,000 - 2,000 USD" → 25.5–51.0 triệu. Nên thêm 2 chuỗi này vào `tests/test_parse_salary.py`. Pilot: 5/5 tin có lương là USD/tháng dạng khoảng.
- Tin có lương chỉ dùng số liệu tổng hợp trong báo cáo (DECISIONS 29/09).

## Lệnh test
```bash
pytest tests/test_parse_salary.py tests/test_dedup.py tests/test_contract.py -v
```
