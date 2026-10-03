# A7 Evaluation — Độ phủ từ điển kỹ năng trên 20 JD ngẫu nhiên

Sinh bởi `scripts/verify_a7.py` (mẫu 20 JD, seed=2026). Nhãn tay ở `reports/a7_manual_labels_seed2026.csv`.

> **Bộ kiểm tra độc lập:** 20 JD không trùng mẫu seed=42; từ điển **không** được chỉnh theo bộ này, nên con số ở đây không bị thiên lệch do chọn alias.

- JD đã gán nhãn: **20/20**
- Tổng kỹ năng thực tế (nhãn tay): **266**
- Extractor bắt đúng: **193**
- **Độ phủ (micro): 72.6%** — ngưỡng A7: 80% → **CHƯA ĐẠT**

## Kỹ năng bị sót nhiều nhất

| Kỹ năng | Số JD bị sót |
|---|---|
| communication | 4 |
| api | 3 |
| ai_agents | 2 |
| android | 2 |
| bash | 2 |
| claude_code | 2 |
| codex | 2 |
| cursor | 2 |
| data_pipeline | 2 |
| delta_lake | 2 |
| github_actions | 2 |
| gitlab_ci | 2 |
| helm | 2 |
| kibana | 2 |
| opensearch | 2 |

## Chi tiết từng JD

| # | Vị trí (Công ty) | Nhãn tay | Bắt đúng | Độ phủ | Bị sót |
|---|---|---|---|---|---|
| 0 | Senior/Lead - Software Engineer (M_Service (MoMo)) | 26 | 16 | 62% | api; claude_code; clickhouse; codex; cursor; data_pipeline; grpc; hbase; microservices; vertx |
| 1 | Remote - Automation QA Lead (OrgScale Recruitment) | 6 | 5 | 83% | playwright |
| 2 | Chuyen vien Van hanh Ung dung Application Support L1 (CTCP SÀN GIAO DỊCH TÀI SẢN MÃ HÓA VIỆT NAM THỊNH VƯỢNG (CAEX)) | 5 | 4 | 80% | kibana |
| 3 | Technical Program Manager - MCA Asia (GoTymeX) | 7 | 7 | 100% |  |
| 4 | AI Lead - GenAI, RAG, AI Agents (FPT Digital) | 12 | 10 | 83% | ai_agents; api |
| 5 | Database Administrator OracleDB, MS SQL, PostgreSQL (Swisslog Vietnam) | 12 | 8 | 67% | bash; jboss; weblogic; wildfly |
| 6 | Chuyen gia tich hop du lieu Data Engineer Expert (PVcomBank) | 18 | 16 | 89% | flink; graph_db |
| 7 | Software Engineer C/C++/Java, Linux/ Android (IriTech Vietnam) | 11 | 7 | 64% | android; api; c; teamwork |
| 8 | DevOps/Platform Engineer (F88) | 24 | 18 | 75% | argocd; bash; gitlab_ci; gitops; helm; opensearch |
| 9 | Senior Golang Engineer Backend (NAB Innovation Centre Vietnam) | 4 | 3 | 75% | communication |
| 10 | AI Engineer (Ngân hàng TMCP Phương Đông | OCB) | 20 | 12 | 60% | ai_agents; communication; delta_lake; langgraph; llm; mlflow; triton; vllm |
| 11 | Techinical Lead .Net (VinSmart Future) | 11 | 11 | 100% |  |
| 12 | Backend Developer Java/ Golang/ NodeJS (Digital Innovation) | 18 | 16 | 89% | json; oracle_db |
| 13 | Cloud Security Engineer Expert (FE CREDIT) | 14 | 9 | 64% | cloudformation; communication; oci; powershell; vng_cloud |
| 14 | Backend Engineer Nodejs (Everfit) | 16 | 12 | 75% | express; jest; mocha; sqs |
| 15 | Remote Data Engineer - AI Data Platform Japan Python (SalesNow Co., Ltd.) | 32 | 19 | 59% | amazon_bedrock; claude_code; coderabbit; codex; cursor; data_pipeline; delta_lake; github_actions; github_copilot; opensearch; scrapy; vercel; web_scraping |
| 16 | DevOps Engineer Mid/Senior (Saigon Technology) | 16 | 11 | 69% | github_actions; gitlab_ci; helm; kibana; powershell |
| 17 | Technical SW Project Manager Embedded Automotive (Hella Vietnam) | 1 | 1 | 100% |  |
| 18 | Senior Flutter Software Engineer (EPOS Vietnam) | 7 | 3 | 43% | android; communication; flutter; jetpack |
| 19 | IT Quality Control Officer Manual Tester (IDEAL LIFE JSC – IZIon24) | 6 | 5 | 83% | postman |
