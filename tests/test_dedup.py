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
        assert sim > 0.6  # similar but not identical

    def test_empty(self):
        assert title_similarity("", "something") == pytest.approx(0.0)

    def test_none(self):
        assert title_similarity(None, "something") == pytest.approx(0.0)


class TestFindDuplicates:
    def test_exact_duplicate(self):
        """Cùng công ty, cùng title, cùng ngày → đánh dấu trùng."""
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
        ])
        dups = find_duplicates(df)
        assert dups.sum() == 1  # 1 bản bị đánh dấu trùng
        assert dups[0] == False  # Bản đầu giữ lại
        assert dups[1] == True   # Bản sau bị đánh dấu trùng

    def test_different_company(self):
        """Khác công ty → không trùng."""
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
            {"company": "XYZ", "title": "Data Engineer", "posted_date": "2026-09-15"},
        ])
        dups = find_duplicates(df)
        assert dups.sum() == 0

    def test_different_title(self):
        """Cùng công ty, khác title → không trùng."""
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-15"},
            {"company": "ABC", "title": "Frontend Developer", "posted_date": "2026-09-15"},
        ])
        dups = find_duplicates(df)
        assert dups.sum() == 0

    def test_date_too_far(self):
        """Cùng công ty, cùng title, nhưng ngày cách quá 7 ngày → không trùng."""
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-01"},
            {"company": "ABC", "title": "Data Engineer", "posted_date": "2026-09-20"},
        ])
        dups = find_duplicates(df)
        assert dups.sum() == 0

    def test_no_date(self):
        """Nếu posted_date là null → vẫn đánh dấu trùng (không check date)."""
        df = pd.DataFrame([
            {"company": "ABC", "title": "Data Engineer", "posted_date": None},
            {"company": "ABC", "title": "Data Engineer", "posted_date": None},
        ])
        dups = find_duplicates(df)
        assert dups.sum() == 1

    def test_similar_title(self):
        """Title gần giống (trên ngưỡng) → đánh dấu trùng."""
        df = pd.DataFrame([
            {"company": "ABC", "title": "Senior Data Engineer", "posted_date": "2026-09-15"},
            {"company": "ABC", "title": "Senior Data Engineer (HCM)", "posted_date": "2026-09-16"},
        ])
        dups = find_duplicates(df, title_threshold=0.7)
        assert dups.sum() == 1
