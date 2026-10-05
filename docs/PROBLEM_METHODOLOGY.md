# 📘 BÀI TOÁN & PHƯƠNG PHÁP LUẬN (PROBLEM & METHODOLOGY)

> **Dự án:** Labor Market Intelligence – Thị trường tuyển dụng CNTT & Dữ liệu Việt Nam 2026  
> **Môn học:** Fundamentals of Data Science (USTH)  
> **Tài liệu tham chiếu:** [README.md](../README.md), [DATA_CONTRACT.md](DATA_CONTRACT.md), [ASSUMPTIONS.md](ASSUMPTIONS.md)

---

## 1. MÔ TẢ BÀI TOÁN (PROBLEM STATEMENT)

### 1.1 Bối cảnh thực tiễn
Thị trường lao động ngành Công nghệ Thông tin (IT) và Kỹ thuật/Khoa học Dữ liệu (Data Science, Data Engineering, AI/ML) tại Việt Nam năm 2026 đang chứng kiến sự dịch chuyển mạnh mẽ:
- Sự bùng nổ của Generative AI và các hệ thống dữ liệu phân tán đòi hỏi kỹ sư kết hợp nhiều nhóm kỹ năng (skill bundles) thay vì chỉ biết một ngôn ngữ đơn lập.
- Tiêu đề tin tuyển dụng trên các sàn như ITviec rất phong phú, nhưng không phản ánh đồng nhất ranh giới nghề nghiệp.
- 75% tin tuyển dụng trên ITviec (516/688 tin, 29/09) không công khai mức lương, gây khó khăn cho việc định hướng mức thu nhập theo kỹ năng.

### 1.2 Mục tiêu và Câu hỏi nghiên cứu (Research Questions)

| STT | Câu hỏi nghiên cứu | Ý nghĩa khoa học & ứng dụng | Phương pháp / Mô hình |
|---|---|---|---|
| **Q1** | Những nhóm kỹ năng nào thường xuyên **đồng xuất hiện** (co-occur) trong các bản mô tả công việc (JD)? | Tìm ra các bộ kỹ năng bổ trợ (complementary skills) cần học cùng lúc. | **Association Rules (Apriori)** |
| **Q2** | Tin tuyển dụng tự nhiên phân tách thành **bao nhiêu nhóm nghề** theo tổ hợp kỹ năng thực tế? | Tự động gom cụm vị trí công việc, so sánh với trường "Job Expertise" của ITviec. | **Hierarchical Clustering (Jaccard + Weighted Linkage)** |
| **Q3** | Kỹ năng, kinh nghiệm và địa điểm nào **dự báo dải lương cao**? | Giải thích quy luật định giá kỹ năng của thị trường. | **Decision Tree Classification (CART)** |

---

## 2. PHƯƠNG PHÁP LUẬN (METHODOLOGY)

### 2.1 Kiến trúc Pipeline Dữ Liệu
Pipeline xử lý theo mô hình 4 tầng độc lập:
1. **Raw Layer (`data/raw/`):** Lưu trữ snapshot HTML thô từ sitemap ITviec (688 tin, crawl tối 29/09), ghi nhận SHA-256 manifest.
2. **Parsed Layer (`data/interim/jobs_parsed.parquet`):** Trích xuất text có cấu trúc, kiểm tra hợp đồng qua `validate_parsed()`.
3. **Cleaned Layer (`data/processed/jobs_clean.parquet`):** Khử trùng lặp đa tiêu chí, chuẩn hóa tiền tệ và dải lương, kiểm tra qua `validate_clean()`.
4. **Feature & Model Layer (`data/processed/skill_matrix.parquet`):** Trích xuất ma trận kỹ năng nhị phân $N \times M$, kiểm tra qua `validate_skills()`.

### 2.2 Các bước tiền xử lý chuyên sâu

#### 1. Khử trùng lặp (Deduplication):
- **Điều kiện:** Cùng công ty AND độ tương đồng tiêu đề (SequenceMatcher ratio) $\ge 0.85$ AND độ tương đồng JD $\ge 0.95$ AND ngày đăng cách nhau $\le 7$ ngày. Trên dữ liệu 29/09: 0 tin trùng.
- Giữ lại bản ghi mới nhất, loại bỏ tin đăng lặp lại để tránh làm lệch phân phối kỹ năng.

#### 2. Chuẩn hóa & Rời rạc hóa lương (Salary Normalization):
- Quy đổi USD sang VNĐ triệu (tỷ giá cố định 25,780 VND/USD — A9); lương theo ngày × 20 ngày công (A18); không điều chỉnh gross ↔ net (A14).
- Nhận diện 3 trạng thái:
  - `full_range`: Đầy đủ `salary_min`, `salary_max`. Tính `salary_mid = (min + max) / 2`.
  - `one_sided`: Chỉ có cận trên hoặc cận dưới.
  - `undisclosed`: Lương thoả thuận / cạnh tranh / thiếu thông tin.
- Rời rạc hóa dải lương phục vụ mô hình phân lớp:
  - `Low`: $< 15$ triệu VND.
  - `Mid`: $15 - 30$ triệu VND.
  - `High`: $> 30$ triệu VND.
  - ⚠️ Trên 172 tin có lương, ngưỡng cố định chỉ cho 18 / 29 / 125 mẫu — không đạt ≥50/lớp. **Mốc 2 (01/10) đã chốt: chia tertile** (60 / 55 / 57 mẫu, ranh giới ≈ 32,2 / 50,0 triệu, tính bằng code); `one_sided` dùng cận duy nhất làm `salary_mid` (`DECISIONS.md`).

