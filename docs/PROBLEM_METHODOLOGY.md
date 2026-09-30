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
- Khoảng 70% tin tuyển dụng ẩn thông tin mức lương ("Thoả thuận", "Cạnh tranh"), gây khó khăn cho việc định hướng mức thu nhập theo kỹ năng.

### 1.2 Mục tiêu và Câu hỏi nghiên cứu (Research Questions)

| STT | Câu hỏi nghiên cứu | Ý nghĩa khoa học & ứng dụng | Phương pháp / Mô hình |
|---|---|---|---|
| **Q1** | Những nhóm kỹ năng nào thường xuyên **đồng xuất hiện** (co-occur) trong các bản mô tả công việc (JD)? | Tìm ra các bộ kỹ năng bổ trợ (complementary skills) cần học cùng lúc. | **Association Rules (Apriori)** |
| **Q2** | Tin tuyển dụng tự nhiên phân tách thành **bao nhiêu nhóm nghề** theo tổ hợp kỹ năng thực tế? | Tự động gom cụm vị trí công việc, so sánh với trường "Job Expertise" của ITviec. | **Hierarchical Clustering (Jaccard + Ward/Average Linkage)** |
| **Q3** | Kỹ năng, kinh nghiệm và địa điểm nào **dự báo dải lương cao**? | Giải thích quy luật định giá kỹ năng của thị trường. | **Decision Tree Classification (CART)** |

---

## 2. PHƯƠNG PHÁP LUẬN (METHODOLOGY)

### 2.1 Kiến trúc Pipeline Dữ Liệu
Pipeline xử lý theo mô hình 4 tầng độc lập:
1. **Raw Layer (`data/raw/`):** Lưu trữ snapshot HTML thô từ sitemap ITviec (681 tin, 29/09), ghi nhận SHA-256 manifest.
2. **Parsed Layer (`data/interim/jobs_parsed.parquet`):** Trích xuất text có cấu trúc, kiểm tra hợp đồng qua `validate_parsed()`.
3. **Cleaned Layer (`data/interim/jobs_clean.parquet`):** Khử trùng lặp đa tiêu chí, chuẩn hóa tiền tệ và dải lương, kiểm tra qua `validate_clean()`.
4. **Feature & Model Layer (`data/processed/skill_matrix.parquet`):** Trích xuất ma trận kỹ năng nhị phân $N \times M$, kiểm tra qua `validate_skills()`.

### 2.2 Các bước tiền xử lý chuyên sâu

#### 1. Khử trùng lặp (Deduplication):
- **Điều kiện:** Cùng công ty AND độ tương đồng tiêu đề (SequenceMatcher ratio) $\ge 0.85$ AND ngày đăng cách nhau $\le 7$ ngày.
- Giữ lại bản ghi mới nhất, loại bỏ tin đăng lặp lại để tránh làm lệch phân phối kỹ năng.

#### 2. Chuẩn hóa & Rời rạc hóa lương (Salary Normalization):
- Quy đổi USD sang VNĐ triệu (tỷ giá cố định 25,500 VND/USD).
- Nhận diện 3 trạng thái:
  - `full_range`: Đầy đủ `salary_min`, `salary_max`. Tính `salary_mid = (min + max) / 2`.
  - `one_sided`: Chỉ có cận trên hoặc cận dưới.
  - `undisclosed`: Lương thoả thuận / cạnh tranh / thiếu thông tin.
- Rời rạc hóa dải lương phục vụ mô hình phân lớp:
  - `Low`: $< 15$ triệu VND.
  - `Mid`: $15 - 30$ triệu VND.
  - `High`: $> 30$ triệu VND.

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
  - Khai phá luật trên Train và đánh giá lại Support, Confidence trên Test nhằm kiểm tra hiện tượng suy giảm luật (rule drift).

### Phương pháp 2: Phân cụm Phân cấp (Hierarchical Agglomerative Clustering)
- **Độ đo khoảng cách Jaccard:**
  $$d_J(\mathbf{u}, \mathbf{v}) = 1 - \frac{|\mathbf{u} \cap \mathbf{v}|}{|\mathbf{u} \cup \mathbf{v}|}$$
- **Phương pháp liên kết:** Ward's Linkage hoặc Average Linkage trên ma trận khoảng cách.
- **Xác định số cụm tối ưu $k$:** Biểu đồ Dendrogram kết hợp Silhouette Score.
- **Đánh giá độ tinh khiết (Purity):**
  $$\text{Purity} = \frac{1}{N} \sum_{k} \max_j |c_k \cap t_j|$$
  So sánh cụm dự đoán $c_k$ với danh mục tuyển dụng chuẩn $t_j$ ("Job Expertise" của ITviec, gộp thành 6–8 nhóm — A16).

### Phương pháp 3: Cây quyết định Phân lớp Dải Lương (Decision Tree Classifier)
- **Mục tiêu:** Phân lớp tin tuyển dụng vào 3 mức lương: Low, Mid, High.
- **Đặc trưng đầu vào:** Ma trận kỹ năng, số năm kinh nghiệm, khu vực làm việc (Hà Nội, TP.HCM, Remote...).
- **Huấn luyện & Tối ưu:** 5-Fold Stratified Cross-Validation, cắt tỉa độ sâu (`max_depth = 3..6`, `min_samples_leaf >= 10`).
- **Khả năng diễn giải:** Xuất biểu đồ cây và bảng xếp hạng tầm quan trọng đặc trưng (Feature Importance).

### Phân tích Thiên lệch Dữ liệu Khuyết (Missing Salary Bias Analysis)
- Đánh giá định lượng sự khác biệt về phân phối kỹ năng và cấp bậc giữa nhóm tin công khai lương ($30\%$) và nhóm tin ẩn lương ($70\%$).
- Xác định rõ phạm vi áp dụng và giới hạn suy luận của mô hình dự báo thu nhập.
