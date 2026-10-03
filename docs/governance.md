# DATA GOVERNANCE — Crawl ITviec

> Người phụ trách: Người 1 (Crawler)
> Ngày tạo: 2026-10-03
> Cập nhật lần cuối: 2026-10-03 (tối — sửa số liệu theo `data/crawl_log.csv`, sửa cách kiểm tra toàn vẹn, bổ sung mục 5)

---

## 1. User-Agent

**Format bắt buộc** (CLAUDE.md mục 3):

```
USTH-FDS-Project/2026 (contact: <email thật của nhóm>)
```

- Email thật được truyền qua biến môi trường `CRAWL_CONTACT`.
- Crawler từ chối chạy nếu `CRAWL_CONTACT` không được đặt hoặc không chứa `@`
  (`src/crawl/crawler.py`, hàm `build_user_agent()`).
- **KHÔNG giả User-Agent trình duyệt** (Chrome, Firefox, v.v.) — đây là quy tắc bắt buộc
  không có ngoại lệ.

**Bằng chứng:** Xác nhận bởi Người 1 (01/10) — crawl pilot và crawl đầy đủ đều chạy với
`CRAWL_CONTACT` là email thật của nhóm. Log `data/crawl_log.csv` không ghi UA nhưng code
chỉ cho phép chạy khi UA đúng format.

---

## 2. Rate Limit

| Thông số | Giá trị |
|----------|---------|
| Delay tối thiểu giữa các request | **≥ 3.0 giây** (thực tế code đặt `DELAY = 3.1s`) |
| Cơ chế | `time.sleep()` trước mỗi request, tính từ lần request trước (`src/crawl/crawler.py`, hàm `get()`) |
| Crawl-delay từ robots.txt | Không có — ITviec không khai báo `Crawl-delay` |
| Delay nhỏ nhất ghi nhận trong log | **3,32 giây** trong lần crawl đầy đủ (29/09); **3,27 giây** nếu tính toàn bộ request ITviec (cả pilot) |
| Tổng request tới ITviec | **715 request** = pilot **24** (robots.txt, sitemap index, sitemap EN, sitemap VN, 20 trang tin) + crawl đầy đủ **691** (robots.txt ×2, sitemap EN, 688 trang tin) |
| Request trang tin | 708 request cho **688 URL khác nhau** — 20 trang của pilot được tải lại ở lần crawl đầy đủ (xem ghi chú cache bên dưới) |
| Tỷ lệ thành công | **100% HTTP 200** — không có request nào thất bại |
| Thời gian crawl đầy đủ | 21:22 → 22:19 ngày 29/09/2026 (~57 phút) |

**Cơ chế cache:** Nếu file HTML đã tồn tại trong `data/raw/`, crawler bỏ qua (không gửi
request mới). Điều này đảm bảo:
- Chạy lại **trong cùng thư mục `data/raw/`** không tạo thêm traffic cho site.
- File lấy từ cache **không** được log vào `crawl_log.csv` (vì không có request thật).

> ⚠️ Cache chỉ có tác dụng khi chạy lại ở cùng thư mục. Log cho thấy 20 trang tin của pilot
> bị tải lại khi crawl đầy đủ (708 request cho 688 URL), tức 2 lần chạy không dùng chung
> `data/raw/`. Lượng tải thêm nhỏ (20 request, vẫn giữ delay ≥ 3s) nhưng ghi nhận để minh bạch.

**Bằng chứng:** `data/crawl_log.csv` — 719 dòng dữ liệu = 4 request TopCV (HTTP 403, bị
Cloudflare chặn) + 715 request ITviec (24 pilot + 691 crawl đầy đủ), **tất cả ITviec HTTP 200**.

---

## 3. Tuân thủ Terms of Service (ToS) & robots.txt

### 3.1 robots.txt

**Nguồn:** `https://itviec.com/robots.txt`

```
# Allow all bots to crawl the entire site except one page
User-Agent: *
Disallow: /subscriptions/new
User-Agent: *
Allow: /
Sitemap: https://itviec.com/dunggiatminh.xml
```

- ITviec **tường minh cho phép** crawler truy cập toàn site (`Allow: /`), ngoại trừ
  `/subscriptions/new`.
