"""
Tests for skill extraction.
"""

import pytest
from src.skills.extractor import load_skill_dict, _build_patterns, extract_skills, build_skill_matrix
import pandas as pd


@pytest.fixture
def skill_dict():
    """Một từ điển nhỏ để test."""
    return {
        "python": ["Python", "python3"],
        "sql": ["SQL", "T-SQL", "PL/SQL"],
        "power_bi": ["Power BI", "PowerBI", "Power-BI"],
        "docker": ["Docker", "docker"],
        "aws": ["AWS", "Amazon Web Services"],
        "react": ["React", "ReactJS", "React.js"],
        "spring": ["Spring", "Spring Boot", "SpringBoot"],
        "excel": ["Excel", "Microsoft Excel", "MS Excel"],
        "kubernetes": ["Kubernetes", "K8s", "k8s"],
        "computer_vision": ["Computer Vision", "OpenCV"],
    }


@pytest.fixture
def patterns(skill_dict):
    return _build_patterns(skill_dict)


class TestExtractSkills:
    def test_basic_match(self, patterns):
        text = "Yêu cầu: thành thạo Python và SQL."
        result = extract_skills(text, patterns)
        assert result["python"] == 1
        assert result["sql"] == 1
        assert result["docker"] == 0

    def test_alias_match(self, patterns):
        """Alias phải match."""
        text = "Sử dụng PowerBI để tạo dashboard."
        result = extract_skills(text, patterns)
        assert result["power_bi"] == 1

    def test_alias_with_space(self, patterns):
        """Power BI (có space) phải match."""
        text = "Kinh nghiệm Power BI là lợi thế."
        result = extract_skills(text, patterns)
        assert result["power_bi"] == 1

    def test_case_insensitive(self, patterns):
        text = "kinh nghiệm PYTHON và docker."
        result = extract_skills(text, patterns)
        assert result["python"] == 1
        assert result["docker"] == 1

    def test_no_match(self, patterns):
        text = "Tìm kiếm nhân viên kế toán có kinh nghiệm lập kế hoạch."
        result = extract_skills(text, patterns)
        assert result["python"] == 0
        assert result["sql"] == 0

    def test_multiple_skills(self, patterns):
        text = "Cần biết Python, SQL, Docker, AWS, React."
        result = extract_skills(text, patterns)
        assert result["python"] == 1
        assert result["sql"] == 1
        assert result["docker"] == 1
        assert result["aws"] == 1
        assert result["react"] == 1

    def test_amazon_web_services_alias(self, patterns):
        text = "Triển khai trên Amazon Web Services."
        result = extract_skills(text, patterns)
        assert result["aws"] == 1

    def test_feedback_cases(self, patterns):
        # Experience with Python: 3 years
        text1 = "Experience with Python: 3 years"
        result1 = extract_skills(text1, patterns)
        assert result1["python"] == 1

        # Python-based tools
        text2 = "Python-based tools"
        result2 = extract_skills(text2, patterns)
        assert result2["python"] == 1

        # "Docker" and K8s
        text3 = '"Docker" and K8s'
        result3 = extract_skills(text3, patterns)
        assert result3["docker"] == 1
        assert result3["kubernetes"] == 1

        # candidate must be in CV review
        text4 = "candidate must be in CV review"
        result4 = extract_skills(text4, patterns)
        assert result4["computer_vision"] == 0

    def test_react_case_sensitive(self, patterns):
        """React (viết hoa) là framework, react (viết thường) là động từ."""
        # Phải bắt được
        assert extract_skills("React Native", patterns)["react"] == 1
        assert extract_skills("Experience with React and Redux", patterns)["react"] == 1
        assert extract_skills("React/Next.js", patterns)["react"] == 1
        assert extract_skills("reactjs", patterns)["react"] == 1  # alias ReactJS, case-insensitive

        # Không được bắt nhầm
        assert extract_skills("users react quickly", patterns)["react"] == 0

    def test_spring_case_sensitive(self, patterns):
        """Spring (viết hoa) là framework, spring (viết thường) là từ thường."""
        assert extract_skills("Spring Framework", patterns)["spring"] == 1
        assert extract_skills("Spring Boot microservices", patterns)["spring"] == 1
        assert extract_skills("spring water is refreshing", patterns)["spring"] == 0

    def test_excel_case_sensitive(self, patterns):
        """Excel (viết hoa) là phần mềm, excel (viết thường) là động từ."""
        assert extract_skills("Proficient in Excel", patterns)["excel"] == 1
        assert extract_skills("MS Excel required", patterns)["excel"] == 1
        assert extract_skills("they excel at programming", patterns)["excel"] == 0


