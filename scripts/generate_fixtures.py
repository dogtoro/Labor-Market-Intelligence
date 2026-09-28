"""Generate sample parquet fixtures for tests — chạy 1 lần để tạo file fixture."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
FIXTURES.mkdir(parents=True, exist_ok=True)

# ── Tầng 2: Parsed ──────────────────────────────────────────────────────────
parsed_data = [
    {
        "job_id": "job-001",
        "url": "https://www.topcv.vn/viec-lam/senior-data-engineer-abc/001",
        "title": "Senior Data Engineer",
        "company": "ABC Technology",
        "level": "Senior",
        "location": "Hồ Chí Minh",
        "posted_date": "2026-09-15",
        "category": "Công nghệ thông tin",
        "salary_raw": "25 - 40 triệu",
        "jd_text": (
            "Xây dựng Data Pipeline trên AWS, sử dụng Apache Spark và Apache Airflow. "
            "Thiết kế Data Warehouse, viết ETL job bằng Python và SQL. "
            "Tối ưu query trên PostgreSQL và BigQuery. "
            "Làm việc với Docker và Kubernetes. "
            "Yêu cầu: thành thạo Python, SQL, Apache Spark, AWS hoặc GCP, "
            "Data Modeling, Data Governance, Git. Tiếng Anh giao tiếp tốt."
        ),
        "crawled_at": "2026-09-25T10:00:00+07:00",
    },
    {
        "job_id": "job-002",
        "url": "https://www.topcv.vn/viec-lam/junior-data-analyst-xyz/002",
        "title": "Junior Data Analyst",
        "company": "XYZ Corp",
        "level": "Junior",
        "location": "Hà Nội",
        "posted_date": "2026-09-18",
        "category": "Phân tích dữ liệu",
        "salary_raw": "Lên đến 2000 USD",
        "jd_text": (
            "Phân tích dữ liệu kinh doanh bằng SQL và Excel. "
            "Tạo báo cáo và dashboard trên Power BI. "
            "Hỗ trợ team Marketing đánh giá A/B Testing. "
            "Yêu cầu: SQL, Excel, Power BI, Python hoặc R. "
            "Kỹ năng giao tiếp và làm việc nhóm. TOEIC ≥ 600."
        ),
        "crawled_at": "2026-09-25T10:05:00+07:00",
    },
    {
        "job_id": "job-003",
        "url": "https://www.topcv.vn/viec-lam/ai-ml-engineer-def/003",
        "title": "AI/ML Engineer",
        "company": "DEF Solutions",
        "level": "Middle",
        "location": "Đà Nẵng",
        "posted_date": "2026-09-20",
        "category": "Trí tuệ nhân tạo",
        "salary_raw": "Thỏa thuận",
        "jd_text": (
            "Xây dựng mô hình Machine Learning và Deep Learning cho sản phẩm NLP. "
            "Triển khai model bằng TensorFlow hoặc PyTorch trên GCP. "
            "Xây dựng RAG pipeline sử dụng LangChain và Vector Database. "
            "Phát triển Generative AI features. "
            "Yêu cầu: Python, TensorFlow hoặc PyTorch, LLM, Generative AI, "
            "Docker, Git. Tiếng Anh đọc hiểu tài liệu kỹ thuật."
        ),
        "crawled_at": "2026-09-25T10:10:00+07:00",
    },
    {
        "job_id": "job-004",
        "url": "https://www.topcv.vn/viec-lam/backend-dev-ghi/004",
        "title": "Backend Developer (Java/Spring)",
        "company": "GHI Software",
        "level": "Senior",
        "location": "Hồ Chí Minh",
        "posted_date": "2026-09-10",
        "category": "Công nghệ thông tin",
        "salary_raw": "Từ 30 triệu",
        "jd_text": (
            "Phát triển backend bằng Java và Spring Boot. "
            "Thiết kế RESTful API và Microservices. "
            "Sử dụng PostgreSQL, Redis, Kafka. "
            "Triển khai trên Kubernetes với Docker. "
            "Yêu cầu: Java, Spring, SQL, Docker, Kubernetes, Git, "
            "CI/CD, Agile. Tiếng Anh giao tiếp."
        ),
        "crawled_at": "2026-09-25T10:15:00+07:00",
    },
    {
        "job_id": "job-005",
        "url": "https://www.topcv.vn/viec-lam/devops-engineer-jkl/005",
        "title": "DevOps Engineer",
        "company": "JKL Cloud",
        "level": "Middle",
        "location": "Hà Nội",
        "posted_date": "2026-09-12",
        "category": "Công nghệ thông tin",
        "salary_raw": "1,500 - 2,500 USD",
        "jd_text": (
            "Quản lý hạ tầng trên AWS và Azure. "
            "Xây dựng CI/CD pipeline bằng Jenkins. "
            "Sử dụng Docker, Kubernetes, Terraform, Ansible. "
            "Monitoring bằng Grafana và Elasticsearch. "
            "Yêu cầu: Linux, Bash, Docker, Kubernetes, Terraform, "
            "AWS, Azure, Jenkins, Git. Tiếng Anh tốt."
        ),
        "crawled_at": "2026-09-25T10:20:00+07:00",
    },
    {
        "job_id": "job-006",
        "url": "https://www.topcv.vn/viec-lam/data-analyst-abc/006",
        "title": "Data Analyst",
        "company": "ABC Technology",
        "level": "Junior",
        "location": "Hồ Chí Minh",
        "posted_date": "2026-09-16",
        "category": "Phân tích dữ liệu",
        "salary_raw": "15 - 25 triệu",
        "jd_text": (
            "Phân tích dữ liệu bằng SQL và Python. "
            "Tạo dashboard trên Tableau và Power BI. "
            "Thực hiện A/B Testing và Statistical Analysis. "
            "Yêu cầu: SQL, Python, Tableau, Power BI, Excel, "
            "Statistics. Tiếng Anh giao tiếp."
        ),
        "crawled_at": "2026-09-25T10:25:00+07:00",
    },
    {
        "job_id": "job-007",
        "url": "https://www.topcv.vn/viec-lam/fullstack-dev-mno/007",
        "title": "Full-Stack Developer",
        "company": "MNO Startup",
        "level": "Junior",
        "location": "Remote",
        "posted_date": "2026-09-22",
        "category": "Công nghệ thông tin",
        "salary_raw": "Cạnh tranh",
        "jd_text": (
            "Phát triển web app bằng React và Node.js. "
            "Thiết kế REST API, tích hợp MongoDB. "
            "Sử dụng TypeScript, HTML/CSS. "
            "Deploy trên AWS. "
            "Yêu cầu: JavaScript, TypeScript, React, Node.js, MongoDB, "
            "Git, Docker. Agile/Scrum."
        ),
        "crawled_at": "2026-09-25T10:30:00+07:00",
    },
    {
        "job_id": "job-008",
        "url": "https://www.topcv.vn/viec-lam/data-engineer-pqr/008",
        "title": "Data Engineer",
        "company": "PQR Analytics",
        "level": "Middle",
        "location": "Hồ Chí Minh",
        "posted_date": "2026-09-14",
        "category": "Công nghệ thông tin",
        "salary_raw": "30 - 50 triệu",
        "jd_text": (
            "Xây dựng Data Pipeline bằng Apache Spark và Airflow. "
            "Sử dụng Databricks và Snowflake. "
            "Viết ETL bằng Python và SQL. "
            "Quản lý Data Lake trên AWS. "
            "Yêu cầu: Python, SQL, Spark, Airflow, dbt, "
            "AWS, Docker, Git. Data Modeling."
        ),
        "crawled_at": "2026-09-25T10:35:00+07:00",
    },
]

# Thêm thêm 2 tin trùng lặp (để test dedup)
parsed_data.append({
    "job_id": "job-009",
    "url": "https://www.topcv.vn/viec-lam/senior-data-engineer-abc-v2/009",
    "title": "Senior Data Engineer",  # Same title as job-001
    "company": "ABC Technology",       # Same company as job-001
    "level": "Senior",
    "location": "Hồ Chí Minh",
    "posted_date": "2026-09-17",       # Within 7 days of job-001
    "category": "Công nghệ thông tin",
    "salary_raw": "25 - 40 triệu",
    "jd_text": parsed_data[0]["jd_text"],  # Same JD
    "crawled_at": "2026-09-25T10:40:00+07:00",
})

parsed_data.append({
    "job_id": "job-010",
    "url": "https://www.topcv.vn/viec-lam/senior-data-engineer-abc-v3/010",
    "title": "Sr. Data Engineer",  # Slightly different title
    "company": "ABC Technology",
    "level": "Senior",
    "location": "Hồ Chí Minh",
    "posted_date": "2026-09-19",
    "category": "Công nghệ thông tin",
    "salary_raw": "25 - 40 triệu",
    "jd_text": parsed_data[0]["jd_text"],
    "crawled_at": "2026-09-25T10:45:00+07:00",
})

df_parsed = pd.DataFrame(parsed_data)
df_parsed.to_parquet(FIXTURES / "sample_jobs_parsed.parquet", index=False)
print(f"✓ Tạo sample_jobs_parsed.parquet ({len(df_parsed)} dòng)")

# ── Tầng 3: Clean ───────────────────────────────────────────────────────────
# (chỉ 8 tin, bỏ 2 tin trùng)
clean_data = parsed_data[:8]  # không lấy 2 tin trùng
df_clean = pd.DataFrame(clean_data)

# Thêm cột clean
from src.parse.salary import parse_salary

salary_results = df_clean["salary_raw"].apply(parse_salary)
df_clean["salary_min"] = salary_results.apply(lambda r: r.salary_min).astype("float64")
df_clean["salary_max"] = salary_results.apply(lambda r: r.salary_max).astype("float64")
df_clean["salary_status"] = salary_results.apply(lambda r: r.salary_status)
df_clean["currency_original"] = salary_results.apply(lambda r: r.currency_original)
df_clean["is_duplicate"] = False

df_clean.to_parquet(FIXTURES / "sample_jobs_clean.parquet", index=False)
print(f"✓ Tạo sample_jobs_clean.parquet ({len(df_clean)} dòng)")

# ── Tầng 4: Skills Matrix ───────────────────────────────────────────────────
from src.skills.extractor import build_skill_matrix

df_skills = build_skill_matrix(df_clean, min_count=1)  # min_count=1 for fixture
df_skills.to_parquet(FIXTURES / "sample_skill_matrix.parquet", index=False)
skill_cols = [c for c in df_skills.columns if c != "job_id"]
print(f"✓ Tạo sample_skill_matrix.parquet ({len(df_skills)} dòng × {len(skill_cols)} kỹ năng)")

print("\n✅ Fixtures sẵn sàng.")