- Crawler kiểm tra `robots.txt` **trước khi chạy** — nếu không đọc được thì dừng
  (`src/crawl/crawler.py`, constructor `ITviecCrawler`).
- Mỗi URL đều được kiểm tra qua `urllib.robotparser` trước khi gửi request
  (`fetch_cached()`, dòng 98).
- **Không có request nào** tới `/subscriptions/new` trong toàn bộ log.

### 3.2 Terms of Service

**Phân tích đầy đủ:** `docs/tos_review.md` (mục 1–10).

**Tóm tắt kết luận:**
- **TopCV:** No-Go — Cloudflare JS Challenge chặn toàn domain (mục 3–4).
- **ITviec:** Go kèm biện pháp — quy chế áp dụng cho "thành viên" đã đăng nhập; crawler
  ẩn danh chỉ đọc trang công khai mà robots.txt mời crawl (mục 5–8, 10).

**Biện pháp bắt buộc** (quyết định Trưởng nhóm, `docs/DECISIONS.md` 29/09):

| # | Biện pháp | Trạng thái |
|---|-----------|------------|
| 1 | Báo cáo/slide chỉ dùng số liệu tổng hợp (skill counts, salary bins…), **KHÔNG** trích nguyên văn JD | Áp dụng xuyên suốt |
| 2 | **KHÔNG** commit/chia sẻ HTML thô — chỉ lưu local + backup Google Drive (thư mục `Funny DS/raw`) | Đã thực hiện |
| 3 | UA có email thật của nhóm (`CRAWL_CONTACT`), delay ≥ 3s | Đã thực hiện |
| 4 | Không đăng nhập, không gọi API nội bộ, không request path bị chặn | Đã thực hiện |

---

## 4. Backup & Lưu trữ dữ liệu

### 4.1 HTML thô (`data/raw/`)

| Thuộc tính | Giá trị |
|------------|---------|
| Số file | **688** file `.html` (1 file / 1 tin tuyển dụng) |
| Naming | `{job_id}.html` — `job_id` = toàn bộ slug URL ITviec |
| Git | **KHÔNG commit** — file `.html` nằm trong `.gitignore` |
| Backup | Google Drive, thư mục `Funny DS/raw` |
| Khi nào | Ngay sau crawl đầy đủ (tối 29/09) |
| Hash tổng 688 file | `648765d9558b820b880f0367162a17701f1a86e7d04bc54fc8cf6396df8c44fc` — bản trên Drive (Trưởng nhóm tính 04/10). ⏳ Người 1 chạy cùng lệnh trên bản gốc để đối chiếu |

### 4.2 Crawl log (`data/crawl_log.csv`)

| Thuộc tính | Giá trị |
|------------|---------|
| Format | CSV, UTF-8 |
| Cột | `url`, `status`, `timestamp` (ISO 8601). 715 dòng ITviec có múi giờ `+07:00`; **4 dòng TopCV đầu tiên không có múi giờ** (ghi bởi bản crawler cũ) — giờ địa phương UTC+7 |
| Dòng | 719 dòng dữ liệu (không kể header) |
| Git | **Đã commit** — đây là bằng chứng tuân thủ rate limit |

### 4.3 Sitemap cache (`data/raw/_sitemaps/`)

| Thuộc tính | Giá trị |
|------------|---------|
| File | `jobs_desc_en.xml` — snapshot sitemap tại thời điểm crawl |
| Mục đích | Đảm bảo toàn bộ pipeline dùng cùng 1 snapshot; không bị ảnh hưởng bởi tin mới/xóa trên site |
| Cách lấy snapshot mới | Xóa thư mục `data/raw/_sitemaps/` trước khi chạy crawler |

### 4.4 Data freeze & Integrity

**File processed** (hash đầy đủ trong `docs/MANIFEST.json`):

| File | SHA-256 (prefix) | Ghi chú |
|------|-------------------|---------|
| `data/processed/jobs_clean.parquet` | `4663b588…` | 688 dòng — freeze tối 01/10 (Mốc 2) |
| `data/processed/skill_matrix.parquet` | `f87bb4a2…` | 677 dòng × 100 kỹ năng (sinh lại 03/10) |
| `data/processed/rules_train.csv` | `10f87bbb…` | Luật Apriori (03/10) |
| `data/processed/cluster_labels.csv` | `93644102…` | Thêm khi merge branch `zang` (03/10) |

