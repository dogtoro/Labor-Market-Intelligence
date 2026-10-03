# Báo Cáo Phân Cụm & Purity

- **K đã chọn:** 8 → **5 cụm thật** + 21 tin nhiễu (3.9%); silhouette = 0.0655
- **Quy tắc chọn k (đặt trước khi xem kết quả, DECISIONS 04/10):** cụm < 15 tin coi là **nhiễu/ngoại lai** (nhãn `-1` trong `cluster_labels.csv`); k hợp lệ khi có ≥ 3 cụm thật và nhiễu ≤ 5%; chọn silhouette cao nhất (tính trên tin không phải nhiễu).
- **Số tin dùng để phân cụm:** 540; bị loại (còn < 2 kỹ năng sau khi lọc): 137
- **Kỹ năng bị loại** (xuất hiện > 40% số tin, < 10 tin, hoặc kỹ năng mềm/công cụ quản lý): agile, api, bi, cassandra, communication, confluence, databricks, dbt, english, hadoop, japanese, jira, mariadb, nginx, numpy, redshift, rust, scala, scikit_learn, snowflake, statistics, tableau, teamwork

## Kết quả các K đã thử

| K | Cụm thật (số tin) | Tin nhiễu | Silhouette | Purity | Baseline | Hợp lệ |
|---|---|---|---|---|---|---|
| 4 | 467 / 60 | 13 (2.4%) | 0.0554 | 0.2410 | 0.2106 | — |
| 5 | 467 / 34 / 26 | 13 (2.4%) | 0.0413 | 0.2581 | 0.2106 | ✅ |
| 6 | 467 / 26 / 26 | 21 (3.9%) | 0.0382 | 0.2601 | 0.2139 | ✅ |
| 7 | 382 / 85 / 26 / 26 | 21 (3.9%) | 0.0476 | 0.3083 | 0.2139 | ✅ |
| 8 | 309 / 85 / 73 / 26 / 26 | 21 (3.9%) | 0.0655 | 0.3218 | 0.2139 | ✅ |

## Top 5 kỹ năng mỗi cụm

- **Nhiễu** (21 tin): dotnet (33%), csharp (24%), microservices (24%), data_governance (19%), machine_learning (19%)
- **Cụm 1** (309 tin): cicd (57%), git (55%), aws (47%), docker (46%), java (43%)
- **Cụm 2** (85 tin): python (51%), llm (48%), cpp (34%), linux (34%), machine_learning (28%)
- **Cụm 3** (73 tin): sql (95%), mssql (36%), dotnet (22%), python (22%), postgresql (21%)
- **Cụm 4** (26 tin): aws (73%), azure (46%), etl (27%), kubernetes (27%), airflow (23%)
- **Cụm 5** (26 tin): test_automation (100%), cicd (54%), sql (31%), git (23%), manual_testing (23%)

## Đánh giá (trên tin không phải nhiễu)
- **Purity:** 0.3218
- **Baseline Purity:** 0.2139
- **Weighted F-measure:** 0.3425

## Nhận xét & hạn chế

- **Cấu trúc cụm yếu:** silhouette = 0.066 (gần 0) — tổ hợp kỹ năng trên ITviec **không tách thành các nhóm nghề rõ ràng**. Đây là kết quả, không phải lỗi.
- **Kết quả nhạy với từ điển:** sau khi bổ sung dạng số nhiều (vd. "APIs", 04/10), `api` vượt ngưỡng 40% và bị loại; quy tắc cũ (mọi cụm ≥ 15 tin) không còn k nào hợp lệ vì luôn có vài cụm 2–13 tin. Đổi sang quy tắc nhiễu (`docs/DECISIONS.md` 04/10) — đây cũng là bằng chứng phân cụm không ổn định.
- **Một cụm "chung" chiếm 309/519 tin không phải nhiễu (60%)** (cụm 1: cicd (57%), git (55%), aws (47%), docker (46%), java (43%)) và trộn lẫn mọi nhóm nghề (xem crosstab).
- **Các cụm nhỏ có đặc trưng rõ hơn:** cụm 2 (85 tin): python (51%), llm (48%); cụm 3 (73 tin): sql (95%), mssql (36%); cụm 4 (26 tin): aws (73%), azure (46%); cụm 5 (26 tin): test_automation (100%), cicd (54%).
- **Purity 0.322 so với baseline 0.214** (baseline = gom tất cả vào 1 cụm, tức tỷ lệ nhóm nghề đông nhất): cụm kỹ năng khớp nhóm nghề tốt hơn baseline nhưng còn xa mức tách bạch; F-measure 0.343.
- **Phạm vi:** 540/688 tin (78%) được phân cụm, trong đó 21 tin là nhiễu; 148 tin (22%) bị loại vì không bắt được kỹ năng nào hoặc còn < 2 kỹ năng sau khi bỏ kỹ năng mềm/hiếm/quá phổ biến.
- Nhóm nghề so sánh lấy từ 72 giá trị "Job Expertise" gộp thành 10 nhóm (`src/models/expertise_groups.json`, ASSUMPTIONS A16 — chờ review).

## Crosstab (Cluster x Expertise Group, không gồm nhiễu)

| Cluster | Architect | BA/PM/Manager | Backend | Data/AI | DevOps/Cloud/System | Frontend/Fullstack | Khác | Mobile | QA/QC | Security |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 15 | 12 | 84 | 25 | 42 | 73 | 4 | 13 | 30 | 11 |
| 2 | 2 | 3 | 7 | 32 | 15 | 2 | 17 | 1 | 1 | 5 |
| 3 | 3 | 24 | 17 | 14 | 2 | 7 | 1 | 1 | 2 | 2 |
| 4 | 4 | 5 | 3 | 9 | 4 | 0 | 0 | 0 | 0 | 1 |
| 5 | 1 | 3 | 0 | 0 | 0 | 2 | 1 | 1 | 18 | 0 |
