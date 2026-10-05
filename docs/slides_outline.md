# Dàn ý slide thuyết trình (sáng 06/10)

> Dành cho Người 5 + Người 3 khi dựng slide, và cả nhóm khi tập.
> Bám 7 mục giảng viên yêu cầu. **Mọi con số lấy từ code** (CLAUDE.md mục 4): cột "Nguồn" ghi khoá trong
> `reports/key_numbers.json` (sinh bởi `notebooks/final_notebook.ipynb`) hoặc file báo cáo. Giá trị trong ngoặc
> là giá trị hiện tại để tiện đối chiếu — khi dựng slide, chép từ nguồn, không chép từ file này.
> Tiêu đề slide bằng tiếng Anh cho khớp với các hình.

**Ký hiệu:** ⭐ = chỗ cần nhấn mạnh khi nói · ⚠️ = điều cần tránh · 🗣️ = gợi ý câu nói

---

## Nguyên tắc trình bày chung

- **Kể chuyện trước, kỹ thuật sau:** mở bằng vấn đề của người học IT → câu hỏi → dữ liệu → mô hình → kết quả.
- **Mỗi slide phân tích = 1 hình + tối đa 3 gạch đầu dòng**; mỗi gạch đầu dòng **in đậm phần kết luận** ở đầu câu, phần sau giải thích.
- **Số lớn, nổi bật** cho các con số chính của dữ liệu (688, 172, 100…).
- **Một sơ đồ pipeline duy nhất**, tô màu theo giai đoạn; dùng lại làm "bản đồ" khi chuyển phần.
- **Giao diện thống nhất:** cùng khung, màu, font; số trang dạng "x / 16"; slide mục lục đánh số theo 7 mục giảng viên.
- Kết thúc bằng **slide demo mời người xem thử**, không chỉ "Thank you".
- Mỗi slide ~1 phút; slide so sánh (12–13) và kết luận (14) dành 1,5–2 phút. Tổng ~18–20 phút.

---

## Dàn ý 16 slide

### 1. Title
- Tên đề tài: *Labor Market Intelligence — What skills does Vietnam's IT job market ask for, and what goes with higher pay?*
- Môn FDS (USTH), tên 5 thành viên + vai trò (Crawl / Parse & clean / Skills & rules / Models / EDA & integration), ngày 06/10/2026.

### 2. Agenda
- 7 mục đúng thứ tự giảng viên: Problem · Data · Models & related work · Building · Testing · Performance & comparison · Lessons learned (+ Demo).

### 3. Problem *(mục: The prediction or analysis problem — đúng 1 slide)*
- Bối cảnh (góc nhìn sinh viên/người tìm việc), 2 dòng:
  - Không biết nên học **kỹ năng nào đi kèm nhau**.
  - **75% tin giấu lương** → không biết kỹ năng/cấp bậc nào đáng giá. Nguồn: `data.pct_with_salary` (25,0 → 75% giấu).
- 3 câu hỏi:
  - **Q1** Kỹ năng nào hay được yêu cầu cùng nhau? *(phân tích — luật kết hợp)*
  - **Q2** Tin tuyển dụng có tự chia thành nhóm nghề theo kỹ năng không? *(phân tích — phân cụm)*
  - **Q3** Cấp bậc/kỹ năng/địa điểm nào đi kèm dải lương cao? *(dự đoán — phân lớp)*
- Nguồn dữ liệu: ITviec, 1 lần crawl ngày `data.crawl_date` (2026-09-29), `data.n_jobs` (688) tin.
- 🗣️ "That's why we built this: a data-driven view of skills and pay from real job postings."
- ⚠️ Không khẳng định điều dữ liệu không chứng minh (vd. "thiếu hụt nhân lực", "chi phí tuyển dụng cao").

