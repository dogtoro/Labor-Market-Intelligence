# WORKFLOW — Quy trình làm việc nhóm

## Branch & PR

- Branch đặt tên: `feat/<vai>-<mô-tả>`, ví dụ: `feat/crawler-sitemap`, `feat/parser-salary`.
- PR nhỏ, merge **trong ngày**. Cần **≥1 người review** (không phải người viết).
- Commit message tiếng Việt hoặc Anh đều được, miễn rõ ràng.

## Standup hằng ngày

- **Thời gian:** 21:00 mỗi tối (29/09 → 05/10).
- **Thời lượng:** 10 phút tối đa.
- Mỗi người ghi vào `docs/STANDUP.md` trước 21:00:
  1. Hôm nay **xong gì**
  2. Ngày mai **làm gì**
  3. Đang **kẹt gì** (nếu có)
- Nếu không họp được → vẫn phải ghi standup vào file.

## Quy tắc khi kẹt

- **Kẹt quá 2 tiếng** → báo nhóm ngay (chat hoặc tag trên Git), **không tự ôm**.
- Mô tả rõ: đang làm gì, kẹt ở đâu, đã thử gì.
- Người khác hỗ trợ hoặc swap task nếu cần.

## Sau Mốc 3 (tối 04/10)

- **Chỉ sửa lỗi** (bug fix), **KHÔNG thêm tính năng**.
- Mọi commit phải tag `[fix]` trong message.
- Slide + notebook + demo đã freeze, chỉ chỉnh typo/format.

## Lịch tổng quan

| Ngày | Mốc | Việc chính |
|------|-----|-----------|
| T3 29/09 | **Mốc 1 (tối)** | Đọc ToS, pilot 20 tin ITviec, Go/No-Go — **xong: Go ITviec** |
| T4 30/09 | | Crawl đầy đủ (qua đêm), parser, EDA draft — **crawl + parser + clean xong** (688 tin) |
| T5 01/10 | **Mốc 2 (tối)** | Freeze dữ liệu + SHA-256, quyết định decision tree — **xong: GIỮ DT (tertile)**; freeze + manifest: **xong** (`docs/MANIFEST.json`) |
| T6 02/10 | | Chạy model (Apriori, clustering, tree nếu giữ) |
| T7 03/10 | | Đánh giá, hình vẽ, bản nháp báo cáo |
| CN 04/10 | **Mốc 3 (tối)** | Slide + demo, khoá nội dung |
| T2 05/10 | | Tổng duyệt, sửa lỗi |
| T3 06/10 | 🎤 | **Present** |
