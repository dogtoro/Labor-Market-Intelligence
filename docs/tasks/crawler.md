# TASK BRIEF — Crawler (Người 1)

## Mục tiêu
Thu thập HTML thô từ ITviec cho tin tuyển dụng IT/Data, đảm bảo tuân thủ ToS + robots.txt. (Đổi từ TopCV tối 29/09 — `docs/DECISIONS.md`.)

## Đầu vào
- Sitemap ITviec `https://itviec.com/twinnings_jobs_desc_en.xml` (688 tin lúc crawl đầy đủ 21:22 29/09; pilot 16:41 có 681)
- `CLAUDE.md` mục 3 (quy tắc crawl bắt buộc)

## Đầu ra

| File | Đường dẫn | Mô tả |
|------|-----------|-------|
| HTML thô | `data/raw/{job_id}.html` | Mỗi tin 1 file |
| Crawl log | `data/crawl_log.csv` (được commit làm bằng chứng) | Cột: url, status, timestamp (ISO 8601, UTC+7). Mọi request thật đều được log; file lấy từ cache không sinh request nên không log |
| ToS review | `docs/tos_review.md` | Kết luận Go/No-Go với trích dẫn |
| Governance | `docs/governance.md` | User-Agent, rate limit, ToS, backup |
| Manifest | `docs/MANIFEST.json` | Tạo bằng `python scripts/make_manifest.py` |

## Hạn chót

| Việc | Hạn |
|------|-----|
| Đọc ToS + crawl thử (pilot 20 tin) | Tối 29/09 (Mốc 1) — **xong** |
| Crawl đầy đủ | Trưa 30/09 — **xong tối 29/09** (21:22–22:19) |
| Freeze dữ liệu + SHA-256 hash | Tối 01/10 (Mốc 2) |
| Viết governance.md | 03/10 |

## Definition of Done
- [x] `docs/tos_review.md` có trích dẫn cụ thể, kết luận rõ Go/No-Go (mục 10)
- [x] `data/raw/` chứa HTML của toàn bộ tin trong sitemap — 688/688 file (ngưỡng ≥1.000 đã hạ — DECISIONS 29/09)
- [x] `crawl_log.csv` ghi đủ mọi request, delay ≥3s giữa các request — 691 request ITviec, 100% HTTP 200, delay nhỏ nhất 3,32s (log gộp pilot + crawl đầy đủ, 719 dòng)
- [x] User-Agent đúng format: `USTH-FDS-Project/2026 (contact: ...)` — log không ghi UA; Người 1 xác nhận (01/10) đã chạy với `CRAWL_CONTACT` là email thật của nhóm
- [x] Không có request nào tới path bị robots.txt chặn (chỉ `/subscriptions/new` bị chặn; log không có path này)
- [ ] SHA-256 hash khớp khi chạy lại `scripts/make_manifest.py`
- [ ] `docs/governance.md` đủ 4 mục

## Trạng thái 01/10
- Crawl đầy đủ **xong** tối 29/09: 688 tin, HTML backup trên Drive (`Funny DS/raw`), log đã gộp vào `data/crawl_log.csv` trên `main`.
- Manifest `jobs_clean.parquet` đã tạo ở Mốc 2 (01/10, `docs/MANIFEST.json`). Còn lại: chạy lại `python scripts/make_manifest.py` khi Người 3 thêm `skill_matrix.parquet`; `docs/governance.md` (03/10).

## Trạng thái 29/09 tối (lịch sử)
- `src/crawl/crawler.py` đã viết lại cho ITviec (sitemap EN, `job_id` = slug, cache cả sitemap, log UTC+7,
  không đọc được robots.txt → dừng). 20 tin pilot đã nằm trong `data/raw/` **trên máy Trưởng nhóm** —
  máy khác chạy pilot sẽ tải lại 20 tin đó (cùng seed 2026).
- **Bắt buộc** đặt `CRAWL_CONTACT=<email thật của nhóm>` — thiếu thì crawler từ chối chạy.
- Việc tiếp theo:
  1. `CRAWL_CONTACT=... python scripts/run_pipeline.py crawl` (~681 tin × 3.1s ≈ 35 phút). Sitemap được cache ở
     `data/raw/_sitemaps/` → cả đợt dùng 1 snapshot; muốn lấy snapshot mới thì xoá thư mục này **trước** khi chạy.
  2. Kiểm tra: số file HTML = số `<loc>` trong sitemap; mọi dòng log mới là HTTP 200.
  3. Backup `data/raw/` lên Google Drive (không commit).
  4. `docs/governance.md` (03/10).

## Lệnh test
```bash
pytest tests/ -v -k "contract"
python scripts/make_manifest.py
```
