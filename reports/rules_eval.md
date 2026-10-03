# Đánh giá Association Rules (Train vs Test)

## Kích thước tập dữ liệu
- Train: 473 bản ghi (70% tin cũ)
- Test: 204 bản ghi (30% tin mới)

## Lựa chọn tham số
- `min_confidence` = 0.5: Đảm bảo độ tin cậy của luật cao (ít nhất 50% khả năng kéo theo).
- `min_lift` = 1.2: Lọc các luật có tương quan tích cực rõ rệt.
Kết quả chạy Apriori trên các mức min_support khác nhau (Train):
- min_support = 0.03: tìm được 3227 luật
- min_support = 0.04: tìm được 1382 luật
- min_support = 0.05: tìm được 589 luật
- min_support = 0.06: tìm được 253 luật
- min_support = 0.1: tìm được 43 luật

=> Chọn `min_support` = 0.1 vì số lượng luật tìm được (43) nằm trong khoảng vừa phải (không quá ít để phân tích, không quá nhiều dẫn đến nhiễu).

## Top 10 luật kết hợp (theo Lift, mỗi tập kỹ năng chỉ giữ 1 luật)
| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| spring | java | 0.101 | 1.000 | 4.683 | 0.083 | 1.000 | 4.000 |
| kubernetes | docker | 0.133 | 0.656 | 3.200 | 0.167 | 0.723 | 2.419 |
| gcp | aws | 0.118 | 0.812 | 2.999 | 0.152 | 0.939 | 3.091 |
| microservices | kubernetes | 0.101 | 0.585 | 2.884 | 0.078 | 0.400 | 1.736 |
| azure | aws | 0.129 | 0.744 | 2.749 | 0.137 | 0.778 | 2.559 |
| api, docker | cicd | 0.101 | 0.800 | 2.540 | 0.132 | 0.614 | 1.868 |
| aws, git | cicd | 0.101 | 0.787 | 2.498 | 0.137 | 0.966 | 2.940 |
| docker | cicd | 0.152 | 0.742 | 2.356 | 0.196 | 0.656 | 1.997 |
| git | cicd | 0.188 | 0.690 | 2.190 | 0.230 | 0.691 | 2.104 |
| api, git | cicd | 0.121 | 0.687 | 2.180 | 0.157 | 0.667 | 2.030 |

## Nhận xét (Overfit / Rule drift)
Có 9/10 luật trong top 10 vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.

> **Hạn chế dữ liệu:** Dữ liệu thu thập là một snapshot các tin tuyển dụng còn active tính đến ngày 29/09. Do đó, việc chia Train/Test theo `posted_date` phản ánh sự khác biệt theo độ tuổi của tin (tin cũ vs tin mới đăng), chứ không hoàn toàn đo lường được sự thay đổi của thị trường theo thời gian dài.

## Top luật có ít nhất 1 kỹ năng data
Kỹ năng data dùng để lọc: airflow, bigquery, data_lake, data_modeling, data_pipeline, data_warehouse, databricks, dbt, deep_learning, etl, hadoop, kafka, machine_learning, numpy, pandas, power_bi, python, redshift, snowflake, spark, sql, statistics, tableau.

Số luật có kỹ năng data theo min_support (Train, lift > 1.2, confidence >= 0.5):
- min_support = 0.09: 7 luật
- min_support = 0.08: 7 luật
- min_support = 0.07: 13 luật

=> Chọn `min_support` = 0.07 (mức cao nhất cho ra ≥10 luật có kỹ năng data; nếu không có thì lấy mức nhiều luật nhất).

| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| kafka | kubernetes | 0.074 | 0.700 | 3.449 | 0.064 | 0.394 | 1.710 |
| mssql | sql | 0.074 | 0.946 | 3.266 | 0.064 | 0.867 | 2.997 |
| kafka | api | 0.078 | 0.740 | 1.651 | 0.123 | 0.758 | 1.561 |
| api, english, sql | communication | 0.072 | 0.680 | 1.517 | 0.044 | 0.529 | 1.403 |
| english, sql | communication | 0.110 | 0.642 | 1.432 | 0.064 | 0.448 | 1.188 |
| communication, sql | api | 0.093 | 0.620 | 1.383 | 0.059 | 0.632 | 1.301 |
| english, sql | api | 0.106 | 0.617 | 1.377 | 0.083 | 0.586 | 1.208 |
| sql | api | 0.171 | 0.591 | 1.319 | 0.162 | 0.559 | 1.153 |
| python | api | 0.125 | 0.541 | 1.208 | 0.191 | 0.591 | 1.218 |

Có 6/9 luật data vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.