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
        "react": ["ReactJS", "React.js"],
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
        text = "Tìm kiếm nhân viên kế toán có kinh nghiệm Excel."
        result = extract_skills(text, patterns)
        assert result["python"] == 0
        assert result["sql"] == 0

    def test_multiple_skills(self, patterns):
        text = "Cần biết Python, SQL, Docker, AWS."
        result = extract_skills(text, patterns)
        assert result["python"] == 1
        assert result["sql"] == 1
        assert result["docker"] == 1
        assert result["aws"] == 1

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
