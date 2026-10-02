# Đánh giá Association Rules (Train vs Test)

## Kích thước tập dữ liệu
- Train: 5 bản ghi (70% tin cũ)
- Test: 3 bản ghi (30% tin mới)

## Top 10 luật kết hợp (theo Lift)
| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |
|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|
| docker, sql | git, english, python | 0.200 | 0.333 | 1.667 | 0.000 | 0.000 | 0.000 |
| git, english, python | docker, sql | 0.200 | 1.000 | 1.667 | 0.000 | 0.000 | 0.000 |
| docker, python | git, sql | 0.400 | 1.000 | 1.667 | 0.000 | 0.000 | 0.000 |
| docker, sql | git, python | 0.400 | 0.667 | 1.667 | 0.000 | 0.000 | 0.000 |
| git, python | docker, sql | 0.400 | 1.000 | 1.667 | 0.000 | 0.000 | 0.000 |
| git, sql | docker, python | 0.400 | 0.667 | 1.667 | 0.000 | 0.000 | 0.000 |
| git, sql | english, docker, python | 0.200 | 0.333 | 1.667 | 0.000 | 0.000 | 0.000 |
| english, docker, python | git, sql | 0.200 | 1.000 | 1.667 | 0.000 | 0.000 | 0.000 |
| docker, english, sql | git, python | 0.200 | 0.500 | 1.250 | 0.000 | 0.000 | 0.000 |
| git, english, sql | docker, python | 0.200 | 0.500 | 1.250 | 0.000 | 0.000 | 0.000 |

## Nhận xét (Overfit / Rule drift)
So sánh Support, Confidence, Lift giữa tập Train (dữ liệu cũ) và Test (dữ liệu mới) cho thấy liệu có sự thay đổi xu hướng tuyển dụng hay luật kết hợp bị overfit vào một thời điểm.