# A7 Evaluation — Độ phủ từ điển kỹ năng trên 20 JD ngẫu nhiên

Sinh bởi `scripts/verify_a7.py` (mẫu 20 JD, seed=42). Nhãn tay ở `reports/a7_manual_labels.csv`.

- JD đã gán nhãn: **20/20**
- Tổng kỹ năng thực tế (nhãn tay): **183**
- Extractor bắt đúng: **145**
- **Độ phủ (micro): 79.2%** — ngưỡng A7: 80% → **CHƯA ĐẠT**

## Kỹ năng bị sót nhiều nhất

| Kỹ năng | Số JD bị sót |
|---|---|
| communication | 5 |
| teamwork | 2 |
| airbyte | 1 |
| android_sdk | 1 |
| backstage | 1 |
| c | 1 |
| cicd | 1 |
| circleci | 1 |
| clickup | 1 |
| cypress | 1 |
| firebase | 1 |
| french | 1 |
| github_actions | 1 |
| gitlab_ci | 1 |
| haproxy | 1 |

## Chi tiết từng JD

| # | Vị trí (Công ty) | Nhãn tay | Bắt đúng | Độ phủ | Bị sót |
|---|---|---|---|---|---|
| 0 | Junior Android Developer Kotlin/Java (Motorist Pte Ltd) | 15 | 7 | 47% | android_sdk; firebase; jetpack_compose; junit; realm; retrofit; rxjava; sqlite |
| 1 | Technical Lead C#, .NET, Azure (MiTek Vietnam) | 13 | 10 | 77% | backstage; communication; github_actions |
| 2 | IT Comtor Japanese JLPT N2+ (ISV Vietnam) | 1 | 1 | 100% |  |
| 3 | Middle Data Engineer Apache Spark, Trino (IMIP Technology And Solution Consultancy) | 15 | 10 | 67% | airbyte; iceberg; microsoft_fabric; open_policy_agent; trino |
| 4 | Manual Tester QA/QC (MiTek Vietnam) | 6 | 6 | 100% |  |
| 5 | Fullstack Developer ReactJS, Angular, NodeJS, Python (CÔNG TY TNHH SOCOTEC VIỆT NAM) | 11 | 9 | 82% | communication; french |
| 6 | Software Engineering Manager C#, .Net, Azure (MiTek Vietnam) | 5 | 5 | 100% |  |
| 7 | Embedded Software Engineer MCU, RTOS (LG Electronics Development Vietnam (LGEDV)) | 10 | 7 | 70% | c; mcu; rtos |
| 8 | Senior Project Manager (TPIsoftware Co., Ltd) | 5 | 4 | 80% | teamwork |
| 9 | IT Business Analyst Fintech, English/ Mandarin (UNIT Corp) | 5 | 3 | 60% | communication; mandarin |
| 10 | Technical Program Manager (Vulcan Labs) | 2 | 2 | 100% |  |
| 11 | DevOps Engineer - Upto 3500 (Viettel Post (A Member of Viettel Group)) | 25 | 22 | 88% | gitlab_ci; haproxy; zabbix |
| 12 | Technical Business Analyst (Hitachi Digital Services) | 3 | 2 | 67% | communication |
| 13 | Business Analyst Japanese (Be A Racer) | 3 | 2 | 67% | teamwork |
| 14 | Thuc tap sinh lap trinh (Tinh Van Consulting) | 9 | 8 | 89% | vb_net |
| 15 | Senior Fullstack Engineer (Grab (Vietnam) Ltd.) | 14 | 14 | 100% |  |
| 16 | QA Specialist (AcceleratorApp) | 8 | 3 | 38% | clickup; communication; cypress; playwright; selenium |
| 17 | Junior Security Engineer (ZALORA Group) | 11 | 10 | 91% | cicd |
| 18 | System Engineer Server/Storage/SAN (SHINHAN DS) | 4 | 3 | 75% | san_storage |
| 19 | Principal Golang Engineer in /Hanoi (MONEY FORWARD VIETNAM CO.,LTD) | 18 | 17 | 94% | circleci |
