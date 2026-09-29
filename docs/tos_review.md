# TOS / robots.txt Review — Nguồn dữ liệu tuyển dụng

Người phụ trách: Người 1 (Crawler)
Ngày kiểm tra: 2026-09-29

## Mục lục

- Nguồn A — TopCV (dự kiến ban đầu): mục 1–4 → **kết luận: nghiêng về No-Go** (Cloudflare JS Challenge chặn toàn domain)
- Nguồn B — ITviec (phương án thay thế): mục 5–8 → **kết luận: Go về mặt kỹ thuật, có 1 điểm cần nhóm quyết định (khối lượng tin)**
- Khuyến nghị chung: mục 9

---

# Nguồn A — TopCV

## 1. robots.txt

Nguồn: `https://www.topcv.vn/robots.txt`

```
Sitemap: https://www.topcv.vn/sitemap.xml
Disallow: /cv/get-private-url/
Disallow: /private/
Disallow: /xem-cv/
Disallow: /xem-cv-draft/
Disallow: /sua-cv/
Disallow: /viet-cv/
Disallow: /edit/cv/
Disallow: /cv-ung-vien/
Disallow: /cv-ung-tuyen/
Disallow: /p/
Disallow: /v4/image/cv-template/cv-sample/toppy-list-mau-cv.png
```

**Nhận xét:**
- Toàn bộ các `Disallow` đều liên quan tới trang CV cá nhân / riêng tư (`/cv/`, `/xem-cv/`, `/sua-cv/`, `/viet-cv/`, `/cv-ung-vien/`, `/cv-ung-tuyen/`) và trang `/p/`. Đây là dữ liệu người dùng, dự án này không đụng tới.
- Path mục tiêu của dự án — trang danh sách tin IT/Data (`/tim-viec-lam-it-phan-mem-c10026`) và trang chi tiết tin — **không nằm trong danh sách bị chặn**.
- Có khai báo `Sitemap: https://www.topcv.vn/sitemap.xml` — đây là nguồn được site tự công bố cho crawler, khớp với "Đầu vào" trong `docs/tasks/crawler.md`.
- Không có dòng `Crawl-delay` — dự án tự đặt delay ≥3s theo `CLAUDE.md` mục 3, không phụ thuộc site có yêu cầu hay không.

**Kết luận robots.txt: KHÔNG có rào cản cho phạm vi crawl dự kiến (listing IT/Data + trang chi tiết tin + sitemap.xml).**

## 2. Điều khoản sử dụng (ToS)

Nguồn: `https://www.topcv.vn/terms-of-service` — **không đọc được**, công cụ fetch trả về HTTP 403 ngay
khi mở trang, nhiều khả năng cùng cơ chế Cloudflare đã chặn crawler (mục 3). Không còn nhiều ý nghĩa để
cố đọc thêm vì mục 3–4 đã đủ căn cứ kết luận No-Go bằng phương pháp hiện tại, không phụ thuộc nội dung ToS.

<!-- Nếu ai đó đọc được ToS này bằng trình duyệt thật, dán nguyên văn phần liên quan crawl/scrape/bot,
     bản quyền nội dung vào đây để hoàn thiện hồ sơ, dù không đổi kết luận No-Go kỹ thuật. -->

## 3. Sự cố kỹ thuật ghi nhận trong quá trình review (pilot 29/09)

**Lần 1–3 (14:41, 14:58, 15:01) — trang danh sách:**
```
Quét lấy link từ: https://www.topcv.vn/tim-viec-lam-it-phan-mem-c10026
ERROR - HTTP Status 403 trên trang danh sách
Hoàn thành Pilot: Lấy được 0 file HTML.
```

**Lần 4 (15:30) — chạy `python scripts/run_pipeline.py pilot`, log debug đầy đủ:**
```
ERROR - HTTP Status 403 on list page.
DEBUG - SERVER HEADERS: {..., 'Cf-Mitigated': 'challenge', 'Server': 'cloudflare',
  'Content-Security-Policy': "...script-src 'nonce-...' 'unsafe-eval' https://challenges.cloudflare.com;
  ...frame-src 'self' https://challenges.cloudflare.com blob:...", 'CF-RAY': 'a429a006be211a5b-HKG', ...}
DEBUG - SERVER RESPONSE BODY (first 500 chars):
<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>...
```