### 4. Data pipeline *(mục: Data after preprocessing, 1/2)*
- Sơ đồ: **Crawl → Parse → Clean → Skill extraction → 3 models → Comparison**.
- Hình: `reports/figures/eda_pipeline_funnel.png` (phễu số tin qua từng bước).
- 3 gạch đầu dòng:
  - **Crawl có trách nhiệm:** User-Agent ghi rõ tên dự án, delay ≥ 3 s, theo robots.txt, 715 request 100% HTTP 200. Nguồn: `docs/governance.md`.
  - **Lương lấy từ dữ liệu có cấu trúc (JSON-LD) vì giao diện ẩn lương.** Nguồn: `docs/DECISIONS.md` 29/09.
  - **Kỹ năng trích bằng từ điển** (114 kỹ năng, có alias) — độ phủ `data.skill_dict_coverage_a7_pct` (72,6%) trên bộ kiểm tra độc lập. Nguồn: `reports/A7_evaluation_seed2026.md`.
- ⭐ Đổi nguồn từ TopCV sang ITviec ngày đầu vì TopCV chặn bot (Cloudflare) — nhóm **không** lách chặn.

### 5. Data after preprocessing *(mục: Data after preprocessing, 2/2)*
- Số lớn: **`data.n_jobs` (688) tin × 16 cột** · **`data.n_jobs_with_skills` (677) × `data.n_skills_in_matrix` (100) kỹ năng** · **`data.n_jobs_with_salary` (172) tin có lương** · train/test **`q1_rules.n_train`/`n_test` (473/204)**.
- Bảng cột rút gọn (nguồn `docs/DATA_CONTRACT.md`): job_id, title, company, level, location, posted_date, category, salary_min/max (triệu VND/tháng), salary_status, currency_original, jd_text…
- Ghi chú quy đổi: tỷ giá cố định (`src/parse/salary.py`, ASSUMPTIONS A9), không phân biệt gross/net (A14).
- ⚠️ Không chiếu nội dung JD gốc (cam kết ToS).

### 6. What the data looks like *(EDA)*
- Hình: `eda_top_skills.png` + `eda_salary_distribution.png` (hoặc `eda_levels.png`).
- 3 gạch đầu dòng:
  - **Kỹ năng phổ biến nhất là kỹ năng chung**: `eda.top10_skills_pct` (english 54,7%, api 45,2%, communication 42,0%…).
  - **Lương trung vị `eda.salary_median_million_vnd` (38,7) triệu/tháng**; 3 lớp tertile cắt ở `q3_tree.tertile_bounds_million_vnd` (32,2 / 50,0).
  - **Chỉ `data.pct_with_salary` (25%) tin có lương, phần lớn ghi USD** (`eda.currency_counts`: 151 USD / 21 VND).
- ⚠️ `english`, `communication` đứng đầu là do từ điển có kỹ năng mềm — nói rõ để không bị hiểu là "kỹ năng kỹ thuật quan trọng nhất".

### 7. Models & related work *(mục: Your model and related (SOTA) models)*
- Bảng 3 dòng:

| | Mô hình của nhóm | Phương pháp so sánh | Hướng SOTA (chỉ related work) |
|---|---|---|---|
| Q1 | Apriori, chia train/test theo thời gian | FP-Growth | Mô hình ngôn ngữ trích kỹ năng từ JD |
| Q2 | Hierarchical clustering, khoảng cách Jaccard | K-means, HDBSCAN, HAC linkage khác | Nhóm nghề từ embedding văn bản |
| Q3 | Decision Tree (CART), nested CV | Logistic regression, naive Bayes, k-NN, random forest, gradient boosting | Transformer (vd. PhoBERT cho tiếng Việt) dự đoán lương từ JD |

- 🗣️ "We did not train transformer models: 172 labelled jobs are far too few, and our goal is interpretable rules."
- ⚠️ **Gọi random forest / K-means là "standard / alternative methods", không gọi là SOTA.**
- ⚠️ Nếu nêu tên mô hình/bài báo SOTA (PhoBERT, JobBERT, SkillSpan…), **kiểm chứng trích dẫn trước** — không đưa tên chưa kiểm tra.

### 8. Building Q1 — Association rules
- Hình: `model_rules_train_test.png` hoặc bảng 5 luật từ `q1_rules.top_rules`.
- 3 gạch đầu dòng:
  - **Train = 70% tin cũ, test = 30% tin mới** (theo ngày đăng) để kiểm tra luật có giữ được theo thời gian.
  - **Thử 5 mức min_support, chọn `q1_rules.min_support` (0,1) → `q1_rules.n_rules` (43) luật**; lọc lift > 1,2, confidence ≥ 0,5.
  - **Luật mạnh nhất:** spring → java, kubernetes → docker, gcp → aws (`q1_rules.top_rules`).

