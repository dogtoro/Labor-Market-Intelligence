# TASK BRIEF — Từ điển kỹ năng + Association Rules (Người 3)

## Mục tiêu
Xây từ điển kỹ năng IT/Data, trích kỹ năng từ JD text thành ma trận nhị phân, chạy Apriori tìm luật kết hợp.

## Đầu vào
- JD mẫu (đọc trực tiếp từ `data/raw/*.html` hoặc `tests/fixtures/`)
- `data/processed/jobs_clean.parquet` (từ Người 2, có từ tối 01/10)
- `docs/DATA_CONTRACT.md` (schema Tầng 4)

## Đầu ra

| File | Đường dẫn | Mô tả |
|------|-----------|-------|
| Từ điển | `src/skills/skill_dict.json` | ≥100 kỹ năng, mỗi kỹ năng có alias |
| Extractor | `src/skills/extractor.py` | Match từ điển → JD text → 0/1 |
| Ma trận kỹ năng | `data/processed/skill_matrix.parquet` | Schema Tầng 4 |
| Apriori rules | `data/processed/rules_train.csv` | itemset, support, confidence, lift |
| Đánh giá | `reports/rules_eval.md` | So sánh train vs test (chia theo ngày) |

## Hạn chót

| Việc | Hạn |
|------|-----|
| Từ điển v1 (~100 kỹ năng, dựa trên 20-30 JD mẫu) | Trưa 30/09 |
| Test Apriori trên dữ liệu mẫu (~200 tin) | Tối 01/10 |
| Ma trận kỹ năng đầy đủ | Sáng 02/10 |
| Apriori train + đánh giá test | Chiều 02/10 → sáng 03/10 |

## Definition of Done
- [ ] `skill_dict.json` có ≥100 kỹ năng, mỗi kỹ năng ≥1 alias
- [ ] `skill_matrix.parquet` qua `validate_skills()` không lỗi
- [ ] Mỗi tin có ≥1 kỹ năng; kỹ năng có <5 tin bị loại
- [ ] Apriori chạy với ≥3 giá trị min_support
- [ ] Rules có lift >1
- [ ] `rules_eval.md` so sánh ≥10 top rules train vs test; nhận xét overfit

## Lệnh test
```bash
pytest tests/test_skills.py tests/test_contract.py -v
```

## Ghi chú
- **Bắt đầu ngay ngày 29/09** bằng cách đọc JD mẫu trong `tests/fixtures/` để xây từ điển.
- Không dùng mô hình NLP. Chỉ dùng string matching với từ điển.
- Chia train/test theo `posted_date` (70% tin cũ hơn = train).