**Lần 5 (kiểm tra tay, không qua crawler.py) — `sitemap.xml`, path chính robots.txt công bố cho crawler:**
```
curl -H "User-Agent: USTH-FDS-Project/2026 (contact: ...)" https://www.topcv.vn/sitemap.xml
→ HTTP 403, cùng trang "Just a moment..." với Cf-Mitigated: challenge
```

**Chẩn đoán:**
- User-Agent dùng đúng format bắt buộc (`USTH-FDS-Project/2026 (contact: ...)`), không giả UA trình duyệt, delay 3.1s — không vi phạm `CLAUDE.md` mục 3.
- robots.txt không chặn cả 2 path đã thử (mục 1) → 403 không phải do site cấm crawl path này qua robots.txt.
- Header `Cf-Mitigated: challenge` + `Server: cloudflare` + trang "Just a moment..." + CSP trỏ `challenges.cloudflare.com` = **Cloudflare Managed/JS Challenge**, không phải chặn theo header đơn giản (Accept/Accept-Language). Đây là cơ chế yêu cầu trình duyệt thật thực thi JavaScript để lấy cookie `cf_clearance`; không thể vượt qua bằng cách thêm header với `requests`/`httpx`.
- Đã thử cả trang danh sách lẫn `sitemap.xml` (path robots.txt tự công bố cho crawler) — **cả hai đều bị challenge như nhau** → đây là chính sách chống bot áp dụng rộng cho traffic tự động vào toàn domain `www.topcv.vn`, không riêng 1 trang.
- **Không thử vượt qua Cloudflare challenge** (không dùng trình duyệt headless để tự giải JS challenge, không dùng thư viện giả lập TLS fingerprint, không dùng dịch vụ giải CAPTCHA/bypass bên thứ ba). Đây là biện pháp bảo mật chống bot TopCV chủ động triển khai; cố lách qua nằm ngoài phạm vi "UA trung thực" mà dự án cho phép.

## 4. Kết luận Go/No-Go

**Trạng thái: NGHIÊNG VỀ NO-GO với TopCV qua HTTP request thông thường — cần Trưởng nhóm quyết định.**

Điều kiện chốt Go (theo `docs/DECISIONS.md` mốc 1):
1. ToS không cấm — _chưa đọc được nội dung ToS (mục 2), nhưng không còn nhiều ý nghĩa nếu (3) fail_
2. HTML parse được — _không đạt: 0 file HTML lấy được sau 5 lần thử, mọi path đều bị Cloudflare challenge_
3. ≥1.000 tin IT/Data — _không đạt được bằng phương pháp hiện tại (`requests`/`httpx` + UA trung thực)_

**Bằng chứng then chốt:** cả trang danh sách và `sitemap.xml` (path robots.txt tự khai cho crawler) đều trả Cloudflare JS Challenge 403 cho client không chạy JavaScript. Đây là rào cản kỹ thuật cố ý của site, không phải lỗi cấu hình phía nhóm.

**Đề xuất:**
- [ ] Escalate lên Trưởng nhóm ngay tối 29/09 (đúng hạn mốc 1) — quyết định No-Go với TopCV bằng phương pháp `requests`/`httpx` hiện tại.
- [ ] Cân nhắc phương án hợp lệ khác, không phải "lách challenge": (a) tìm nguồn dữ liệu khác không có Cloudflare bot-management (kiểm tra lại A1–A3 trong `docs/ASSUMPTIONS.md` với site thay thế), (b) liên hệ TopCV xin quyền truy cập/API chính thức cho mục đích học thuật, hoặc (c) hỏi giảng viên hướng xử lý khi nguồn dữ liệu dự kiến chặn bot ở mức hạ tầng.
- [ ] Không tự ý triển khai trình duyệt headless / thư viện giả lập TLS để giải challenge — cần thảo luận nhóm + giảng viên trước, vì đây là ranh giới đạo đức/ToS khác hẳn "UA trung thực".

---

# Nguồn B — ITviec (phương án thay thế)

Kiểm tra ngày 29/09, ngay sau khi xác nhận TopCV nghiêng No-Go. Dùng đúng UA dự án
(`USTH-FDS-Project/2026 (contact: email@usth.edu.vn)`), delay thủ công ≥3s giữa các request
kiểm tra, không đăng nhập, không request nào tới path robots.txt chặn.

## 5. robots.txt

Nguồn: `https://itviec.com/robots.txt`

```
# Allow all bots to crawl the entire site except one page
User-Agent: *
Disallow: /subscriptions/new
User-Agent: *
Allow: /
Sitemap: https://itviec.com/dunggiatminh.xml
```

