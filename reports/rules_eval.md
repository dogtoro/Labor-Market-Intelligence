# Đánh giá Association Rules (Train vs Test)

## Kích thước tập dữ liệu
- Train: 470 bản ghi (70% tin cũ)
- Test: 202 bản ghi (30% tin mới)

## Lựa chọn tham số
- `min_confidence` = 0.5: Đảm bảo độ tin cậy của luật cao (ít nhất 50% khả năng kéo theo).
- `min_lift` = 1.2: Lọc các luật có tương quan tích cực rõ rệt.
Kết quả chạy Apriori trên các mức min_support khác nhau (Train):
- min_support = 0.03: tìm được 1984 luật
- min_support = 0.04: tìm được 848 luật
- min_support = 0.05: tìm được 412 luật
- min_support = 0.06: tìm được 169 luật
- min_support = 0.1: tìm được 30 luật

=> Chọn `min_support` = 0.1 vì số lượng luật tìm được (30) nằm trong khoảng vừa phải (không quá ít để phân tích, không quá nhiều dẫn đến nhiễu).

## Top 10 luật kết hợp (theo Lift, đã bỏ luật đối xứng)
| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| kubernetes | docker | 0.134 | 0.649 | 3.083 | 0.168 | 0.739 | 2.531 |
| microservices | kubernetes | 0.102 | 0.615 | 2.982 | 0.074 | 0.429 | 1.882 |
| gcp | aws | 0.123 | 0.817 | 2.953 | 0.144 | 0.935 | 3.149 |
| azure | aws | 0.132 | 0.747 | 2.701 | 0.134 | 0.771 | 2.597 |
| git, docker | cicd | 0.100 | 0.825 | 2.567 | 0.158 | 0.780 | 2.426 |
| git, cicd | docker | 0.100 | 0.522 | 2.479 | 0.158 | 0.696 | 2.382 |
| git, aws | cicd | 0.104 | 0.790 | 2.460 | 0.134 | 0.964 | 2.997 |
| cicd, aws | git | 0.104 | 0.653 | 2.380 | 0.134 | 0.771 | 2.292 |
| cicd, docker | git | 0.100 | 0.644 | 2.346 | 0.158 | 0.821 | 2.437 |
| docker | cicd | 0.155 | 0.737 | 2.295 | 0.193 | 0.661 | 2.054 |

## Nhận xét (Overfit / Rule drift)
Có 10/10 luật trong top 10 vẫn đạt ngưỡng lift > 1.2 trên tập Test.

> **Hạn chế dữ liệu:** Dữ liệu thu thập là một snapshot các tin tuyển dụng còn active tính đến ngày 29/09. Do đó, việc chia Train/Test theo `posted_date` phản ánh sự khác biệt theo độ tuổi của tin (tin cũ vs tin mới đăng), chứ không hoàn toàn đo lường được sự thay đổi của thị trường theo thời gian dài.