- Dữ liệu freeze từ tối 01/10 (`docs/DECISIONS.md` Mốc 2).
- Schema không được thay đổi sau freeze (`CLAUDE.md` mục 4, `docs/DATA_CONTRACT.md`).

**Cách kiểm tra toàn vẹn** — ⚠️ **không** dùng `make_manifest.py` để kiểm tra: script này **ghi đè**
`MANIFEST.json`, nên so sánh sau đó luôn "khớp" kể cả khi dữ liệu đã bị thay. Dùng một trong hai cách:

```bash
# Cách 1: tính hash rồi so tay với docs/MANIFEST.json (không ghi file nào)
sha256sum data/processed/*.parquet data/processed/*.csv

# Cách 2: sinh lại manifest rồi xem git có báo thay đổi không — phải KHÔNG có diff
python scripts/make_manifest.py && git diff --exit-code docs/MANIFEST.json
```

Code dùng dữ liệu cho model (`src/models/features.py::load_and_verify_data`) tự kiểm hash
với `MANIFEST.json` và dừng nếu lệch.

**HTML thô** — hash tổng của bản trên Drive đã ghi ở bảng 4.1 (04/10). Người 1 chạy lệnh dưới đây trên bản gốc;
kết quả phải trùng. Lưu ý: 688 file đều xuống dòng kiểu CRLF (crawl trên Windows) — crawl lại trên Linux sẽ ra hash khác:

```bash
# Hash từng file (lưu làm bằng chứng) + hash tổng (sắp theo tên để ổn định giữa các máy)
# LC_ALL=C: thứ tự sắp xếp không phụ thuộc locale (locale khác có thể bỏ qua dấu '-' khi sắp xếp)
find data/raw -maxdepth 1 -name '*.html' | LC_ALL=C sort | xargs sha256sum > raw_html_sha256.txt
wc -l raw_html_sha256.txt          # phải là 688
sha256sum raw_html_sha256.txt      # hash tổng
```

---

## 5. Quyền truy cập, thời hạn lưu trữ & dữ liệu cá nhân

| Hạng mục | Quy định |
|----------|----------|
| Quyền truy cập Drive `Funny DS/raw` | Chỉ 5 thành viên nhóm (+ giảng viên nếu được yêu cầu). ⏳ **Người 1 xác nhận** danh sách người có quyền và chế độ chia sẻ (không bật "Anyone with the link") |
| Kiểm tra sau khi backup | Sau khi tải HTML lên/về Drive, chạy lại lệnh hash ở mục 4.4 và so với hash tổng đã ghi — bản tải về từ Drive đã có hash (bảng 4.1); ⏳ còn đối chiếu với bản gốc của Người 1 |
| Thời hạn lưu trữ | HTML thô chỉ dùng cho môn học; **xoá khỏi Drive và máy cá nhân sau khi có điểm môn học**. `crawl_log.csv`, `MANIFEST.json` và số liệu tổng hợp được giữ trong repo |
| Dữ liệu cá nhân | JD có thể chứa tên, email, số điện thoại của người tuyển dụng. Không trích nguyên văn JD, không công bố thông tin liên hệ trong báo cáo/slide; các file nhãn (vd. `reports/a7_manual_labels*.csv`) chỉ chứa tên vị trí, công ty và tên kỹ năng |

---

## Tài liệu tham chiếu

| Tài liệu | Đường dẫn | Nội dung |
|-----------|-----------|----------|
| Quy tắc crawl | `CLAUDE.md` mục 3 | Quy tắc bắt buộc cho mọi agent |
| ToS review | `docs/tos_review.md` | Phân tích ToS + robots.txt TopCV & ITviec |
| Quyết định | `docs/DECISIONS.md` | Lịch sử mọi quyết định quan trọng |
| Data contract | `docs/DATA_CONTRACT.md` | Schema các tầng dữ liệu |
| Giả định | `docs/ASSUMPTIONS.md` | Danh sách giả định + kết quả kiểm chứng |
| Manifest | `docs/MANIFEST.json` | SHA-256 hash các file processed |
