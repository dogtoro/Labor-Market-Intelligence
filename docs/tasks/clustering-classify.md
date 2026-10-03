# TASK BRIEF — Clustering + Phân lớp lương (Người 4)

## Mục tiêu
Nhóm tin tuyển dụng theo kỹ năng (hierarchical clustering), đánh giá purity. Phân lớp dải lương bằng decision tree — **Mốc 2 (01/10) đã chốt GIỮ** (`docs/DECISIONS.md`).

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
| Tree script | `src/models/classification.py` | Decision tree + CV |
| Tree viz | `reports/figures/tree_viz.png` | Hình cây quyết định |
| CV results | `reports/tree_cv_results.csv` | k-fold results |
| Bias analysis | `reports/bias_analysis.md` | So sánh tin có/không lương |

## Hạn chót

| Việc | Hạn |
|------|-----|
| Prototype clustering trên dữ liệu mẫu | Tối 01/10 |
| Hierarchical clustering đầy đủ | Chiều 02/10 |
| Purity report | Sáng 03/10 |
| Decision tree + bias analysis | Chiều 02/10 → sáng 03/10 — **xong 03/10, merge 04/10** |

## Definition of Done
- [x] Dendrogram rõ ràng, thử ≥3 giá trị k, chọn k có lý do (k = 4–8, chọn theo silhouette + cụm nhỏ nhất ≥ 15)
- [x] Purity tính đúng công thức bài giảng (bảng gộp nhóm nghề A16 đã review 04/10)
- [x] `purity_report.md` có bảng cluster × category + nhận xét
- [x] k-fold CV (k≥5), max_depth + min_samples_leaf tuned (nested CV 5×3)
- [x] Confusion matrix + bootstrap CI
- [x] `bias_analysis.md` so ≥3 chiều (kỹ năng, cấp bậc, địa điểm)

## Lệnh test
```bash
pytest tests/test_contract.py -v
```

## Ghi chú
- **Bắt đầu prototype ngay** trên `tests/fixtures/sample_jobs_clean.parquet`.
- Khoảng cách: **Jaccard** (1 − Jaccard similarity). Linkage: **weighted** (Ward không hợp lệ với Jaccard, average bị chaining — DECISIONS 03/10).
- Quyết định giữ/bỏ decision tree: **Mốc 2 (01/10) — GIỮ.** Các mục Decision Tree ở trên đều phải làm.
- **Nhãn lương (theo DECISIONS Mốc 2):**
  - Chỉ dùng tin `salary_status != "undisclosed"` (172/688 tin).
  - `salary_mid` = trung bình `salary_min`, `salary_max` với `full_range`; = cận duy nhất với `one_sided` (20 tin).
  - Chia 3 lớp Low / Mid / High bằng tertile (`pd.qcut(salary_mid, 3)`), **tính ranh giới trong code**, không gõ tay
    (trên dữ liệu 29/09: ≈ 32,2 / 50,0 triệu → 60 / 55 / 57 mẫu). Ghi ranh giới ra file kết quả để slide dùng lại.
  - KHÔNG dùng ngưỡng cố định 15/30 triệu (chỉ cho 18 / 29 / 125 mẫu).
  - Phần hạn chế: 20 tin `one_sided` dùng 1 cận; tin có lương chỉ chiếm 25% → `bias_analysis.md` so nhóm có/không lương.
