# TASK BRIEF — Parser + Làm sạch (Người 2)

## Mục tiêu
Biến HTML thô thành bảng có cấu trúc, loại tin trùng, chuẩn hóa lương về triệu VND/tháng.

## Đầu vào
- `data/raw/*.html` (từ Người 1, có mẫu thử tối 29/09, đầy đủ trưa 30/09)
- `docs/DATA_CONTRACT.md` (schema Tầng 2 + 3)

## Đầu ra

| File | Đường dẫn | Mô tả |
|------|-----------|-------|
| Parser script | `src/parse/parser.py` | HTML → 12 cột |
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

## Lệnh test
```bash
pytest tests/test_parse_salary.py tests/test_dedup.py tests/test_contract.py -v
```