### 9. Building Q2 — Clustering
- Hình: `model_cluster_profiles.png` (dendrogram `dendrogram.png` để phụ lục).
- 3 gạch đầu dòng:
  - **Lọc kỹ năng mềm, kỹ năng quá phổ biến (> 40%) và quá hiếm (< 10 tin)**; còn `data.n_jobs_clustered` (540) tin.
  - **Khoảng cách Jaccard + weighted linkage; cụm < 15 tin coi là nhiễu.**
  - **Kết quả: `q2_clustering.n_real_clusters` (5) cụm + `n_noise_jobs` (21) tin nhiễu**; tên cụm theo top kỹ năng (`reports/purity_report.md`): DevOps/Backend chung (309), AI/Python (85), SQL/.NET (73), Cloud/Data (26), QA (26).
- ⚠️ Quy tắc chọn số cụm được đổi **sau khi** quy tắc cũ không còn số cụm hợp lệ (DECISIONS 04/10) — nếu bị hỏi, nói thẳng.

### 10. Building Q3 — Salary classifier
- Hình: `model_feature_importance.png` + bảng "phân bố lớp lương theo cấp bậc" trong `reports/classification_report.md`.
- 3 gạch đầu dòng:
  - **Nhãn Low/Mid/High chia tertile → lớp cân bằng** `q3_tree.class_counts` (60/55/57).
  - **Đặc trưng: `q3_tree.n_features` (81) = kỹ năng + cấp bậc (suy từ tiêu đề) + địa điểm.**
  - **Nested CV (5 fold ngoài × 3 fold trong) để chọn tham số** → `q3_tree.final_params`.
- ⭐ Cấp bậc quyết định nhiều nhất: Lead 75% High, Manager 78% High (bảng trong classification_report).
- ⚠️ **Nhóm `Intern/Junior` toàn bộ là Low, nhưng 14/17 tin là thực tập sinh (phụ cấp).** Phải nói rõ, nếu không người nghe hiểu thành "Junior lương thấp".
- ⚠️ **Không chiếu `tree_viz.png` cỡ lớn** (sâu 6, 15 lá, không đọc được) — để phụ lục. Không diễn giải các nhánh theo kỹ năng (lá < 10 tin).
- ⚠️ "Middle 73% Low" chỉ dựa trên 11 tin — không trình bày như phát hiện.

### 11. Testing *(mục: Testing your model)*
- Hình: `confusion_matrix.png`.
- 3 gạch đầu dòng:
  - **Q1: `q1_rules.top_rules_hold_on_test` (9/10) luật top vẫn đạt ngưỡng trên tin mới.**
  - **Q3: accuracy out-of-fold `q3_tree.accuracy` (0,517), 95% CI `q3_tree.accuracy_ci95` (0,442–0,593) vs baseline `q3_tree.baseline` (0,349).** Recall từng lớp `q3_tree.recall_by_class`.
  - **Q2: purity `q2_clustering.purity` (0,322) vs baseline `baseline_purity` (0,214); độ ổn định qua mẫu con `comparison.q2_stability_ari_mean` (0,345).**
- Ý phụ: kết quả **tái lập được** — SHA-256 cho dữ liệu (`docs/MANIFEST.json`), kết quả không đổi khi đổi seed, 131 test tự động.
- ⭐ Khoảng tin cậy và baseline là thứ chứng minh mô hình "có học được", không chỉ "con số trông đẹp".

### 12. Performance & comparison — Q3
- Hình: `model_compare_classifiers.png`. Nguồn: `comparison.q3_classifiers`, `reports/model_comparison.md`.
- 3 gạch đầu dòng:
  - **Random forest cao nhất (0,581) nhưng không phương pháp nào hơn Decision Tree có ý nghĩa thống kê** (`comparison.q3_significantly_better_than_tree` = rỗng; CI ghép cặp của hiệu đều chứa 0).
  - **Cây chỉ dùng cấp bậc (6 đặc trưng) đạt 0,547 ≈ cây đầy đủ (81 đặc trưng)** → với 172 tin, kỹ năng gần như không thêm thông tin.
  - **Giữ Decision Tree vì đọc được luật trực tiếp**; logistic regression cũng là lựa chọn hợp lý.
