# Báo cáo phân lớp lương (Decision Tree)

Sinh bởi `src/models/classification.py`. Chỉ dùng tin **có công bố lương** — xem `bias_analysis.md` về phạm vi áp dụng.

## Dữ liệu

- **Số tin:** 172 (left join `skill_matrix`, tin không bắt được kỹ năng nào điền 0)
- **Nhãn (tertile `salary_mid`, triệu VND/tháng):** Low < 32.2 ≤ Mid < 50.0 ≤ High
- **Số tin mỗi lớp:** Low 60 / Mid 55 / High 57
- **Feature:** 80 = 70 kỹ năng (xuất hiện ≥ 5 lần) + 6 cấp bậc (one-hot, có `Unknown`) + 4 địa điểm (multi-hot)

## Đánh giá (nested CV, dự đoán out-of-fold)

Vòng ngoài 5 fold đánh giá, vòng trong 3 fold chọn `max_depth ∈ {3,4,5,6}`, `min_samples_leaf ∈ {5,10,15}`.

- **Accuracy:** 0.5291 (95% bootstrap CI: 0.4535 – 0.6047, 1000 lần)
- **Baseline** (luôn đoán lớp đông nhất): 0.3488
- **Macro-F1:** 0.5060

### Confusion matrix (out-of-fold)

|  | Dự đoán: Low | Dự đoán: Mid | Dự đoán: High |
|---|---|---|---|
| Thật: Low | 43 | 9 | 8 |
| Thật: Mid | 20 | 13 | 22 |
| Thật: High | 7 | 15 | 35 |

### Tham số chọn ở từng fold

| Fold | max_depth | min_samples_leaf | inner_cv_accuracy | fold_accuracy |
|---|---|---|---|---|
| 1 | 3 | 5 | 0.4957 | 0.4571 |
| 2 | 4 | 10 | 0.5248 | 0.4286 |
| 3 | 3 | 5 | 0.4928 | 0.5588 |
| 4 | 4 | 5 | 0.4493 | 0.5882 |
| 5 | 4 | 5 | 0.4783 | 0.6176 |

## Mô hình cuối

- **Tham số:** max_depth=3, min_samples_leaf=5 — bộ được vòng trong chọn nhiều nhất (2/5 fold); hoà thì chọn cây đơn giản hơn (nông hơn).
- **Cây:** độ sâu 3, 5 lá. Hình: `reports/figures/tree_viz.png`.
- **Model:** `models/tree_model.pkl` (sklearn 1.9.1; metadata ở `models/tree_model_meta.json`).

### Feature importance (> 0)

| Feature | Importance |
|---|---|
| lvl_Junior | 0.455 |
| lvl_Middle | 0.224 |
| lvl_Unknown | 0.202 |
| cpp | 0.119 |

## Nhận xét

- Accuracy out-of-fold 52.9%, cận dưới CI 45.3% vẫn cao hơn baseline 34.9% → mô hình học được tín hiệu thật.
- Cấp bậc (suy từ tiêu đề) là feature quan trọng nhất; việc **không suy được** cấp bậc (`lvl_Unknown`) cũng mang thông tin.
- Recall từng lớp: Low 43/60 (72%), Mid 13/55 (24%), High 35/57 (61%) — lớp giữa khó tách nhất, thường bị nhầm sang hai lớp bên cạnh.
- Mẫu nhỏ (172 tin) nên CI rộng; kết luận chỉ áp dụng cho tin có công bố lương (25% tổng số tin, phần lớn ghi USD).
