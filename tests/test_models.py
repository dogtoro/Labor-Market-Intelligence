import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from src.models.features import (
    calculate_salary_mid,
    clean_level_feature,
    extract_location_flags,
    load_and_verify_data,
)


# ---------------------------------------------------------------------------
# load_and_verify_data
# ---------------------------------------------------------------------------

def _write_data(tmp_path, *, tamper=None, drop=None):
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    pd.DataFrame({"job_id": ["a", "b"]}).to_parquet(processed / "jobs_clean.parquet")
    pd.DataFrame({"job_id": ["a"], "python": [1]}).to_parquet(processed / "skill_matrix.parquet")

    files = []
    for name in ("jobs_clean.parquet", "skill_matrix.parquet"):
        if name == drop:
            continue
        sha = hashlib.sha256((processed / name).read_bytes()).hexdigest()
        files.append({"filename": name, "sha256": "0" * 64 if name == tamper else sha})
    manifest = tmp_path / "MANIFEST.json"
    manifest.write_text(json.dumps({"files": files}), encoding="utf-8")
    return tmp_path / "data", manifest


def test_load_and_verify_data_ok(tmp_path):
    data_dir, manifest = _write_data(tmp_path)
    jobs, skills = load_and_verify_data(data_dir, manifest)
    assert len(jobs) == 2
    assert list(skills.columns) == ["job_id", "python"]


def test_load_and_verify_data_hash_mismatch_raises(tmp_path):
    data_dir, manifest = _write_data(tmp_path, tamper="skill_matrix.parquet")
    with pytest.raises(ValueError, match="lệch MANIFEST"):
        load_and_verify_data(data_dir, manifest)


def test_load_and_verify_data_not_in_manifest_raises(tmp_path):
    data_dir, manifest = _write_data(tmp_path, drop="jobs_clean.parquet")
    with pytest.raises(ValueError, match="không có jobs_clean.parquet"):
        load_and_verify_data(data_dir, manifest)


def test_load_and_verify_data_missing_file_raises(tmp_path):
    data_dir, manifest = _write_data(tmp_path)
    (data_dir / "processed" / "skill_matrix.parquet").unlink()
    with pytest.raises(FileNotFoundError):
        load_and_verify_data(data_dir, manifest)


# ---------------------------------------------------------------------------
# calculate_salary_mid
# ---------------------------------------------------------------------------

def test_salary_mid():
    df = pd.DataFrame({
        "salary_min": [10.0, 20.0, np.nan, np.nan],
        "salary_max": [20.0, np.nan, 30.0, np.nan],
        "salary_status": ["full_range", "one_sided", "one_sided", "undisclosed"],
    })
    s_mid = calculate_salary_mid(df)

    assert s_mid.iloc[0] == 15.0   # (10 + 20) / 2
    assert s_mid.iloc[1] == 20.0   # one_sided, chỉ có cận dưới
    assert s_mid.iloc[2] == 30.0   # one_sided, chỉ có cận trên
    assert pd.isna(s_mid.iloc[3])  # undisclosed


def test_salary_mid_tertile_labels():
    df = pd.DataFrame({
        "salary_min": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "salary_max": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "salary_status": ["full_range"] * 6,
    })
    labels = pd.qcut(calculate_salary_mid(df), q=3, labels=["Low", "Mid", "High"])
    assert list(labels) == ["Low", "Low", "Mid", "Mid", "High", "High"]


# ---------------------------------------------------------------------------
# extract_location_flags
# ---------------------------------------------------------------------------

def test_location_flags_real_values():
    df = pd.DataFrame({"location": [
        "Hồ Chí Minh",
        "Hà Nội; Đà Nẵng",
        "Thành phố khác",
        np.nan,
        "Hồ Chí Minh; Thành phố khác",
    ]})
    flags = extract_location_flags(df)

    assert list(flags.columns) == ["loc_hcm", "loc_hn", "loc_dn", "loc_other"]
    assert flags.iloc[0].tolist() == [1, 0, 0, 0]
    assert flags.iloc[1].tolist() == [0, 1, 1, 0]
    assert flags.iloc[2].tolist() == [0, 0, 0, 1]
    assert flags.iloc[3].tolist() == [0, 0, 0, 0]
    assert flags.iloc[4].tolist() == [1, 0, 0, 1]


