# GIẢ ĐỊNH CHƯA KIỂM CHỨNG

> ⚠️ **Đây là giả định, KHÔNG phải sự thật.** Cập nhật cột "Kết quả" ngay khi có dữ liệu.

| # | Giả định | Kiểm chứng bằng cách nào | Ai kiểm | Khi nào | Kết quả |
|---|----------|--------------------------|---------|---------|---------|
| A1 | ToS TopCV không cấm scraping dữ liệu công khai cho mục đích học thuật | Đọc ToS + robots.txt | Người 1 | Tối 29/09 | _chưa_ |
| A2 | TopCV render phía server (HTML thô chứa JD, không cần chạy JS) | Crawl thử 5 trang, mở bằng text editor, tìm JD | Người 1 | Tối 29/09 | _chưa_ |
| A3 | Có ≥1.000 tin IT/Data trên TopCV qua sitemap | Đếm URL trong sitemap thuộc danh mục IT | Người 1 | Tối 29/09 | _chưa_ |
| A4 | Tỷ lệ tin công khai lương ≥20–30% | Đếm trên 200 tin mẫu | Người 2 | Sáng 30/09 | _chưa_ |
| A5 | Trang tin tuyển dụng có trường danh mục nghề (category) trong HTML | Kiểm tra HTML mẫu | Người 2 | Sáng 30/09 | _chưa_ |
| A6 | Cấu trúc HTML đồng nhất giữa các tin (cùng CSS class) | Parse 200 tin, đếm tỷ lệ thành công | Người 2 | Sáng 30/09 | _chưa_ |
| A7 | ~100–200 kỹ năng phủ được ≥80% mention trong JD IT/Data | Đối chiếu từ điển v1 với 20 JD mẫu | Người 3 | Trưa 30/09 | _chưa_ |
| A8 | Lương chủ yếu ghi bằng VND hoặc USD | Đếm đơn vị tiền trên mẫu | Người 2 | Sáng 30/09 | _chưa_ |
| A9 | Tỷ giá USD/VND ổn định trong khoảng crawl, dùng 1 giá trị cố định là đủ | Tra tỷ giá Vietcombank ngày crawl | Người 2 | 01/10 | _chưa_ |
| A10 | robots.txt itviec.com không cấm crawl `/it-jobs/*` | Đọc robots.txt | Người 1 | 29/09 | **Đã kiểm — ĐÚNG.** `Allow: /`, chỉ chặn `/subscriptions/new`. Chi tiết: `docs/tos_review.md` mục 5 |
| A11 | itviec.com render phía server (HTML thô chứa JD, không cần chạy JS) | Crawl thử trang danh sách + 1 trang chi tiết bằng `curl` + UA thật, tìm title/công ty/lương/JD trong HTML thô | Người 1 | 29/09 | **Đã kiểm — ĐÚNG.** Title, tên công ty, lương (khi công khai) nằm sẵn trong HTML. Chi tiết: `docs/tos_review.md` mục 7 |
| A12 | Có ≥1.000 tin IT/Data trên itviec.com | Đếm thẻ `<loc>` trong sitemap `twinnings_jobs_desc_en.xml` | Người 1 | 29/09 | **Đã kiểm — SAI.** Chỉ 673 tin đang active. Cần Trưởng nhóm quyết định hạ ngưỡng hoặc bổ sung nguồn phụ. Chi tiết: `docs/tos_review.md` mục 7–8 |
| A13 | TopCV có thể crawl được bằng `requests`/`httpx` + UA trung thực | Pilot crawl trang danh sách + sitemap.xml | Người 1 | 29/09 | **Đã kiểm — SAI.** Toàn bộ domain bị chặn bởi Cloudflare JS Challenge (`Cf-Mitigated: challenge`), kể cả path robots.txt tự khai cho crawler. Không có cách hợp lệ để vượt qua trong phạm vi quy tắc dự án. Chi tiết: `docs/tos_review.md` mục 3–4 |