#### 3. Trích xuất kỹ năng bằng Từ điển Regex (Skill Extraction):
- Từ điển gồm $> 100$ kỹ năng IT/Data được chuẩn hóa với danh sách từ đồng nghĩa (aliases).
- Sử dụng regex word-boundary `\b` chống nhận diện sai các từ ngắn (C, R, Go, Java vs JavaScript).
- Ma trận kỹ năng nhị phân $X \in \{0, 1\}^{N \times M}$ chỉ giữ lại các kỹ năng có tần suất $\ge 5$ tin.

---

### 2.3 Mô hình Khai phá Dữ liệu & Học máy (Models)

### Phương pháp 1: Khai phá Luật Kết hợp (Apriori Algorithm)
- **Độ đo:**
  - $\text{Support}(X \to Y) = P(X \cup Y) = \frac{\sigma(X \cup Y)}{N}$
  - $\text{Confidence}(X \to Y) = P(Y \mid X) = \frac{\text{Support}(X \cup Y)}{\text{Support}(X)}$
  - $\text{Lift}(X \to Y) = \frac{\text{Confidence}(X \to Y)}{\text{Support}(Y)}$ (lọc các luật có $\text{Lift} > 1.2$)
- **Kiểm định tính bền vững (Temporal Evaluation):**
  - Chia tập dữ liệu theo thứ tự thời gian `posted_date`: 70% tin cũ làm Train, 30% tin mới làm Test.
  - Khai phá luật trên Train (`min_support` ∈ {0.03, 0.04, 0.05, 0.06, 0.10}, `confidence ≥ 0.5`) và đánh giá lại Support, Confidence, Lift trên Test nhằm kiểm tra hiện tượng suy giảm luật (rule drift).

### Phương pháp 2: Phân cụm Phân cấp (Hierarchical Agglomerative Clustering)
- **Độ đo khoảng cách Jaccard:**
  $$d_J(\mathbf{u}, \mathbf{v}) = 1 - \frac{|\mathbf{u} \cap \mathbf{v}|}{|\mathbf{u} \cup \mathbf{v}|}$$
- **Phương pháp liên kết:** Weighted Linkage (WPGMA). Ward không hợp lệ với Jaccard; Average bị chaining (DECISIONS 03/10).
- **Xác định số cụm tối ưu $k$:** Dendrogram + Silhouette, $k \in [4, 8]$; cụm < 15 tin coi là nhiễu (nhãn -1); $k$ hợp lệ khi có ≥ 3 cụm thật và nhiễu ≤ 5%; chọn $k$ có Silhouette cao nhất (DECISIONS 04/10). Purity tính trên tin không phải nhiễu.
- **Đánh giá độ tinh khiết (Purity):**
  $$\text{Purity} = \frac{1}{N} \sum_{k} \max_j |c_k \cap t_j|$$
  So sánh cụm dự đoán $c_k$ với danh mục tuyển dụng chuẩn $t_j$ ("Job Expertise" của ITviec, 72 giá trị gộp thành 10 nhóm — A16, đã review).

### Phương pháp 3: Cây quyết định Phân lớp Dải Lương (Decision Tree Classifier)
- **Mục tiêu:** Phân lớp tin tuyển dụng vào 3 mức lương: Low, Mid, High.
- **Đặc trưng đầu vào:** Ma trận kỹ năng, cấp bậc suy từ tiêu đề (`Intern/Junior`, Middle, Senior, Lead, Manager, Unknown), khu vực làm việc (HCM, HN, ĐN, khác). ITviec không có số năm kinh nghiệm.
- **Huấn luyện & Tối ưu:** Nested Stratified CV (ngoài 5 fold đánh giá, trong 3 fold chọn `max_depth` ∈ {3..6}, `min_samples_leaf` ∈ {5, 10, 15}), 95% bootstrap CI.
- **Khả năng diễn giải:** Xuất biểu đồ cây và bảng xếp hạng tầm quan trọng đặc trưng (Feature Importance).

### So sánh với phương pháp khác (yêu cầu giảng viên, DECISIONS 04/10)
- **Q3:** so Decision Tree với baseline lớp đông nhất, cây chỉ dùng cấp bậc, logistic regression, Bernoulli naive Bayes, k-NN (Jaccard), random forest, gradient boosting — cùng nested CV và cùng seed; báo cáo CI bootstrap và CI ghép cặp của hiệu accuracy.
- **Q2:** so HAC weighted với HAC average/complete, K-means, HDBSCAN — cùng ma trận và quy tắc nhiễu; bootstrap ghép cặp purity/ARI giữa HAC weighted và K-means, cả ở cùng số cụm thật (3–7); độ ổn định bằng ARI trên cùng 50 mẫu con 80% cho mọi phương pháp có k hợp lệ.
- **Q1:** Apriori vs FP-Growth (cùng luật, so thời gian).
- Mô hình dựa trên mô hình ngôn ngữ (transformer) chỉ nêu ở phần related work vì 172 tin có nhãn là quá ít và khó giải thích.
- Kết quả: `reports/model_comparison.md`.

### Phân tích Thiên lệch Dữ liệu Khuyết (Missing Salary Bias Analysis)
- Đánh giá định lượng sự khác biệt về phân phối kỹ năng và cấp bậc giữa nhóm tin công khai lương ($25\%$, 172 tin) và nhóm tin ẩn lương ($75\%$, 516 tin).
- Xác định rõ phạm vi áp dụng và giới hạn suy luận của mô hình dự báo thu nhập.
