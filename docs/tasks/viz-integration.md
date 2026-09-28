# TASK BRIEF — EDA + Trực quan + Slide + Demo (Người 5)

## Mục tiêu
Tạo mọi thứ "người xem thấy": biểu đồ EDA, notebook tích hợp, slide trình bày, demo tương tác.

## Đầu vào
- `data/processed/jobs_clean.parquet` (từ Người 2)
- `data/processed/skill_matrix.parquet` (từ Người 3)
- Output model từ Người 3 + 4 (rules, clusters, tree)
- `tests/fixtures/` (dữ liệu mẫu để bắt đầu sớm)

## Đầu ra

| File | Đường dẫn | Mô tả |
|------|-----------|-------|
| EDA draft | `notebooks/eda_draft.ipynb` | ≥5 biểu đồ trên dữ liệu mẫu |
| EDA đầy đủ | `notebooks/eda_full.ipynb` | ≥10 biểu đồ chất lượng trình bày |
| Final notebook | `notebooks/final_notebook.ipynb` | EDA + model, chạy end-to-end |
| Figures | `reports/figures/*.png` | Tất cả hình xuất từ code |
| Slide | `reports/slides.pptx` hoặc Google Slides | ≤15 slide |
| Demo | Notebook hoặc Streamlit | Có ≥1 tương tác |

## Hạn chót

| Việc | Hạn |
|------|-----|
| EDA draft trên dữ liệu mẫu | Tối 30/09 |
| EDA đầy đủ | Chiều 02/10 |
| Tích hợp notebook | Tối 03/10 |
| Slide + demo | Tối 04/10 (Mốc 3) |

## Definition of Done
- [ ] `eda_draft.ipynb`: ≥5 biểu đồ (phân phối lương, top kỹ năng, top địa điểm, top cấp bậc, timeline)
- [ ] `eda_full.ipynb`: ≥10 biểu đồ, có title, label trục, chú thích, font ≥12pt
- [ ] `final_notebook.ipynb`: Restart & Run All thành công
- [ ] Slide ≤15 slide: bìa, pipeline, EDA (≥3 hình), model (≥2 hình), kết luận, hạn chế
- [ ] Demo chạy ≤2 phút setup, có ≥1 tương tác (filter/dropdown)
- [ ] **Mọi con số trong slide sinh ra từ code** (không gõ tay)

## Lệnh test
```bash
pytest tests/test_contract.py -v
# Kiểm tra notebook:
jupyter nbconvert --execute notebooks/final_notebook.ipynb --to html
```

## Ghi chú
- **Bắt đầu ngay ngày 30/09** trên `tests/fixtures/sample_jobs_clean.parquet`.
- Ngày 29/09 rảnh → hỗ trợ Người 3 xây từ điển kỹ năng.
- Ngày 01/10 nhàn → hỗ trợ Người 2 vẽ phễu chất lượng.