def test_location_flags_unknown_value_raises():
    with pytest.raises(ValueError, match="Location lạ"):
        extract_location_flags(pd.DataFrame({"location": ["Cần Thơ"]}))


# ---------------------------------------------------------------------------
# clean_level_feature
# ---------------------------------------------------------------------------

def test_clean_level_feature():
    df = pd.DataFrame({"level": [
        "Intern", "Fresher", "Junior", "Middle", "Senior",
        "Lead", "Principal", "Manager", "Head", "Director", None,
    ]})
    assert clean_level_feature(df).tolist() == [
        "Intern/Junior", "Intern/Junior", "Intern/Junior", "Middle", "Senior",
        "Lead", "Lead", "Manager", "Manager", "Manager", "Unknown",
    ]


def test_clean_level_feature_unknown_label_raises():
    with pytest.raises(ValueError, match="Level lạ"):
        clean_level_feature(pd.DataFrame({"level": ["Senior", "Staff"]}))

# ---------------------------------------------------------------------------
# calculate_purity_fmeasure
# ---------------------------------------------------------------------------
from src.models.clustering import calculate_purity_fmeasure

def test_purity_and_fmeasure():
    # Example from a typical clustering evaluation
    crosstab = pd.DataFrame({
        'Cat1': [5, 1, 2],
        'Cat2': [1, 4, 0],
        'Cat3': [0, 1, 3]
    }, index=['C1', 'C2', 'C3'])
    
    purity, baseline_purity, overall_f = calculate_purity_fmeasure(crosstab)
    
    # N = 17
    # Max per cluster: C1=5, C2=4, C3=3. Sum = 12. Purity = 12/17 = 0.7058...
    # Baseline purity: Max per Cat: Cat1=8. Baseline = 8/17 = 0.4705...
    assert pytest.approx(purity, 0.001) == 12 / 17
    assert pytest.approx(baseline_purity, 0.001) == 8 / 17
    
    # Cat1 F-measure: best is C1: precision=5/6, recall=5/8 -> F1 = 2 * (5/6 * 5/8) / (5/6 + 5/8) = 0.714
    # Cat2 F-measure: best is C2: precision=4/6, recall=4/5 -> F1 = 2 * (4/6 * 4/5) / (4/6 + 4/5) = 0.727
    # Cat3 F-measure: best is C3: precision=3/5, recall=3/4 -> F1 = 2 * (3/5 * 3/4) / (3/5 + 3/4) = 0.666
    
    # overall_f = (0.714 * 8 + 0.727 * 5 + 0.666 * 4) / 17 = 0.706
    assert overall_f > 0.6 and overall_f < 0.8


# ---------------------------------------------------------------------------
# map_expertise_groups
# ---------------------------------------------------------------------------

def test_map_expertise_groups_ok():
    from src.models.clustering import map_expertise_groups

    cats = pd.Series(["Backend Developer", "Data Engineer", None])
    groups = map_expertise_groups(cats, {"Backend Developer": "Backend", "Data Engineer": "Data/AI"})
    assert groups.iloc[0] == "Backend"
    assert groups.iloc[1] == "Data/AI"
    assert pd.isna(groups.iloc[2])


def test_map_expertise_groups_unmapped_raises():
    from src.models.clustering import map_expertise_groups

    with pytest.raises(ValueError, match="Chưa gộp category"):
        map_expertise_groups(pd.Series(["Backend Developer", "Prompt Engineer"]), {"Backend Developer": "Backend"})


def test_expertise_groups_file_covers_all_categories():
    """expertise_groups.json phải phủ đủ 72 giá trị Job Expertise trong dữ liệu thật."""
    import json
    from pathlib import Path

    data = Path(__file__).resolve().parents[1] / "data" / "processed" / "jobs_clean.parquet"
    if not data.exists():
        pytest.skip("Chưa có jobs_clean.parquet (tải từ Drive)")
    from src.models.clustering import map_expertise_groups

    mapping = json.loads((data.parents[2] / "src" / "models" / "expertise_groups.json").read_text(encoding="utf-8"))
    groups = map_expertise_groups(pd.read_parquet(data)["category"], mapping)
    assert groups.notna().all()

