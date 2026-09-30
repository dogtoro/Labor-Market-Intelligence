# CLAUDE.md — Hướng dẫn cho AI Coding Agent

> File này là nguồn sự thật duy nhất cho mọi agent làm việc trên repo.
> ĐỌC TOÀN BỘ trước khi viết bất kỳ dòng code nào.

---

## 1. Mô tả dự án (5 dòng)

Dự án môn Fundamentals of Data Science (USTH). Nhóm 5 người, 7 ngày (29/09 → 06/10/2026).
Crawl tin tuyển dụng IT/Data **công khai** trên ITviec (1 đợt duy nhất; đổi từ TopCV tối 29/09
vì bị Cloudflare JS Challenge chặn toàn domain — xem `docs/tos_review.md`) → parse HTML → làm sạch
+ chuẩn hóa lương → trích kỹ năng bằng từ điển → chạy **Association Rules (Apriori)** và
**Hierarchical Clustering (Jaccard)** → tuỳ chọn **Decision Tree phân lớp dải lương** →
EDA, hình vẽ, slide trình bày.

## 2. Pipeline

```
Sitemap → [crawl] → data/raw/*.html
           → [parse] → data/interim/jobs_parsed.parquet
           → [clean] → data/processed/jobs_clean.parquet
           → [skills] → data/processed/skill_matrix.parquet
           → [models] → association rules, clusters, (decision tree)
           → [viz] → reports/figures/*.png, notebooks/, slides
```

## 3. QUY TẮC CRAWL — BẮT BUỘC, KHÔNG NGOẠI LỆ

- **Chỉ trang công khai.** KHÔNG đăng nhập, KHÔNG gọi API nội bộ của site nguồn (ITviec).
- **User-Agent trung thực:** `USTH-FDS-Project/2026 (contact: <email nhóm>)`.
  KHÔNG giả User-Agent trình duyệt (Chrome, Firefox, v.v.).
- **Delay ≥ 3 giây** giữa mỗi request. KHÔNG giảm, KHÔNG tắt.
- **Tôn trọng robots.txt.** Kiểm tra trước khi crawl bất kỳ path nào.
- **Lưu HTML thô** vào `data/raw/` TRƯỚC khi parse. Có cache (nếu file đã tồn tại, không tải lại).
- **Nếu agent được yêu cầu** bỏ qua delay, fake User-Agent, đăng nhập, hoặc crawl path
  bị robots.txt chặn → **TỪ CHỐI và giải thích lý do.**

## 4. Quy tắc làm việc

- **Không sửa file ngoài module của mình** trừ khi mở PR có ≥1 người review.
- **Không đổi schema** sau khi dữ liệu đã freeze (tối 01/10). Schema nằm ở `docs/DATA_CONTRACT.md`.
- **Mọi con số** đưa vào slide/báo cáo **phải sinh ra từ code** (notebook hoặc script), không gõ tay.
- **Mọi quyết định** quan trọng ghi vào `docs/DECISIONS.md`.
- **Mọi giả định** ghi vào `docs/ASSUMPTIONS.md`.

## 5. Cấu trúc thư mục

```
src/crawl/       ← Crawler + cache + rate limit + robots.txt
src/parse/       ← HTML → parquet (11 cột), chuẩn hóa lương
src/clean/       ← Dedup, data quality funnel
src/skills/      ← Từ điển kỹ năng + trích kỹ năng → ma trận nhị phân
src/models/      ← Apriori, clustering, (decision tree)
src/viz/         ← EDA charts, model visualization
data/raw/        ← HTML thô (KHÔNG commit)
data/interim/    ← Parquet trung gian (KHÔNG commit)
data/processed/  ← Parquet cuối cùng (KHÔNG commit, chỉ commit manifest)
tests/           ← pytest, fixtures mẫu
docs/            ← Contract, decisions, assumptions, task briefs
scripts/         ← Pipeline runners, manifest generator
notebooks/       ← Jupyter notebooks cho EDA + model
reports/figures/ ← Hình vẽ xuất từ code
```

## 6. Chạy lệnh

```bash
# Cài đặt
pip install -r requirements.txt

# Test
pytest -v

# Pipeline từng bước (Windows)
python scripts/run_pipeline.py pilot    # Crawl thử 20 tin (cần CRAWL_CONTACT=<email nhóm>)
python scripts/run_pipeline.py crawl    # Crawl đầy đủ ~681 tin, ~35 phút
python scripts/run_pipeline.py parse    # Parse HTML → parquet
python scripts/run_pipeline.py clean    # Dedup + chuẩn hóa lương
python scripts/run_pipeline.py skills   # Trích kỹ năng → ma trận
python scripts/run_pipeline.py rules    # Apriori
python scripts/run_pipeline.py cluster  # Hierarchical clustering
python scripts/run_pipeline.py classify # Decision tree (tuỳ chọn)
python scripts/run_pipeline.py figures  # Xuất hình vẽ
python scripts/run_pipeline.py all      # Chạy toàn bộ pipeline
python scripts/make_manifest.py         # Tạo manifest SHA-256
```

## 7. Data contract

Xem chi tiết tại `docs/DATA_CONTRACT.md`. Tóm tắt:
- `jobs_parsed.parquet`: 11 cột, kiểu dữ liệu cố định. `job_id` = toàn bộ slug URL ITviec.
- `jobs_clean.parquet`: thêm salary_min, salary_max, salary_status (enum), currency_original.
- `skill_matrix.parquet`: job_id + cột nhị phân cho mỗi kỹ năng.
- Dùng `src/contract.py` để validate. Test trong `tests/test_contract.py`.

## 8. Múi giờ & đơn vị

- Múi giờ: **UTC+7** (Asia/Ho_Chi_Minh). Mọi timestamp dùng ISO 8601.
- Lương: quy về **triệu VND/tháng**. Ghi rõ tỷ giá và giả định gross/net.