**Nhận xét:**
- Chỉ chặn duy nhất `/subscriptions/new`. Ngoài ra khai báo tường minh `Allow: /` — site **chủ động mời crawler** vào toàn bộ nội dung công khai, rõ ràng hơn cả TopCV (TopCV không có dòng `Allow` tường minh, chỉ suy ra từ việc thiếu `Disallow`).
- Sitemap khai ở path khác thường: `/dunggiatminh.xml` (không phải `/sitemap.xml` mặc định). Đã xác nhận path này hoạt động (mục 6).
- Không có `Crawl-delay` — vẫn áp dụng delay ≥3s theo `CLAUDE.md` mục 3 như đã làm khi test.

**Kết luận robots.txt: KHÔNG có rào cản, site còn tường minh cho phép crawl toàn site.**

## 6. Điều khoản sử dụng (ToS)

Nguồn: `https://itviec.com/blog/quy-che-hoat-dong-cua-itviec/` — "Quy chế hoạt động của ITviec", quy chế
chung toàn site (khác với `https://itviec.com/blog/dieu-khoan-dieu-kien-cua-khao-sat/` — điều khoản riêng
cho khảo sát, không liên quan).

**Trích nguyên văn 3 nhóm điều khoản liên quan (tất cả đều ghi rõ áp dụng cho "thành viên"/"ứng viên",
tức người đã đăng ký tài khoản — crawler dự án không đăng nhập, không tạo tài khoản):**

> **Mục V. Đảm bảo an toàn giao dịch:**
> "Ứng viên tuyệt đối không sử dụng bất kỳ chương trình, công cụ hay hình thức nào khác để can thiệp vào
> hệ thống hay làm thay đổi cấu trúc dữ liệu."
> "Nghiêm cấm việc phát tán, truyền bá hay cổ vũ cho bất kỳ hoạt động nào nhằm can thiệp, phá hoại hay
> xâm [nhập] của hệ thống website."

> **Mục X. Quyền và nghĩa vụ Ban quản trị:**
> "Website itviec.com giữ bản quyền mọi nội dung trên Website itviec.com theo các quy định pháp luật về
> bảo hộ sở hữu trí tuệ tại Việt Nam."
> "Nghiêm cấm mọi hành vi sao chép, sử dụng và phổ biến bất hợp pháp các quyền sở hữu trên."

> **Mục VIII/XI. Quyền và trách nhiệm thành viên:**
> "Thành viên không được thay đổi, chỉnh sửa, gán gép, copy, truyền bá, phân phối, cung cấp và tạo những
> công cụ tương tự do Website itviec.com cung cấp cho một bên thứ ba nếu không được sự đồng ý của
> Website itviec.com."

**Phân tích (không phải kết luận pháp lý cuối cùng — cần giảng viên/Trưởng nhóm quyết định):**

1. **Phạm vi áp dụng "thành viên":** Cả 3 nhóm điều khoản đều nằm trong mục ghi rõ áp dụng cho
   "thành viên"/"ứng viên" đã đăng ký. Crawler dự án chỉ gửi request công khai, không đăng nhập, không
   tạo tài khoản, không đồng ý điều khoản này ở bước nào (đúng `CLAUDE.md` mục 3: chỉ trang công khai,
   không đăng nhập). Về hình thức hợp đồng, có thể lập luận điều khoản không ràng buộc client ẩn danh —
   nhưng đây không phải kết luận chắc chắn, tuỳ cách diễn giải.
2. **Mâu thuẫn với robots.txt:** `robots.txt` (văn bản dành riêng cho bot, mục 5) ghi tường minh
   `Allow: /`, mời crawler vào. ToS (hướng tới thành viên) lại có ngôn ngữ rộng hơn cấm "công cụ... can
   thiệp hệ thống". Điều khoản "can thiệp hệ thống/thay đổi cấu trúc dữ liệu" đọc giống chống hack/tấn
   công/spam hơn là chống đọc dữ liệu công khai bằng request thông thường, nhưng không loại trừ hoàn
   toàn cách diễn giải ngược lại.
3. **Bản quyền nội dung** là điểm cần lưu ý nhất cho khâu báo cáo: lưu HTML thô (`data/raw/`) để phân
   tích nội bộ khác với **tái xuất bản nguyên văn JD** trong báo cáo/slide. Trích xuất kỹ năng/thống kê
   tổng hợp (không show lại toàn văn JD) là hình thức sử dụng khác hẳn sao chép/phổ biến, nhiều khả năng
   hợp lý cho mục đích học thuật phi thương mại — nhưng đây là câu hỏi pháp lý thật, không tự kết luận.
