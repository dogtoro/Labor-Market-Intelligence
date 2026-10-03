# Đánh giá Association Rules (Train vs Test)

## Kích thước tập dữ liệu
- Train: 473 bản ghi (70% tin cũ)
- Test: 204 bản ghi (30% tin mới)

## Lựa chọn tham số
- `min_confidence` = 0.5: Đảm bảo độ tin cậy của luật cao (ít nhất 50% khả năng kéo theo).
- `min_lift` = 1.2: Lọc các luật có tương quan tích cực rõ rệt.
Kết quả chạy Apriori trên các mức min_support khác nhau (Train):
- min_support = 0.03: tìm được 2608 luật
- min_support = 0.04: tìm được 1098 luật
- min_support = 0.05: tìm được 477 luật
- min_support = 0.06: tìm được 197 luật
- min_support = 0.1: tìm được 35 luật

=> Chọn `min_support` = 0.1 vì số lượng luật tìm được (35) nằm trong khoảng vừa phải (không quá ít để phân tích, không quá nhiều dẫn đến nhiễu).

## Top 10 luật kết hợp (theo Lift, mỗi tập kỹ năng chỉ giữ 1 luật)
| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| spring | java | 0.101 | 1.000 | 4.683 | 0.083 | 1.000 | 4.000 |
| kubernetes | docker | 0.133 | 0.656 | 3.200 | 0.167 | 0.723 | 2.419 |
| gcp | aws | 0.118 | 0.812 | 2.999 | 0.152 | 0.939 | 3.091 |
| microservices | kubernetes | 0.101 | 0.608 | 2.994 | 0.074 | 0.441 | 1.915 |
| azure | aws | 0.129 | 0.744 | 2.749 | 0.137 | 0.778 | 2.559 |
| aws, git | cicd | 0.101 | 0.787 | 2.498 | 0.137 | 0.966 | 2.940 |
| docker | cicd | 0.152 | 0.742 | 2.356 | 0.196 | 0.656 | 1.997 |
| api, git | cicd | 0.104 | 0.700 | 2.222 | 0.147 | 0.682 | 2.076 |
| git | cicd | 0.188 | 0.690 | 2.190 | 0.230 | 0.691 | 2.104 |
| kubernetes | aws | 0.116 | 0.573 | 2.117 | 0.147 | 0.638 | 2.100 |

## Nhận xét (Overfit / Rule drift)
Có 9/10 luật trong top 10 vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.

> **Hạn chế dữ liệu:** Dữ liệu thu thập là một snapshot các tin tuyển dụng còn active tính đến ngày 29/09. Do đó, việc chia Train/Test theo `posted_date` phản ánh sự khác biệt theo độ tuổi của tin (tin cũ vs tin mới đăng), chứ không hoàn toàn đo lường được sự thay đổi của thị trường theo thời gian dài.

## Top luật có kỹ năng data
Kỹ năng data dùng để lọc: airflow, bigquery, data_lake, data_modeling, data_pipeline, data_warehouse, databricks, dbt, deep_learning, etl, hadoop, kafka, machine_learning, numpy, pandas, power_bi, python, redshift, snowflake, spark, sql, statistics, tableau.

Số luật có kỹ năng data theo min_support (Train, lift > 1.2, confidence >= 0.5):
- min_support = 0.09: 2 luật
- min_support = 0.08: 3 luật
- min_support = 0.07: 7 luật
- min_support = 0.06: 17 luật

=> Chọn `min_support` = 0.06 (mức cao nhất cho ra ≥10 luật có kỹ năng data; nếu không có thì lấy mức nhiều luật nhất).

| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| redis | kafka | 0.061 | 0.674 | 6.380 | 0.103 | 0.656 | 4.057 |
| kafka | kubernetes | 0.074 | 0.700 | 3.449 | 0.064 | 0.394 | 1.710 |
| mssql | sql | 0.074 | 0.946 | 3.266 | 0.064 | 0.867 | 2.997 |
| cicd, sql | git | 0.068 | 0.711 | 2.607 | 0.059 | 0.706 | 2.118 |
| git, python | cicd | 0.061 | 0.725 | 2.302 | 0.098 | 0.690 | 2.100 |
| git, sql | api | 0.066 | 0.674 | 1.956 | 0.059 | 0.857 | 2.057 |
| cicd, sql | api | 0.063 | 0.667 | 1.935 | 0.064 | 0.765 | 1.835 |
| mysql | sql | 0.061 | 0.547 | 1.889 | 0.039 | 0.242 | 0.838 |
| kafka | api | 0.068 | 0.640 | 1.857 | 0.113 | 0.697 | 1.673 |
| communication, sql | api | 0.078 | 0.521 | 1.512 | 0.049 | 0.526 | 1.263 |

Có 8/10 luật data vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.