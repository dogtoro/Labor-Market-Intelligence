# NHẬT KÝ QUYẾT ĐỊNH

> Mỗi quyết định quan trọng ghi 1 dòng. Không xoá dòng cũ, chỉ thêm mới.

| Ngày | Quyết định | Lý do | Ai chốt |
|------|-----------|-------|---------|
| 29/09 tối | **MỐC 1 — Go / No-Go crawl** | Kiểm tra: (1) ToS TopCV không cấm, (2) HTML parse được, (3) ≥1.000 tin IT/Data. Nếu bất kỳ điều kiện fail → dừng, báo giảng viên, đổi nguồn. | Trưởng nhóm + Người 1 |
| 01/10 tối | **MỐC 2 — Freeze dữ liệu + Giữ/Bỏ Decision Tree** | Freeze `data/processed/`, tạo SHA-256 manifest. Quyết định giữ model phân lớp lương nếu: tỷ lệ tin có lương ≥25% VÀ mỗi class ≥50 mẫu. Ghi lý do vào đây. | Cả nhóm |
| 04/10 tối | **MỐC 3 — Khoá nội dung** | Không thêm tính năng. Chỉ sửa lỗi, chỉnh slide. Freeze slide + notebook. | Cả nhóm |
| 29/09 tối | **MỐC 1 — KẾT QUẢ: No-Go TopCV, GO ITviec** | TopCV bị Cloudflare JS Challenge chặn toàn domain, không có cách vượt hợp lệ (`docs/tos_review.md` mục 3–4). ITviec: robots.txt `Allow: /`, HTML render phía server, pilot 20 tin 24/24 request HTTP 200 (`docs/tos_review.md` mục 10). Giảng viên giao nhóm toàn quyền quyết định. | Trưởng nhóm |
| 29/09 tối | **Diễn giải ToS ITviec: Go kèm biện pháp** | Quy chế ITviec ghi áp dụng cho "thành viên"; crawler không đăng nhập, không tạo tài khoản; robots.txt mời crawl tường minh. Biện pháp bắt buộc: (1) báo cáo/slide chỉ dùng số liệu tổng hợp, KHÔNG trích nguyên văn JD; (2) KHÔNG commit/chia sẻ HTML thô; (3) UA có email thật của nhóm (`CRAWL_CONTACT`), delay ≥3s. | Trưởng nhóm |
| 29/09 tối | **Hạ ngưỡng khối lượng: chấp nhận toàn bộ sitemap (681 tin ngày 29/09) thay cho ≥1.000** | ITviec chuyên biệt IT nên ít tin hơn nhưng đúng phạm vi. Sitemap VN trùng 100% EN → không tăng được. Thêm nguồn thứ 2 không khả thi trong 7 ngày. Đủ cho Apriori + HAC ở quy mô đồ án; ghi vào phần hạn chế. | Trưởng nhóm |
| 29/09 tối | **Dùng lương từ JSON-LD `baseSalary`** | Giao diện ẩn lương ("Sign in to view salary") ở 20/20 tin pilot, nhưng 5/20 tin có lương trong JSON-LD `JobPosting` — dữ liệu ITviec tự nhúng vào HTML công khai cho máy đọc (Google Jobs), không cần đăng nhập. Chỉ dùng tổng hợp; ghi rõ nguồn trong báo cáo. Giá trị `"You'll love it"` = `undisclosed`. | Trưởng nhóm |
| 29/09 tối | **`job_id` = toàn bộ slug URL** | 4 chữ số cuối URL KHÔNG unique (681 tin chỉ 612 đuôi khác nhau). | Trưởng nhóm |
| 29/09 tối | **`posted_date` lấy từ JSON-LD `datePosted`** | Dòng "Posted X ago" trên giao diện lệch với `datePosted` (tin được đẩy lại); `<lastmod>` sitemap chỉ là giờ sinh sitemap. | Trưởng nhóm |
| 29/09 tối | **`category` = trường "Job Expertise"** | Có ở 20/20 tin pilot, ~15 giá trị/20 tin → cần gộp thành 6–8 nhóm nghề khi tính purity (Người 4 đề xuất bảng gộp, ghi vào ASSUMPTIONS). | Trưởng nhóm |
| 30/09 tối | **Layer 3 loại vật lý bản ghi trùng; các hàng được giữ có `is_duplicate = False`** | Các bản ghi xác định là trùng bị loại khỏi `jobs_clean.parquet`; cột `is_duplicate` vẫn giữ để tương thích Data Contract. Báo cáo dedup ghi tiêu chí và số lượng bị loại. | Người 2 |