4. **Điều khoản cấm sao chép "công cụ tương tự"** — rõ ràng không áp dụng, dự án không xây sản phẩm
   cạnh tranh với ITviec.

**Kết luận mục 6: KHÔNG rõ ràng là Go hay No-Go.** Có tín hiệu trái chiều giữa robots.txt (mời crawl) và
ToS (ngôn ngữ rộng chống "công cụ", dù hướng tới thành viên). Cần escalate lên giảng viên/Trưởng nhóm —
đúng tình huống `docs/tasks/crawler.md` mục "Hỏi ai khi kẹt" đã dự trù.

## 7. Kiểm tra kỹ thuật (29/09, sau khi TopCV bị chặn)

Tất cả request dùng `curl -A "USTH-FDS-Project/2026 (contact: email@usth.edu.vn)"`, không có request nào tới path bị robots.txt chặn.

| # | URL | Kết quả | Ghi chú |
|---|-----|---------|---------|
| 1 | `https://itviec.com/` | HTTP 200, 358.769 B | Không có dấu hiệu Cloudflare (`Just a moment`, `cf-mitigated`, `__cf_chl`...) |
| 2 | `https://itviec.com/it-jobs` (trang danh sách) | HTTP 200, 529.933 chars | Chứa link tin thật ngay trong HTML thô, dạng `/it-jobs/<slug>-<công-ty>-<id>`, ví dụ `/it-jobs/agentic-engineer-python-go-c-c-backend-ai-agents-mb-bank-4137`. 127 phần tử có class chứa "company", 25 chỗ có text liên quan lương |
| 3 | `https://itviec.com/it-jobs/agentic-engineer-...-mb-bank-4137` (1 trang chi tiết tin) | HTTP 200, 349.215 chars | `<title>` = "Agentic Engineer (Python/Go/C/C++ Backend & AI Agents) at MB Bank \| ITviec"; có lương công khai ("2,000 USD") lẫn tin ẩn lương ("Sign in to view salary") — khớp giả định A4 (`docs/ASSUMPTIONS.md`) rằng chỉ một phần tin công khai lương |
| 4 | `https://itviec.com/dunggiatminh.xml` (sitemap index) | HTTP 200, 1.921 B | `<sitemapindex>` liệt kê 13 sitemap con, gồm `twinnings_jobs_desc_en.xml` / `_vn.xml` (JD tin), `twinnings_jobs_by_skill_*.xml`, `twinnings_companies_*.xml` |
| 5 | `https://itviec.com/twinnings_jobs_desc_en.xml` | HTTP 200, 157.094 B | Đếm được chính xác **673** thẻ `<loc>` — tức 673 tin IT đang active |

**Kết luận kỹ thuật:**
- **Không bị Cloudflare hay bất kỳ WAF nào chặn** — không giống TopCV.
- **HTML render sẵn phía server**: title, tên công ty, mô tả công việc, lương (khi công khai) đều nằm trong HTML thô lấy bằng `curl`/`requests`, không cần chạy JavaScript. Xác nhận đúng giả định A2 kiểu (site render server-side).
- **Có sitemap XML đếm được chính xác số tin**, không phải suy đoán qua pagination.

## 8. Kết luận Go/No-Go — ITviec

**Điều kiện 1 (ToS không cấm):** **KHÔNG RÕ RÀNG.** Đã đọc được ToS (mục 6) — không có lệnh cấm crawl
tường minh, nhưng có ngôn ngữ rộng ("công cụ... can thiệp hệ thống", "bản quyền nội dung") áp dụng cho
"thành viên", trong khi robots.txt lại mời crawler công khai. Cần giảng viên/Trưởng nhóm quyết định cách
diễn giải trước khi coi đây là "đạt".

**Điều kiện 2 (HTML parse được):** **ĐẠT.** Xác nhận trực tiếp bằng 5 request thật (mục 7), có title/công ty/lương/JD trong HTML thô.

**Điều kiện 3 (≥1.000 tin IT/Data):** **KHÔNG ĐẠT theo số tuyệt đối.** Sitemap đếm được **673 tin đang active**, thấp hơn ngưỡng 1.000 đặt ra ban đầu (`docs/ASSUMPTIONS.md` A3, `docs/tasks/crawler.md` DoD). Đây là hệ quả tự nhiên của việc chọn site **chuyên biệt IT** thay vì site đa ngành có category IT (TopCV) — ít tin hơn nhưng đúng phạm vi hơn, không lẫn tin ngành khác.

