"""
Tests for deduplication logic.
"""

import pandas as pd
import pytest
from src.clean.dedup import title_similarity, find_duplicates


class TestTitleSimilarity:
    def test_identical(self):
        assert title_similarity("Senior Data Engineer", "Senior Data Engineer") == pytest.approx(1.0)

    def test_case_insensitive(self):
        assert title_similarity("Senior Data Engineer", "senior data engineer") == pytest.approx(1.0)

    def test_different(self):
        sim = title_similarity("Senior Data Engineer", "Junior Frontend Developer")
        assert sim < 0.5

    def test_similar(self):
        sim = title_similarity("Senior Data Engineer", "Sr. Data Engineer")
        assert sim > 0.6

    def test_empty(self):
        assert title_similarity("", "something") == pytest.approx(0.0)

    def test_none(self):
        assert title_similarity(None, "something") == pytest.approx(0.0)


class TestFindDuplicates:
    def test_exact_duplicate(self):
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
        ])
        dups = find_duplicates(df)
        assert dups.sum() == 1
        assert dups[0] == False
        assert dups[1] == True

    def test_company_case_and_whitespace_normalized(self):
        df = pd.DataFrame([
            {"company": "Example Co", "title": "Data Engineer", "posted_date": "2026-09-15"},
            {"company": "  example   co ", "title": "Data Engineer", "posted_date": "2026-09-16"},
        ])
        dups = find_duplicates(df)
        assert dups.tolist() == [False, True]

    def test_different_company(self):
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
            {"company": "XYZ", "title": "Data Engineer", "posted_date": "2026-09-15"},
        ])
        assert find_duplicates(df).sum() == 0

    def test_different_title(self):
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
            {"company": "ABC", "title": "Frontend Developer", "posted_date": "2026-09-15"},
        ])
        assert find_duplicates(df).sum() == 0

    def test_date_too_far(self):
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-01"},
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-20"},
        ])
        assert find_duplicates(df).sum() == 0

    def test_no_date(self):
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": None},
            {"company": "ABC", "title": "Data Engineer", "posted_date": None},
        ])
        assert find_duplicates(df).sum() == 1

    def test_similar_title(self):
        df = pd.DataFrame([
            {"company": "ABC", "title": "Senior Data Engineer", "posted_date": "2026-09-15"},
            {"company": "ABC", "title": "Senior Data Engineer (HCM)", "posted_date": "2026-09-16"},
        ])
        assert find_duplicates(df, title_threshold=0.7).sum() == 1
