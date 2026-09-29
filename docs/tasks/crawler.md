# TASK BRIEF — Crawler (Người 1)

## Mục tiêu
Thu thập HTML thô từ ITviec cho tin tuyển dụng IT/Data, đảm bảo tuân thủ ToS + robots.txt. (Đổi từ TopCV tối 29/09 — `docs/DECISIONS.md`.)

## Đầu vào
- Sitemap ITviec `https://itviec.com/twinnings_jobs_desc_en.xml` (681 tin, 29/09)
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
| Crawl đầy đủ | Trưa 30/09 (chạy qua đêm) |
| Freeze dữ liệu + SHA-256 hash | Tối 01/10 (Mốc 2) |
| Viết governance.md | 03/10 |

## Definition of Done
- [x] `docs/tos_review.md` có trích dẫn cụ thể, kết luận rõ Go/No-Go (mục 10)
- [ ] `data/raw/` chứa HTML của toàn bộ tin trong sitemap (681 tin ngày 29/09; ngưỡng ≥1.000 đã hạ — DECISIONS 29/09)
- [ ] `crawl_log.csv` ghi đủ mọi request, delay ≥3s giữa các request
- [ ] User-Agent đúng format: `USTH-FDS-Project/2026 (contact: ...)`
- [ ] Không có request nào tới path bị robots.txt chặn
- [ ] SHA-256 hash khớp khi chạy lại `scripts/make_manifest.py`
- [ ] `docs/governance.md` đủ 4 mục

## Trạng thái 29/09 tối — Người 1 làm tiếp từ đây
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
