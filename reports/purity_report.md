# Báo Cáo Phân Cụm & Purity

- **K đã chọn:** 4 — silhouette cao nhất trong các k hợp lệ (cụm nhỏ nhất ≥ 15 tin), silhouette = 0.0480
- **Số tin dùng để phân cụm:** 548; bị loại (còn < 2 kỹ năng sau khi lọc): 129
- **Kỹ năng bị loại** (xuất hiện > 40% số tin, < 10 tin, hoặc kỹ năng mềm/công cụ quản lý): ab_testing, agile, bi, cassandra, communication, confluence, data_lake, data_pipeline, databricks, dbt, english, hadoop, japanese, jira, mariadb, nginx, numpy, redshift, rust, scala, scikit_learn, snowflake, statistics, tableau, teamwork

## Kết quả các K đã thử

| K | Kích thước các cụm | Silhouette | Purity | Hợp lệ (cụm nhỏ nhất ≥ 15) |
|---|---|---|---|---|
| 4 | 400 / 76 / 43 / 29 | 0.0480 | 0.3339 | ✅ |
| 5 | 351 / 76 / 49 / 43 / 29 | 0.0459 | 0.3540 | ✅ |
| 6 | 351 / 76 / 49 / 43 / 20 / 9 | 0.0430 | 0.3540 | — |
| 7 | 336 / 76 / 49 / 43 / 20 / 15 / 9 | 0.0442 | 0.3631 | — |
| 8 | 280 / 76 / 56 / 49 / 43 / 20 / 15 / 9 | 0.0474 | 0.3978 | — |

## Top 5 kỹ năng mỗi cụm

- **Cụm 1:** sql (88%), python (26%), api (23%), power_bi (23%), figma (21%)
- **Cụm 2:** aws (52%), data_governance (52%), airflow (48%), sql (41%), machine_learning (41%)
- **Cụm 3:** llm (61%), python (57%), aws (50%), azure (39%), machine_learning (37%)
- **Cụm 4:** api (51%), cicd (46%), git (45%), java (34%), aws (34%)

## Đánh giá
- **Purity:** 0.3339
- **Baseline Purity:** 0.2080
- **Weighted F-measure:** 0.3229

## Crosstab (Cluster x Expertise Group)

| Cluster | Architect | BA/PM/Manager | Backend | Data/AI | DevOps/Cloud/System | Frontend/Fullstack | Khác | Mobile | QA/QC | Security |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 22 | 3 | 12 | 2 | 0 | 2 | 0 | 0 | 2 |
| 2 | 1 | 4 | 3 | 18 | 1 | 0 | 0 | 0 | 2 | 0 |
| 3 | 3 | 7 | 3 | 38 | 10 | 3 | 3 | 2 | 1 | 6 |
| 4 | 22 | 27 | 105 | 15 | 51 | 85 | 17 | 16 | 51 | 11 |
