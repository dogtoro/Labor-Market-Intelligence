"""Tests for conservative ITviec deduplication logic."""

import pandas as pd
import pytest

from src.clean.dedup import find_duplicates, jd_similarity, title_similarity


class TestTitleSimilarity:
    def test_identical(self):
        assert title_similarity("Senior Data Engineer", "Senior Data Engineer") == pytest.approx(1.0)

    def test_case_insensitive(self):
        assert title_similarity("Senior Data Engineer", "senior data engineer") == pytest.approx(1.0)

    def test_different(self):
        assert title_similarity("Senior Data Engineer", "Junior Frontend Developer") < 0.5

    def test_empty(self):
        assert title_similarity("", "something") == pytest.approx(0.0)


class TestJdSimilarity:
    def test_identical(self):
        assert jd_similarity("Build APIs and maintain services", "Build APIs and maintain services") == pytest.approx(1.0)

    def test_different(self):
        assert jd_similarity("Build mobile apps with Flutter", "Build backend APIs with Java Spring") < 0.95


class TestFindDuplicates:
    def _row(self, title, jd, date="2026-09-15", company="ABC"):
        return {"company": company, "title": title, "jd_text": jd, "posted_date": date}

    def test_exact_duplicate(self):
        jd = "Build ETL pipelines with Python SQL Airflow and maintain data quality."
        df = pd.DataFrame([
            self._row("Data Engineer", jd, "2026-09-15"),
            self._row("Data Engineer", jd, "2026-09-16"),
        ])
        dups = find_duplicates(df)
        assert dups.sum() == 1
        assert dups.tolist() == [True, False]  # newer row is retained

    def test_similar_title_but_different_jd_is_not_duplicate(self):
        df = pd.DataFrame([
            self._row(
                "Middle, Senior FullStack Developer",
                "Build React frontend and Node.js services for an e-commerce platform.",
            ),
            self._row(
                "Junior, Senior FullStack Developer",
                "Develop Java Spring banking APIs and maintain Oracle integrations.",
            ),
        ])
        assert find_duplicates(df).sum() == 0

    def test_mobile_vs_backend_template_false_positive(self):
        df = pd.DataFrame([
            self._row("Middle/Senior Mobile Developer", "Develop native iOS and Android applications."),
            self._row("Middle/Senior Backend Developer", "Develop backend microservices using Java and Kafka."),
        ])
        assert find_duplicates(df).sum() == 0

    def test_ai_titles_different_jd_not_duplicate(self):
        df = pd.DataFrame([
            self._row("Senior AI Engineer CV/NLP/LLM", "Train computer vision and NLP models for document AI."),
            self._row("All level AI Engineer CV/NLP/LLM", "Build LLM agents, RAG pipelines and evaluation systems."),
        ])
        assert find_duplicates(df).sum() == 0

    def test_data_vs_ai_trainee_not_duplicate(self):
        df = pd.DataFrame([
            self._row("Tap su tiem nang Data Engineer", "Build ETL pipelines, SQL models and data warehouses."),
            self._row("Tap su tiem nang AI Engineer", "Train machine learning models using Python and PyTorch."),
        ])
        assert find_duplicates(df).sum() == 0

    def test_different_company(self):
        jd = "Same exact JD content"
        df = pd.DataFrame([
            self._row("Data Engineer", jd, company="ABC"),
            self._row("Data Engineer", jd, company="XYZ"),
        ])
        assert find_duplicates(df).sum() == 0

    def test_date_too_far(self):
        jd = "Same exact JD content"
        df = pd.DataFrame([
            self._row("Data Engineer", jd, "2026-09-01"),
            self._row("Data Engineer", jd, "2026-09-20"),
        ])
        assert find_duplicates(df).sum() == 0

    def test_requires_jd_text(self):
        df = pd.DataFrame([{"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"}])
        with pytest.raises(ValueError, match="jd_text"):
            find_duplicates(df)
