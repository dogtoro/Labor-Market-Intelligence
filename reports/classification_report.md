# Báo cáo phân lớp lương (Decision Tree)

Sinh bởi `src/models/classification.py`. Chỉ dùng tin **có công bố lương** — xem `bias_analysis.md` về phạm vi áp dụng.

## Dữ liệu

- **Số tin:** 172 (left join `skill_matrix`, tin không bắt được kỹ năng nào điền 0)
- **Nhãn (tertile `salary_mid`, triệu VND/tháng):** Low < 32.2 ≤ Mid < 50.0 ≤ High
- **Số tin mỗi lớp:** Low 60 / Mid 55 / High 57
- **Feature:** 81 = 71 kỹ năng (xuất hiện ≥ 5 lần) + 6 cấp bậc (one-hot, có `Unknown`) + 4 địa điểm (multi-hot)

## Đánh giá (nested CV, dự đoán out-of-fold)

Vòng ngoài 5 fold đánh giá, vòng trong 3 fold chọn `max_depth ∈ {3,4,5,6}`, `min_samples_leaf ∈ {5,10,15}`.

- **Accuracy:** 0.5174 (95% bootstrap CI: 0.4419 – 0.5930, 1000 lần)
- **Baseline** (luôn đoán lớp đông nhất): 0.3488
- **Macro-F1:** 0.5202

### Confusion matrix (out-of-fold)

|  | Dự đoán: Low | Dự đoán: Mid | Dự đoán: High |
|---|---|---|---|
| Thật: Low | 30 | 16 | 14 |
| Thật: Mid | 8 | 26 | 21 |
| Thật: High | 4 | 20 | 33 |

### Tham số chọn ở từng fold

| Fold | max_depth | min_samples_leaf | inner_cv_accuracy | fold_accuracy |
|---|---|---|---|---|
| 1 | 3 | 5 | 0.4957 | 0.4571 |
| 2 | 6 | 5 | 0.5327 | 0.4571 |
| 3 | 4 | 10 | 0.5072 | 0.4118 |
| 4 | 3 | 10 | 0.4348 | 0.5588 |
| 5 | 6 | 5 | 0.4783 | 0.7059 |

## Mô hình cuối

- **Tham số:** max_depth=6, min_samples_leaf=5 — bộ được vòng trong chọn nhiều nhất (2/5 fold); hoà thì chọn cây đơn giản hơn (nông hơn).
- **Cây:** độ sâu 6, 15 lá. Hình: `reports/figures/tree_viz.png`.
- **Model:** `models/tree_model.pkl` (sklearn 1.9.1; metadata ở `models/tree_model_meta.json`).

### Feature importance (> 0)

| Feature | Importance |
|---|---|
| lvl_Intern/Junior | 0.237 |
| lvl_Middle | 0.117 |
| lvl_Unknown | 0.105 |
| lvl_Senior | 0.077 |
| loc_hn | 0.065 |
| docker | 0.064 |
| go | 0.062 |
| react | 0.057 |
| kubernetes | 0.057 |
| api | 0.055 |
| git | 0.054 |
| communication | 0.021 |
| aws | 0.021 |
| redis | 0.009 |

### Nhóm cấp bậc `Intern/Junior`

Intern, Fresher và Junior được gộp thành 1 nhóm (`LEVEL_GROUPS`) vì Junior thật rất ít. Trong các tin có lương, thành phần nhóm này:

| Level gốc | Số tin | Trung vị (triệu) | Thấp nhất | Cao nhất |
|---|---|---|---|---|
| Intern | 14 | 4.1 | 2.3 | 9.0 |
| Fresher | 1 | 3.6 | 3.6 | 3.6 |
| Junior | 2 | 15.7 | 12.0 | 19.3 |

→ **14/17 tin là thực tập sinh**; con số "lương" của họ là **phụ cấp thực tập**, không phải lương. Vì vậy nhánh `lvl_Intern/Junior` của cây (toàn bộ dự đoán Low) phản ánh "thực tập sinh có thu nhập thấp" — **không** được diễn giải thành "Junior lương thấp".

### Phân bố lớp lương theo cấp bậc

| Cấp bậc | Số tin | Low | Mid | High | Lớp đông nhất |
|---|---|---|---|---|---|
| Intern/Junior | 17 | 100% | 0% | 0% | Low |
| Lead | 12 | 0% | 25% | 75% | High |
| Manager | 18 | 6% | 17% | 78% | High |
| Middle | 11 | 73% | 18% | 9% | Low |
| Senior | 52 | 15% | 44% | 40% | Mid |
| Unknown | 62 | 42% | 39% | 19% | Low |

## Nhận xét

- Accuracy out-of-fold 51.7%, cận dưới CI 44.2% vẫn cao hơn baseline 34.9% → mô hình học được tín hiệu thật.
- Cấp bậc (suy từ tiêu đề) là nhóm feature quan trọng nhất. Tách quan trọng nhất là `lvl_Intern/Junior`, nhưng nhóm này chủ yếu là thực tập sinh (phụ cấp) nên kết luận gần như hiển nhiên. Các cấp bậc còn lại (lớp đông nhất, xem bảng trên): Lead (75% High), Manager (78% High), Middle (73% Low), Senior (44% Mid), Unknown (42% Low).
- Cây có 15 lá, trong đó 10 lá có < 10 tin; các nhánh tách theo kỹ năng (`docker`, `go`, `react`, `kubernetes`, `api`, `git`, `communication`, `aws`, `redis`) dựa trên rất ít tin nên **không** nên diễn giải thành "kỹ năng X → lương Y".
- **Hạn chế:** phụ cấp thực tập nằm chung với lương trong dữ liệu (không tách được ở bước làm sạch); phương án loại tin thực tập khỏi mô hình lương sẽ đổi N = 172 và tertile đã chốt ở Mốc 2 nên không áp dụng.
- Recall từng lớp: Low 30/60 (50%), Mid 26/55 (47%), High 33/57 (58%) — lớp giữa khó tách nhất, thường bị nhầm sang hai lớp bên cạnh.
- Mẫu nhỏ (172 tin) nên CI rộng; kết luận chỉ áp dụng cho tin có công bố lương (25% tổng số tin, phần lớn ghi USD).