# ---------------------------------------------------------------------------
# Task 1 & 2 Output Tests
# ---------------------------------------------------------------------------
def test_expertise_groups_coverage():
    import json
    from pathlib import Path
    
    project_root = Path(__file__).resolve().parent.parent
    mapping_file = project_root / 'src' / 'models' / 'expertise_groups.json'
    
    if not mapping_file.exists():
        pytest.skip("expertise_groups.json không tồn tại")
        
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
        
    assert len(mapping) == 72
    assert 'Data Analyst' in mapping
    assert mapping['Data Analyst'] == 'Data/AI'
    assert mapping['DevSecOps Engineer'] == 'Security'

def test_cluster_labels_contract():
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    
    cluster_file = project_root / 'data' / 'processed' / 'cluster_labels.csv'
    skill_file = project_root / 'data' / 'processed' / 'skill_matrix.parquet'
    
    if not cluster_file.exists() or not skill_file.exists():
        pytest.skip("Chưa có data để test output clustering")
        
    labels = pd.read_csv(cluster_file)
    skills = pd.read_parquet(skill_file)
    
    # job_id unique
    assert labels['job_id'].is_unique
    
    # Nằm trong skill matrix
    skill_jobs = set(skills['job_id'] if 'job_id' in skills.columns else skills.index)
    label_jobs = set(labels['job_id'])
    
    assert label_jobs.issubset(skill_jobs)



# ---------------------------------------------------------------------------
# classification: build_dataset, choose_final_params
# ---------------------------------------------------------------------------

def _toy_jobs_skills():
    jobs = pd.DataFrame({
        "job_id": [f"j{i}" for i in range(7)],
        "salary_status": ["full_range"] * 5 + ["one_sided", "undisclosed"],
        "salary_min": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, np.nan],
        "salary_max": [10.0, 20.0, 30.0, 40.0, 50.0, np.nan, np.nan],
        "level": ["Junior", "Senior", None, "Lead", "Manager", "Intern", "Senior"],
        "location": ["Hồ Chí Minh", "Hà Nội", "Hồ Chí Minh; Hà Nội", None, "Đà Nẵng", "Thành phố khác", "Hà Nội"],
    })
    # j5 không có trong skill_matrix (không bắt được kỹ năng nào)
    skills = pd.DataFrame({
        "job_id": ["j0", "j1", "j2", "j3", "j4", "j6"],
        "python": [1, 1, 1, 1, 1, 0],
        "sql": [0, 1, 0, 0, 0, 1],
    })
    return jobs, skills


def test_build_dataset_keeps_all_salary_jobs_and_columns():
    from src.models.classification import LEVEL_COLUMNS, build_dataset

    jobs, skills = _toy_jobs_skills()
    X, y, bins = build_dataset(jobs, skills, min_skill_count=2)

    assert len(X) == 6                      # 6 tin có lương, kể cả j5 không có trong skill_matrix
    assert "j6" not in X.index              # tin undisclosed bị loại
    assert X.loc["j5", "python"] == 0       # left join điền 0
    assert "sql" not in X.columns           # chỉ 1 lần trong tin có lương < min_skill_count
    for col in LEVEL_COLUMNS + ["loc_hcm", "loc_hn", "loc_dn", "loc_other"]:
        assert col in X.columns             # đủ cột kể cả khi không có tin nào
    assert list(X.columns) == sorted(X.columns)
    assert X.loc["j2", "lvl_Unknown"] == 1
    assert X.loc["j2", ["loc_hcm", "loc_hn"]].tolist() == [1, 1]
    assert y.value_counts().to_dict() == {"Low": 2, "Mid": 2, "High": 2}
    assert len(bins) == 4


def test_choose_final_params_tie_prefers_simpler_tree():
    from src.models.classification import choose_final_params

    # (3,5) và (4,5) hoà 2–2 → chọn cây nông hơn, không phụ thuộc thứ tự
    assert choose_final_params([(4, 5), (4, 10), (3, 5), (3, 5), (4, 5)]) == (3, 5)
    assert choose_final_params([(3, 5), (3, 5), (4, 5), (4, 5), (4, 10)]) == (3, 5)
    # cùng depth, hoà → min_samples_leaf lớn hơn
    assert choose_final_params([(3, 5), (3, 10)]) == (3, 10)
    # không hoà → bộ nhiều nhất
    assert choose_final_params([(5, 5), (5, 5), (3, 5)]) == (5, 5)