- ⭐ Đây là phần giảng viên nhấn mạnh — nói chậm, chỉ vào khoảng tin cậy.
- ⚠️ Không nói "hai model bằng nhau" — nói "**không đủ bằng chứng** để kết luận model nào tốt hơn" (172 mẫu).

### 13. Performance & comparison — Q2, Q1 và giới hạn
- Hình: `model_compare_clustering.png`; bảng nhỏ cùng số cụm từ `comparison.q2_same_size`.
- 3 gạch đầu dòng:
  - **Không phương pháp nào tìm được nhóm nghề rõ** (silhouette mọi phương pháp ≈ 0, `comparison.q2_methods`).
  - **K-means tốt hơn HAC của nhóm:** purity cao hơn có ý nghĩa ở 4/5 mức số cụm (5 cụm: 0,415 vs 0,322, `comparison.q2_same_size`) và ổn định hơn (`comparison.q2_stability_by_method`: 0,630 vs 0,345). Nhóm giữ HAC (Jaccard hợp dữ liệu thưa, dendrogram dễ giải thích; DECISIONS 05/10).
  - **Q1: FP-Growth cho đúng cùng luật với Apriori** (`comparison.q1_apriori_fpgrowth_identical`), chậm hơn trên dữ liệu nhỏ.
- Giới hạn (bias): tin có lương **nghiêng về Hà Nội** — HN `bias.location.loc_hn` (51,7% vs 38,6%, adj p 0,006); kỹ năng không khác biệt (`bias.n_skills_significant` = 0/100). Hình phụ: `bias_levels.png`. Nguồn: `reports/bias_analysis.md`.
- ⭐ Thừa nhận K-means tốt hơn là điểm cộng — cho thấy nhóm so sánh nghiêm túc.
- ⚠️ Không nói "chênh lệch không đáng kể" cho Q2 — đã kiểm định và K-means **hơn có ý nghĩa** về purity.

### 14. Findings & limitations
- Findings (lấy từ phần kết luận cuối `final_notebook.ipynb`):
  - **Q1:** bộ kỹ năng DevOps/cloud đi cùng nhau và ổn định theo thời gian.
  - **Q2:** kỹ năng không tách thành nhóm nghề rõ; chỉ vài cụm nhỏ (AI, SQL, QA) có đặc trưng.
  - **Q3:** cấp bậc quyết định nhiều nhất; lớp Mid khó tách nhất.
- Limitations: 1 snapshot, 688 tin; 25% tin có lương, nghiêng Hà Nội; từ điển phủ 72,6%; `eda.pct_level_unknown` (42,4%) tin không suy được cấp bậc; phân cụm nhạy với từ điển và kém ổn định.

### 15. Lessons learned *(mục: Lessons learned)*
Chọn 4–5 ý, mỗi ý 1 dòng + 1 ví dụ có số (nguồn: `docs/DECISIONS.md`):
1. **Kiểm tra nguồn dữ liệu sớm** — TopCV chặn bot ngày đầu → đổi sang ITviec hợp lệ.
2. **Giao diện web ≠ dữ liệu** — lương nằm trong JSON-LD; 4 số cuối URL bị trùng, không dùng làm ID.
3. **Kiểm tra trên dữ liệu thật** — dedup theo tiêu đề loại nhầm 4 tin; thiếu alias "APIs" làm sót 63 tin.
4. **Đo, đừng đoán** — độ phủ từ điển ban đầu ghi ">90%" chưa đo; đo trên bộ độc lập chỉ 72,6%. Ban đầu nghĩ HAC ≈ K-means; kiểm định cho thấy K-means tốt hơn.
5. **Model phức tạp hơn chưa chắc tốt hơn** — với 172 mẫu, random forest không hơn có ý nghĩa; chỉ cấp bậc đã đủ.

