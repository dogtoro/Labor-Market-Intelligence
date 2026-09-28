# TASK BRIEF — Crawler (Người 1)

## Mục tiêu
Thu thập HTML thô từ TopCV cho tin tuyển dụng IT/Data, đảm bảo tuân thủ ToS + robots.txt.

## Đầu vào
- Sitemap TopCV (URL công khai)
- `CLAUDE.md` mục 3 (quy tắc crawl bắt buộc)

## Đầu ra

| File | Đường dẫn | Mô tả |
|------|-----------|-------|
| HTML thô | `data/raw/{job_id}.html` | Mỗi tin 1 file |
| Crawl log | `data/raw/crawl_log.csv` | Cột: url, job_id, status_code, timestamp, cached |
| ToS review | `docs/tos_review.md` | Kết luận Go/No-Go với trích dẫn |
| Governance | `docs/governance.md` | User-Agent, rate limit, ToS, backup |
| Manifest | `docs/MANIFEST.json` | Tạo bằng `python scripts/make_manifest.py` |

## Hạn chót

| Việc | Hạn |
|------|-----|
| Đọc ToS + crawl thử 200–300 tin | Tối 29/09 (Mốc 1) |
| Crawl đầy đủ | Trưa 30/09 (chạy qua đêm) |
| Freeze dữ liệu + SHA-256 hash | Tối 01/10 (Mốc 2) |
| Viết governance.md | 03/10 |

## Definition of Done
- [ ] `docs/tos_review.md` có trích dẫn cụ thể, kết luận rõ Go/No-Go
- [ ] `data/raw/` chứa ≥1.000 file HTML tin IT/Data
- [ ] `crawl_log.csv` ghi đủ mọi request, delay ≥3s giữa các request
- [ ] User-Agent đúng format: `USTH-FDS-Project/2026 (contact: ...)`
- [ ] Không có request nào tới path bị robots.txt chặn
- [ ] SHA-256 hash khớp khi chạy lại `scripts/make_manifest.py`
- [ ] `docs/governance.md` đủ 4 mục

## Lệnh test
```bash
pytest tests/ -v -k "contract"
python scripts/make_manifest.py
```
