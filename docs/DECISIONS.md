# NHẬT KÝ QUYẾT ĐỊNH

> Mỗi quyết định quan trọng ghi 1 dòng. Không xoá dòng cũ, chỉ thêm mới.

**Tóm tắt kết quả các mốc** (chi tiết ở các dòng bên dưới — bảng chỉ thêm dòng mới ở cuối, nên dòng kết quả nằm sau dòng kế hoạch):

| Mốc | Kết quả | Ngày |
|-----|---------|------|
| Mốc 1 — Go/No-Go crawl | **No-Go TopCV, GO ITviec** (kèm biện pháp ToS, chấp nhận <1.000 tin, dùng lương JSON-LD) | 29/09 tối |
| Mốc 2 — Freeze dữ liệu + Giữ/Bỏ Decision Tree | **GIỮ Decision Tree**, chia 3 lớp lương theo tertile. Freeze `jobs_clean.parquet` (688 dòng) + `docs/MANIFEST.json`: **xong**. `skill_matrix.parquet` thêm vào manifest khi Người 3 sinh | 01/10 |
| Mốc 3 — Khoá nội dung | _chưa đến_ | 04/10 tối |

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
| 30/09 | **Dữ liệu cuối cùng: 688 tin ITviec (crawl 21:22–22:19 29/09)** | Sitemap lúc crawl đầy đủ có 688 tin (pilot 16:41 có 681). Log `data/crawl_log.csv`: 691 request tới ITviec, 100% HTTP 200, delay nhỏ nhất 3,32s, 688 file HTML khớp 1–1 sitemap. Thay số 681 ở các dòng 29/09 bằng 688 cho mọi phân tích. HTML backup trên Drive, không commit. | Trưởng nhóm |
| 30/09 tối | **Dedup yêu cầu thêm JD giống ≥0,95; giữ bản đăng mới hơn** | Chỉ dùng tiêu đề (≥0,85) loại nhầm 4 tin khác nhau (vd. Mobile vs Backend Developer, Data Engineer vs AI Engineer) vì tiêu đề ITviec theo khuôn mẫu. Sau sửa: 0 tin trùng trên 688 tin (`reports/dedup_report.md`). | Người 2 (Trưởng nhóm review) |
| 01/10 | **Tỷ giá cố định 25.780 VND/USD; lương theo ngày × 20 ngày công; không điều chỉnh gross ↔ net** | Chi tiết và bằng chứng tại `docs/ASSUMPTIONS.md` A9, A14, A18. | Người 2 (Trưởng nhóm review) |
| 01/10 | **MỐC 2 — KẾT QUẢ: GIỮ Decision Tree; nhãn lương chia 3 lớp theo tertile thay ngưỡng cố định 15/30 triệu** | Cả 2 điều kiện Mốc 2 đạt: tỷ lệ tin có lương 172/688 = **25,0%** (≥25%); chia tertile được **Low 60 / Mid 55 / High 57** (≥50 mỗi lớp). Ngưỡng cố định 15/30 triệu chỉ cho 18 / 29 / 125 vì lương ITviec cao (trung vị ≈ 38 triệu). Quy ước: `salary_mid` = trung bình 2 cận với `full_range`, = cận duy nhất với `one_sided` (20 tin, ghi vào phần hạn chế). Ranh giới tertile (≈ 32,2 / 50,0 triệu trên dữ liệu 29/09) **phải tính bằng code từ dữ liệu**, không gõ tay. | Trưởng nhóm |
| 01/10 | **MỐC 2 — Freeze `data/processed/jobs_clean.parquet`** | File Người 2 upload Drive (688 dòng × 16 cột) qua `validate_clean()` và khớp 100% từng giá trị với bản Trưởng nhóm chạy lại từ code `main` (`3207964`). SHA-256 `4663b58857429318…` ghi trong `docs/MANIFEST.json`. Từ nay KHÔNG đổi schema (CLAUDE.md mục 4); mọi người tải đúng file này từ Drive và kiểm hash trước khi dùng. `make_manifest.py` bỏ qua file ẩn (`.gitkeep`) để hash tổng không lệch giữa Windows/Linux. | Trưởng nhóm |
