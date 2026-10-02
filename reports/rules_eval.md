# Đánh giá Association Rules (Train vs Test)

## Kích thước tập dữ liệu
- Train: 5 bản ghi (70% tin cũ)
- Test: 3 bản ghi (30% tin mới)

## Kết quả chạy Apriori trên các mức min_support khác nhau (Train)
- min_support = 0.03: tìm được 58 luật (lift > 1.2)
- min_support = 0.05: tìm được 58 luật (lift > 1.2)
- min_support = 0.1: tìm được 58 luật (lift > 1.2)

## Top 10 luật kết hợp (theo Lift, đã bỏ luật đối xứng)
| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| docker, sql | git, python | 0.400 | 0.667 | 1.667 | 0.000 | 0.000 | 0.000 |
| docker, python | sql, git | 0.400 | 1.000 | 1.667 | 0.000 | 0.000 | 0.000 |
| english, docker, python | sql, git | 0.200 | 1.000 | 1.667 | 0.000 | 0.000 | 0.000 |
| docker, sql | english, git, python | 0.200 | 0.333 | 1.667 | 0.000 | 0.000 | 0.000 |
| git, python | sql | 0.400 | 1.000 | 1.250 | 0.000 | 0.000 | 0.000 |
| python | sql | 0.600 | 1.000 | 1.250 | 0.333 | 0.500 | 1.500 |
| docker, git, python | sql | 0.400 | 1.000 | 1.250 | 0.000 | 0.000 | 0.000 |
| docker, python | git | 0.400 | 1.000 | 1.250 | 0.333 | 1.000 | 1.500 |
| docker | git, python | 0.400 | 0.500 | 1.250 | 0.333 | 0.500 | 1.500 |
| docker, sql | git | 0.600 | 1.000 | 1.250 | 0.000 | 0.000 | 0.000 |

## Nhận xét (Overfit / Rule drift)
Có sự sụt giảm về Lift trên tập Test so với tập Train (trung bình giảm 0.97). Hiện tượng rule drift có xuất hiện, cho thấy một số luật đã thay đổi theo thời gian hoặc bị overfit nhẹ vào tập Train.