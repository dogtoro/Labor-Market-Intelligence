# Đánh giá Association Rules (Train vs Test)

## Kích thước tập dữ liệu
- Train: 473 bản ghi (70% tin cũ)
- Test: 204 bản ghi (30% tin mới)

## Lựa chọn tham số
- `min_confidence` = 0.5: Đảm bảo độ tin cậy của luật cao (ít nhất 50% khả năng kéo theo).
- `min_lift` = 1.2: Lọc các luật có tương quan tích cực rõ rệt.
Kết quả chạy Apriori trên các mức min_support khác nhau (Train):
- min_support = 0.03: tìm được 2589 luật
- min_support = 0.04: tìm được 1093 luật
- min_support = 0.05: tìm được 482 luật
- min_support = 0.06: tìm được 198 luật
- min_support = 0.1: tìm được 34 luật

=> Chọn `min_support` = 0.1 vì số lượng luật tìm được (34) nằm trong khoảng vừa phải (không quá ít để phân tích, không quá nhiều dẫn đến nhiễu).

## Top 10 luật kết hợp (theo Lift, mỗi tập kỹ năng chỉ giữ 1 luật)
| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| kubernetes | docker | 0.133 | 0.649 | 3.135 | 0.167 | 0.739 | 2.513 |
| microservices | kubernetes | 0.101 | 0.615 | 3.001 | 0.074 | 0.429 | 1.901 |
| gcp | aws | 0.121 | 0.814 | 2.986 | 0.147 | 0.938 | 3.135 |
| azure | aws | 0.129 | 0.744 | 2.728 | 0.137 | 0.778 | 2.601 |
| aws, git | cicd | 0.104 | 0.790 | 2.492 | 0.132 | 0.964 | 2.981 |
| docker | cicd | 0.152 | 0.735 | 2.317 | 0.196 | 0.667 | 2.061 |
| api, git | cicd | 0.106 | 0.704 | 2.221 | 0.142 | 0.674 | 2.085 |
| cicd | git | 0.190 | 0.600 | 2.200 | 0.225 | 0.697 | 2.091 |
| docker | git | 0.121 | 0.582 | 2.133 | 0.201 | 0.683 | 2.050 |
| kubernetes | aws | 0.118 | 0.577 | 2.117 | 0.142 | 0.630 | 2.108 |

## Nhận xét (Overfit / Rule drift)
Có 9/10 luật trong top 10 vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.

> **Hạn chế dữ liệu:** Dữ liệu thu thập là một snapshot các tin tuyển dụng còn active tính đến ngày 29/09. Do đó, việc chia Train/Test theo `posted_date` phản ánh sự khác biệt theo độ tuổi của tin (tin cũ vs tin mới đăng), chứ không hoàn toàn đo lường được sự thay đổi của thị trường theo thời gian dài.

## Top luật có kỹ năng data
Kỹ năng data dùng để lọc: airflow, bigquery, data_lake, data_modeling, data_pipeline, data_warehouse, databricks, dbt, deep_learning, etl, hadoop, kafka, machine_learning, numpy, pandas, power_bi, python, redshift, snowflake, spark, sql, statistics, tableau.

Số luật có kỹ năng data theo min_support (Train, lift > 1.2, confidence >= 0.5):
- min_support = 0.09: 2 luật
- min_support = 0.08: 3 luật
- min_support = 0.07: 7 luật
- min_support = 0.06: 16 luật

=> Chọn `min_support` = 0.06 (mức cao nhất cho ra ≥10 luật có kỹ năng data; nếu không có thì lấy mức nhiều luật nhất).

| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| kafka | redis | 0.061 | 0.580 | 6.235 | 0.103 | 0.636 | 4.188 |
| kafka | kubernetes | 0.074 | 0.700 | 3.413 | 0.064 | 0.394 | 1.747 |
| mssql | sql | 0.072 | 0.944 | 3.285 | 0.069 | 0.875 | 2.975 |
| sql, cicd | git | 0.068 | 0.711 | 2.607 | 0.059 | 0.706 | 2.118 |
| python, git | cicd | 0.061 | 0.725 | 2.286 | 0.098 | 0.690 | 2.132 |
| sql, cicd | api | 0.063 | 0.667 | 1.911 | 0.064 | 0.765 | 1.880 |
| sql, git | api | 0.063 | 0.667 | 1.911 | 0.064 | 0.867 | 2.130 |
| kafka | api | 0.068 | 0.640 | 1.835 | 0.113 | 0.697 | 1.713 |
| sql, communication | api | 0.076 | 0.514 | 1.474 | 0.054 | 0.550 | 1.352 |
| sql, english | communication | 0.108 | 0.637 | 1.443 | 0.069 | 0.467 | 1.221 |

Có 8/10 luật data vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.