**Việc cần nhóm quyết định (không tự chốt):**
1. **Diễn giải ToS (mục 6):** chấp nhận lập luận "điều khoản chỉ ràng buộc thành viên đăng nhập, crawler ẩn danh không bị ràng buộc" hay coi ngôn ngữ "công cụ can thiệp hệ thống" là đủ rộng để tự loại trừ ITviec luôn. Khuyến nghị: hỏi giảng viên trước khi crawl full, vì đây là rủi ro pháp lý/đạo đức chứ không phải kỹ thuật.
2. Có chấp nhận hạ ngưỡng "≥1.000 tin" xuống mức thực tế (~673, có thể tăng nhẹ nếu gộp cả `twinnings_jobs_desc_vn.xml` nếu danh sách khác bản EN) hay không — 673 tin vẫn là cỡ mẫu hợp lý cho Apriori/Hierarchical Clustering ở quy mô đồ án môn học, nhưng đây là thay đổi so với con số đã ghi trong tài liệu nhóm, cần đồng thuận.
3. Có cần thử thêm 1 nguồn nữa (vd. `vietnamworks.com`, đã xác nhận HTTP 200 không Cloudflare ở mức trang chủ nhưng chưa đếm được khối lượng IT) để gộp cho đủ 1.000+, hay chấp nhận 673 là đủ.
4. Nếu Go: giới hạn báo cáo/slide chỉ dùng số liệu thống kê tổng hợp (skill counts, salary bins...), **không** tái xuất bản nguyên văn JD, để giảm rủi ro với điều khoản bản quyền (mục 6, điểm 3).

---

# 9. Khuyến nghị chung

| Tiêu chí | TopCV | ITviec |
|---|---|---|
| robots.txt | Không chặn path dự kiến | Không chặn, tường minh `Allow: /` |
| ToS | Không đọc được (site 403 khi fetch) | **Đã đọc — không rõ ràng.** Ngôn ngữ rộng chống "công cụ can thiệp hệ thống" + bản quyền nội dung, nhưng chỉ ghi áp dụng cho "thành viên" đăng nhập (crawler không đăng nhập) |
| Chặn bot (WAF) | **Có — Cloudflare JS Challenge toàn domain** | Không phát hiện |
| HTML parse được (không cần JS) | Không xác nhận được (0 file tải về) | **Có, xác nhận trực tiếp** |
| Số tin IT hiện có | Không đo được (bị chặn trước khi đếm) | **673** (đếm chính xác qua sitemap) |
| Phạm vi ngành | Đa ngành, lọc qua category `c10026` | Chuyên biệt IT |

**Đề xuất của Người 1:** chuyển sang `itviec.com` làm nguồn chính cho pilot 200–300 tin tiếp theo — đây là
nguồn duy nhất trong 2 lựa chọn thực sự crawl được bằng phương pháp hợp lệ của dự án (UA trung thực,
không giả trình duyệt, không login, không bypass WAF), và robots.txt mời crawl tường minh. Còn 2 điểm
nghẽn cần Trưởng nhóm/giảng viên quyết định trước khi Go hoàn toàn: (1) diễn giải ToS mục 6, (2) khối
lượng tin (673 < 1.000).

**Việc cần làm tiếp trước khi code crawler chính thức chuyển sang itviec.com:**
- [x] Đọc ToS itviec.com, điền mục 6 — xong, kết quả "không rõ ràng", cần người quyết định diễn giải
- [ ] Trưởng nhóm/giảng viên chốt mục 8 (điều kiện 1 và 3)
- [ ] Nếu Go: cập nhật `src/crawl/crawler.py` — đổi `BASE_URL`, đổi cách lấy URL tin sang dùng sitemap `twinnings_jobs_desc_*.xml` thay vì phân trang `/it-jobs?page=N` (ổn định hơn, có sẵn danh sách đầy đủ, đỡ tốn request dò trang)
- [x] Cập nhật `docs/ASSUMPTIONS.md` A1–A13 (đã thêm A10–A13 cho itviec.com/TopCV — xong)
- [ ] Ghi quyết định cuối vào `docs/DECISIONS.md` mốc 1 khi Trưởng nhóm chốt
