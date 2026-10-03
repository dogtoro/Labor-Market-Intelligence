# Phân Tích Thiên Lệch (Bias Analysis)

Báo cáo này phân tích sự khác biệt (thiên lệch) giữa nhóm tin có công bố lương (dùng để train Decision Tree) và nhóm không công bố lương.
- **Nhóm có lương (Train):** 172 tin
- **Nhóm không lương:** 516 tin

## 1. Thiên lệch theo Kỹ năng

Fisher exact cho 100 kỹ năng (xuất hiện ≥ 5 tin), hiệu chỉnh Benjamini–Hochberg. Không có kỹ năng nào khác biệt có ý nghĩa thống kê sau khi hiệu chỉnh bội (adj_p < 0.05). Dưới đây là top 15 kỹ năng có chênh lệch tuyệt đối lớn nhất:

| Kỹ năng | Có lương (%) | Không lương (%) | Chênh lệch (%) | p_value | adj_p_value |
|---|---|---|---|---|---|
| english | 49.4% | 56.4% | -7.0% | 0.1127 | 0.5365 |
| aws | 23.3% | 29.1% | -5.8% | 0.1678 | 0.5989 |
| azure | 12.8% | 18.6% | -5.8% | 0.0812 | 0.4778 |
| cicd | 27.3% | 32.8% | -5.4% | 0.2174 | 0.7013 |
| rag | 10.5% | 5.2% | +5.2% | 0.0206 | 0.4120 |
| postgresql | 20.3% | 15.7% | +4.7% | 0.1600 | 0.5989 |
| fastapi | 7.6% | 3.1% | +4.5% | 0.0161 | 0.4019 |
| teamwork | 15.7% | 11.4% | +4.3% | 0.1451 | 0.5989 |
| figma | 1.2% | 5.2% | -4.1% | 0.0258 | 0.4134 |
| japanese | 9.3% | 5.2% | +4.1% | 0.0682 | 0.4545 |
| jenkins | 5.2% | 9.3% | -4.1% | 0.1102 | 0.5365 |
| kotlin | 0.0% | 4.1% | -4.1% | 0.0036 | 0.3567 |
| python | 28.5% | 24.4% | +4.1% | 0.3123 | 0.8252 |
| test_automation | 10.5% | 14.5% | -4.1% | 0.1989 | 0.6630 |
| agile | 22.7% | 26.6% | -3.9% | 0.3639 | 0.8598 |

## 2. Thiên lệch theo Địa điểm

Multi-hot theo 3 thành phố chính và 'Khác' (một tin có thể ở nhiều nơi nên tổng % mỗi cột có thể > 100%). Fisher exact cho từng địa điểm, hiệu chỉnh Benjamini–Hochberg cho 4 phép kiểm định.

| Địa điểm | Có lương (%) | Không lương (%) | Chênh lệch (%) | p_value | adj_p_value |
|---|---|---|---|---|---|
| HCM | 47.7% | 66.5% | -18.8% | 0.0000 | 0.0001 |
| HN | 51.7% | 38.6% | +13.2% | 0.0032 | 0.0063 |
| DN | 4.1% | 5.2% | -1.2% | 0.6855 | 0.9140 |
| OTHER | 0.6% | 0.4% | +0.2% | 1.0000 | 1.0000 |

## 3. Thiên lệch theo Cấp bậc (Level)

Kiểm định Chi-Square test trên toàn bộ bảng chéo: p-value = 6.0407e-02

| Cấp bậc | Có lương | Có lương (%) | Không lương | Không lương (%) | Chênh lệch (%) |
|---|---|---|---|---|---|
| Intern/Junior | 17 | 9.9% | 37 | 7.2% | +2.7% |
| Lead | 12 | 7.0% | 54 | 10.5% | -3.5% |
| Manager | 18 | 10.5% | 42 | 8.1% | +2.3% |
| Middle | 11 | 6.4% | 15 | 2.9% | +3.5% |
| Senior | 52 | 30.2% | 138 | 26.7% | +3.5% |
| Unknown | 62 | 36.0% | 230 | 44.6% | -8.5% |

## 4. Đặc điểm nhóm có lương: tiền tệ (mô tả, không phải so sánh)

Tin không công bố lương không có thông tin tiền tệ, nên đây **không phải** phép so sánh 2 nhóm.

| Tiền tệ (`currency_original`) | Số tin |
|---|---|
| USD | 151 |
| VND | 21 |

151/172 tin có lương (87.8%) ghi bằng USD. **Giả thuyết (chưa kiểm chứng):** nhóm có lương có thể lệch về công ty nước ngoài/outsourcing; tuy nhiên ghi lương bằng USD cũng là cách hiển thị phổ biến trên ITviec, nên không suy ra được loại công ty.

## 5. Kết luận phạm vi áp dụng

Mô hình lương ở Task 3 chỉ học từ tin có công bố lương. So với tin không công bố lương:

1. **Địa điểm — có thiên lệch có ý nghĩa thống kê:** HCM 47.7% so với 66.5% (adj p = 0.0001); HN 51.7% so với 38.6% (adj p = 0.0063). Kết quả dự đoán lương vì vậy đại diện cho tin ở Hà Nội nhiều hơn so với thị trường chung.
2. **Kỹ năng — không có thiên lệch có ý nghĩa thống kê:** không kỹ năng nào có adj p < 0.05 (các chênh lệch trong bảng mục 1 chỉ là quan sát, không đủ bằng chứng).
3. **Cấp bậc — không khác biệt có ý nghĩa thống kê** (chi-square p = 0.0604 ≥ 0.05). Quan sát: tỷ lệ không suy được cấp bậc ở nhóm có lương thấp hơn (36.0% so với 44.6%), nhưng chưa đủ bằng chứng.
4. **Tiền tệ:** 87.8% tin có lương ghi USD — chỉ là đặc điểm mô tả (mục 4), không kết luận về loại công ty.

**Liên hệ với mô hình Task 3:** cây quyết định dựa chủ yếu vào cấp bậc, mà phân phối cấp bậc không khác biệt có ý nghĩa giữa 2 nhóm; nhưng địa điểm thì có. Vì vậy kết quả dự đoán lương nên được hiểu là đại diện cho tin có công bố lương, nghiêng về Hà Nội, chứ không phải toàn bộ thị trường.