### 16. Try it yourself (demo) + Thank you
- Chạy `notebooks/demo.ipynb`: chọn kỹ năng + địa điểm → dải lương, kỹ năng hay đi kèm, nhóm nghề tuyển.
- 🗣️ Mời giảng viên chọn một kỹ năng bất kỳ.
- Lời cảm ơn; có thể nhắc nhóm đã tham khảo cách trình bày của các nhóm khóa trước.

### Phụ lục (không chiếu, để trả lời câu hỏi)
- `tree_viz.png`, `dendrogram.png`, `eda_cooccurrence.png`, bảng đầy đủ trong `reports/model_comparison.md`.

---

## Chỗ cần nhấn mạnh

- ⭐ **So sánh có kiểm định** (slide 12–13): baseline, khoảng tin cậy, bootstrap ghép cặp — phần giảng viên yêu cầu và là điểm mạnh nhất.
- ⭐ **Trung thực về kết quả yếu**: phân cụm không tìm thấy nhóm nghề rõ, K-means tốt hơn — trình bày như phát hiện.
- ⭐ **Cấp bậc là yếu tố lương quan trọng nhất**, cây chỉ dùng cấp bậc ≈ cây đầy đủ.
- ⭐ **Thu thập dữ liệu có trách nhiệm** (UA, delay, robots.txt, không lách Cloudflare, không đăng lại JD).

## Điều cần tránh

- ⚠️ Gõ tay số liệu — luôn lấy từ `key_numbers.json` / `reports/`.
- ⚠️ Kết luận "mô hình tốt" mà không so với baseline; ghi sai đơn vị (accuracy/purity không phải %, lương là triệu VND/tháng).
- ⚠️ Gọi RF/K-means là SOTA; nêu bài báo SOTA chưa kiểm chứng.
- ⚠️ Diễn giải "Junior lương thấp" (thực ra là thực tập sinh); diễn giải nhánh cây theo kỹ năng; diễn giải "Middle 73% Low" (11 tin).
- ⚠️ Nói "không khác biệt" khi chỉ là "không đủ bằng chứng"; nói Q2 "chênh lệch không đáng kể".
- ⚠️ Chiếu nội dung JD gốc, tên/liên hệ người tuyển dụng.
- ⚠️ Biểu đồ tròn nhiều phần, trục không làm sạch, chữ nhỏ hơn 12pt.
- ⚠️ Chạy lại `final_notebook.ipynb` khi đang thuyết trình (~2 phút) — mở bản có sẵn output.

## Câu hỏi có thể gặp (chuẩn bị trả lời)

| Câu hỏi | Trả lời ngắn | Nguồn |
|---|---|---|
| Sao chỉ 688 tin? | ITviec chỉ có chừng đó tin IT đang mở; đã hạ ngưỡng 1.000, ghi vào hạn chế | DECISIONS 29/09 |
| Lấy lương thế nào khi web ẩn lương? | JSON-LD công khai trong HTML (cho máy tìm kiếm), không đăng nhập | DECISIONS 29/09 |
| Sao không dùng random forest? | Không hơn có ý nghĩa; cây đọc được luật | `reports/model_comparison.md` |
| Sao không đổi sang K-means? | Phát hiện ngay trước thuyết trình; kết luận chính không đổi; hướng phát triển tiếp | DECISIONS 05/10 |
| Sao không dùng BERT/PhoBERT? | 172 tin có nhãn quá ít; ưu tiên giải thích được | slide 7 |
| Train/test theo thời gian có ý nghĩa không? | Đo "tuổi" của tin trong 1 snapshot, không phải xu hướng dài hạn | `reports/rules_eval.md` |

## Checklist trước giờ thuyết trình

- [ ] `git pull`, `pip install -r requirements.txt` trên máy thuyết trình; kernel `.venv`.
- [ ] 4 file trong `data/processed/` khớp `docs/MANIFEST.json`.
- [ ] Chạy thử `demo.ipynb`; mở sẵn `final_notebook.ipynb` (đã có output).
- [ ] Bản dự phòng: `jupyter nbconvert --to html notebooks/final_notebook.ipynb notebooks/demo.ipynb` + ảnh chụp demo.
- [ ] Mọi số trên slide đối chiếu lại với `reports/key_numbers.json`.