class TestBuildSkillMatrix:
    def test_basic_matrix(self, skill_dict):
        df = pd.DataFrame([
            {"job_id": "j1", "jd_text": "Cần Python và SQL."},
            {"job_id": "j2", "jd_text": "Sử dụng Docker và AWS."},
            {"job_id": "j3", "jd_text": "Python, Docker, PowerBI."},
        ])
        matrix = build_skill_matrix(df, skill_dict=skill_dict, min_count=1)
        assert "job_id" in matrix.columns
        assert len(matrix) == 3
        # Check job j1
        j1 = matrix[matrix["job_id"] == "j1"].iloc[0]
        assert j1["python"] == 1
        assert j1["sql"] == 1
        assert j1["docker"] == 0

    def test_min_count_filter(self, skill_dict):
        """Kỹ năng xuất hiện < min_count bị loại."""
        df = pd.DataFrame([
            {"job_id": "j1", "jd_text": "Python và SQL."},
            {"job_id": "j2", "jd_text": "Python và Docker."},
            {"job_id": "j3", "jd_text": "Python, SQL."},
        ])
        # react chỉ xuất hiện 0 lần → bị loại với min_count=1
        matrix = build_skill_matrix(df, skill_dict=skill_dict, min_count=2)
        assert "python" in matrix.columns  # 3 lần ≥ 2
        assert "sql" in matrix.columns     # 2 lần ≥ 2
        # react xuất hiện 0 lần → bị loại
        assert "react" not in matrix.columns

    def test_load_default_dict(self):
        """Có thể load từ điển mặc định."""
        d = load_skill_dict()
        assert isinstance(d, dict)
        assert "python" in d
        assert isinstance(d["python"], list)


class TestRealDictionaryAliases:
    """Alias bổ sung sau kiểm chứng A7 — chạy trên từ điển thật."""

    @pytest.fixture(scope="class")
    def real_patterns(self):
        return _build_patterns(load_skill_dict())

    def test_go_case_sensitive_with_exclusions(self, real_patterns):
        assert extract_skills("Python, Bash, Go for automation", real_patterns)["go"] == 1
        assert extract_skills("Java/Go services", real_patterns)["go"] == 1
        assert extract_skills("post Go-live support", real_patterns)["go"] == 0
        assert extract_skills("Go to market strategy", real_patterns)["go"] == 0
        assert extract_skills("ready to go now", real_patterns)["go"] == 0

    def test_testing_skills(self, real_patterns):
        assert extract_skills("hands-on manual testing", real_patterns)["manual_testing"] == 1
        assert extract_skills("Playwright, Cypress, or Selenium", real_patterns)["test_automation"] == 1

    def test_soft_skill_aliases(self, real_patterns):
        assert extract_skills("a reliable team player", real_patterns)["teamwork"] == 1
        assert extract_skills("Able to communicate clearly", real_patterns)["communication"] == 1

    def test_swift_case_sensitive(self, real_patterns):
        assert extract_skills("iOS Native using Swift", real_patterns)["swift"] == 1
        assert extract_skills("UIKit, SwiftUI, Combine", real_patterns)["swift"] == 1
        # SWIFT (chuẩn ngân hàng) không phải ngôn ngữ Swift
        assert extract_skills("banking protocols (ISO 8583, SWIFT)", real_patterns)["swift"] == 0

    def test_plural_and_singular_aliases(self, real_patterns):
        """Dạng số nhiều/số ít (04/10): 'APIs' trước đây không khớp 'API' → sót 63 tin."""
        assert extract_skills("Build REST APIs and integrate systems", real_patterns)["api"] == 1
        assert extract_skills("knowledge of SQL, APIs, system integration", real_patterns)["api"] == 1
        assert extract_skills("Design data pipelines for ML", real_patterns)["data_pipeline"] == 1
        assert extract_skills("microservice architecture, REST, gRPC", real_patterns)["microservices"] == 1
        assert extract_skills("RAG pipelines, vector databases", real_patterns)["vector_db"] == 1
        # không bắt nhầm sang từ khác
        assert extract_skills("rapid prototyping", real_patterns)["api"] == 0