# ---------------------------------------------------------------------------
# bias_analysis: compare_groups, top_by_abs_diff
# ---------------------------------------------------------------------------

def test_compare_groups_rates_pvalues_and_bh():
    from scipy.stats import fisher_exact
    from src.models.bias_analysis import DIFF, PCT_HAS, PCT_NO, compare_groups

    has = pd.Series([True] * 4 + [False] * 6)
    flags = pd.DataFrame({
        "a": [1, 1, 1, 0, 0, 0, 0, 0, 0, 1],   # có lương 3/4, không lương 1/6
        "b": [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],   # có lương 0/4, không lương 6/6
        "rare": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    })
    out = compare_groups(flags, has, min_total=2)

    assert "rare" not in out.index                       # tổng 1 < min_total
    assert out.loc["a", PCT_HAS] == 0.75
    assert out.loc["a", PCT_NO] == pytest.approx(1 / 6)
    assert out.loc["a", DIFF] == pytest.approx(0.75 - 1 / 6)
    assert out.loc["a", "p_value"] == pytest.approx(fisher_exact([[3, 1], [1, 5]]).pvalue)
    assert (out["adj_p_value"] >= out["p_value"]).all()  # BH không làm p nhỏ đi


def test_top_by_abs_diff_ties_sorted_by_name():
    from src.models.bias_analysis import DIFF, top_by_abs_diff

    df = pd.DataFrame({DIFF: [0.041, -0.041, 0.10, 0.041]}, index=["kotlin", "figma", "aws", "jenkins"])
    assert list(top_by_abs_diff(df, 4).index) == ["aws", "figma", "jenkins", "kotlin"]
    # đảo thứ tự dòng đầu vào → kết quả không đổi
    assert list(top_by_abs_diff(df.iloc[::-1], 4).index) == ["aws", "figma", "jenkins", "kotlin"]


# ---------------------------------------------------------------------------
# clustering: quy tắc nhiễu (04/10)
# ---------------------------------------------------------------------------

def test_assign_noise_marks_small_clusters_and_renumbers_by_size():
    import numpy as np
    from src.models.clustering import NOISE_LABEL, assign_noise

    raw = np.array([3] * 20 + [1] * 40 + [2] * 5 + [4] * 16)
    out = assign_noise(raw, min_size=15)

    assert set(out) == {1, 2, 3, NOISE_LABEL}
    assert (out[raw == 1] == 1).all()          # 40 tin → cụm 1 (lớn nhất)
    assert (out[raw == 3] == 2).all()          # 20 tin → cụm 2
    assert (out[raw == 4] == 3).all()          # 16 tin → cụm 3
    assert (out[raw == 2] == NOISE_LABEL).all()  # 5 tin < 15 → nhiễu


def test_evaluate_k_validity_rule():
    import numpy as np
    from src.models.clustering import evaluate_k

    # 3 cụm thật × 20 tin + 2 tin nhiễu (3,2% ≤ 5%) → hợp lệ
    raw = np.array([1] * 20 + [2] * 20 + [3] * 20 + [4] * 2)
    D = np.ones((len(raw), len(raw)))
    for c in set(raw):
        idx = np.where(raw == c)[0]
        D[np.ix_(idx, idx)] = 0.2
    np.fill_diagonal(D, 0)
    groups = np.array(["A"] * 20 + ["B"] * 20 + ["C"] * 20 + ["A"] * 2)

    res = evaluate_k(raw, D, groups)
    assert res["valid"]
    assert res["n_noise"] == 2
    assert res["purity"] == 1.0                 # 3 cụm thật khớp hoàn toàn 3 nhóm
    assert res["silhouette"] > 0.5

    # chỉ 2 cụm thật → không hợp lệ
    res2 = evaluate_k(np.array([1] * 30 + [2] * 30 + [3] * 2), D[:62, :62], groups[:62])
    assert not res2["valid"]
