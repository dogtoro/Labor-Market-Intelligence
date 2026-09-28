# TASK BRIEF — Clustering + Phân lớp lương (Người 4)

## Mục tiêu
Nhóm tin tuyển dụng theo kỹ năng (hierarchical clustering), đánh giá purity. Nếu Mốc 2 cho phép: phân lớp dải lương bằng decision tree.

## Đầu vào
- `data/processed/skill_matrix.parquet` (từ Người 3)
- `data/processed/jobs_clean.parquet` (từ Người 2)
- `docs/DATA_CONTRACT.md`

## Đầu ra

| File | Đường dẫn | Mô tả |
|------|-----------|-------|
| Clustering script | `src/models/clustering.py` | Jaccard + linkage |
| Dendrogram | `reports/figures/dendrogram.png` | Hình cây phân cụm |
| Cluster labels | `data/processed/cluster_labels.csv` | job_id, cluster_id |
| Purity report | `reports/purity_report.md` | Bảng cluster × category, purity, F-measure |
| *(Nếu giữ)* Tree script | `src/models/classification.py` | Decision tree + CV |
| *(Nếu giữ)* Tree viz | `reports/figures/tree_viz.png` | Hình cây quyết định |
| *(Nếu giữ)* CV results | `reports/tree_cv_results.csv` | k-fold results |
| *(Nếu giữ)* Bias analysis | `reports/bias_analysis.md` | So sánh tin có/không lương |

## Hạn chót

| Việc | Hạn |
|------|-----|
| Prototype clustering trên dữ liệu mẫu | Tối 01/10 |
| Hierarchical clustering đầy đủ | Chiều 02/10 |
| Purity report | Sáng 03/10 |
| *(Nếu giữ)* Decision tree + bias analysis | Chiều 02/10 → sáng 03/10 |

## Definition of Done
- [ ] Dendrogram rõ ràng, thử ≥3 giá trị k, chọn k có lý do
- [ ] Purity tính đúng công thức bài giảng
- [ ] `purity_report.md` có bảng cluster × category + nhận xét
- [ ] *(Nếu giữ tree)* k-fold CV (k≥5), max_depth + min_samples_leaf tuned
- [ ] *(Nếu giữ tree)* Confusion matrix + bootstrap CI
- [ ] *(Nếu giữ tree)* `bias_analysis.md` so ≥3 chiều (kỹ năng, cấp bậc, địa điểm)

## Lệnh test
```bash
pytest tests/test_contract.py -v
```

## Ghi chú
- **Bắt đầu prototype ngay** trên `tests/fixtures/sample_jobs_clean.parquet`.
- Khoảng cách: **Jaccard** (1 − Jaccard similarity). Linkage: **Ward** hoặc **average**.
- Quyết định giữ/bỏ decision tree: **tối 01/10 (Mốc 2)**.
