import pandas as pd
import pytest
from src.models.apriori import run_apriori

def test_run_apriori():
    # Create mock boolean dataframe
    data = {
        'java': [1, 1, 0, 1, 0],
        'spring': [1, 1, 0, 0, 0],
        'docker': [1, 0, 1, 1, 0],
        'kubernetes': [0, 0, 1, 1, 0],
        'sql': [1, 1, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    
    # Run apriori
    # We set min_supports to capture rules in this small dataset
    best_rules, results = run_apriori(df, min_supports=[0.2, 0.4, 0.6], min_lift=1.0, min_confidence=0.1)
    
    # Assert return types and structures
    assert isinstance(best_rules, pd.DataFrame)
    assert isinstance(results, dict)
    
    # Verify results dict
    assert 0.2 in results
    assert 0.4 in results
    assert 0.6 in results
    
    # Verify best_rules
    assert not best_rules.empty
    assert 'antecedents' in best_rules.columns
    assert 'consequents' in best_rules.columns
    assert 'support' in best_rules.columns
    assert 'confidence' in best_rules.columns
    assert 'lift' in best_rules.columns
    assert 'min_support_used' in best_rules.columns
    
    # Test lift filtering condition
    assert all(best_rules['lift'] >= 1.0)


def test_evaluate_rules_on_test():
    from src.models.apriori import evaluate_rules_on_test
    
    top_rules = pd.DataFrame({
        'antecedents': [['java']],
        'consequents': [['spring']],
        'support': [0.5],
        'confidence': [1.0],
        'lift': [2.0]
    })
    
    test_df = pd.DataFrame({
        'java': [1, 1, 0, 0],
        'spring': [1, 0, 1, 0]
    })
    
    results = evaluate_rules_on_test(top_rules, test_df)
    
    assert 0 in results
    res = results[0]
    assert res['test_support'] == 0.25      # java and spring = 1 / 4
    assert res['test_confidence'] == 0.5    # java is 1 in 2 rows. spring is 1 in 1 of them. 1/2
    assert res['test_lift'] == 1.0          # test_conf (0.5) / test_con_supp (0.5) = 1.0


def test_dedup_by_itemset_keeps_best_permutation():
    from src.models.apriori import dedup_by_itemset

    rules = pd.DataFrame({
        'antecedents': [frozenset({'git', 'docker'}), frozenset({'git', 'cicd'}), frozenset({'aws'})],
        'consequents': [frozenset({'cicd'}), frozenset({'docker'}), frozenset({'gcp'})],
        'lift': [2.5, 2.4, 3.0],
        'confidence': [0.8, 0.6, 0.7],
    })
    top = dedup_by_itemset(rules, top_n=10)

    # {git, docker, cicd} chỉ còn 1 luật (lift cao nhất), {aws, gcp} giữ nguyên
    assert len(top) == 2
    assert list(top['lift']) == [3.0, 2.5]


def test_mine_data_rules_picks_support_by_data_rules():
    from src.models.apriori import mine_data_rules

    # python và sql luôn đi cùng nhau; docker/kubernetes đi cùng nhau ở nửa còn lại
    df = pd.DataFrame({
        'python':     [1, 1, 1, 1, 0, 0, 0, 0],
        'sql':        [1, 1, 1, 1, 0, 0, 0, 0],
        'docker':     [0, 0, 0, 0, 1, 1, 1, 1],
        'kubernetes': [0, 0, 0, 0, 1, 1, 1, 1],
    })
    rules, used_ms, counts = mine_data_rules(
        df, min_supports=[0.6, 0.4], min_lift=1.2, min_confidence=0.5,
        skills={'python', 'sql'}, min_rules=2,
    )

    assert counts[0.6] == 0          # support 0.6 quá cao, không có luật nào
    assert used_ms == 0.4
    assert len(rules) == 2           # python → sql và sql → python
    for _, r in rules.iterrows():
        assert (set(r['antecedents']) | set(r['consequents'])) == {'python', 'sql'}


def test_mine_data_rules_empty_when_no_data_skill():
    from src.models.apriori import mine_data_rules

    df = pd.DataFrame({'docker': [1, 1, 0, 0], 'kubernetes': [1, 1, 0, 0]})
    rules, used_ms, _ = mine_data_rules(df, min_supports=[0.4], skills={'python'}, min_rules=1)

    assert rules.empty
    assert used_ms is None


def test_dedup_symmetric_rules_keeps_higher_confidence():
    from src.models.apriori import dedup_by_itemset

    # A→B và B→A luôn cùng lift; phải chọn theo confidence, không theo thứ tự frozenset
    rules = pd.DataFrame({
        'antecedents': [frozenset({'cicd'}), frozenset({'git'})],
        'consequents': [frozenset({'git'}), frozenset({'cicd'})],
        'lift': [2.2, 2.2],
        'confidence': [0.600, 0.698],
    })
    top = dedup_by_itemset(rules)

    assert len(top) == 1
    assert top.iloc[0]['antecedents'] == frozenset({'git'})


def test_format_itemset_is_sorted():
    from src.models.apriori import format_itemset

    assert format_itemset(frozenset({'git', 'aws', 'cicd'})) == "aws, cicd, git"


def test_chronological_split_stable_on_ties():
    from src.models.apriori import chronological_split

    df = pd.DataFrame({
        'job_id': ['d', 'b', 'c', 'a'],
        'posted_date': pd.to_datetime(['2026-09-01', '2026-09-02', '2026-09-02', '2026-09-02']),
    })
    train, test = chronological_split(df, train_frac=0.5)

    # Cùng ngày 02/09 → thứ tự theo job_id: a, b, c
    assert list(train['job_id']) == ['d', 'a']
    assert list(test['job_id']) == ['b', 'c']
    # Đảo thứ tự dòng đầu vào không đổi kết quả
    train2, _ = chronological_split(df.iloc[::-1], train_frac=0.5)
    assert list(train2['job_id']) == ['d', 'a']


def test_rules_identical_across_hash_seeds():
    """Cùng dữ liệu, PYTHONHASHSEED khác nhau → luật và thứ tự phải giống hệt."""
    import os
    import subprocess
    import sys

    code = (
        "import numpy as np, pandas as pd\n"
        "from src.models.apriori import run_apriori, dedup_by_itemset, format_itemset\n"
        "rng = np.random.default_rng(7)\n"
        "cols = ['python', 'sql', 'git', 'cicd', 'aws', 'docker', 'kubernetes', 'api']\n"
        "base = rng.random((300, 1)) < 0.5\n"
        "df = pd.DataFrame((rng.random((300, 8)) < 0.3) | base, columns=cols).astype(int)\n"
        "rules, _ = run_apriori(df, min_supports=[0.2], min_lift=1.0, min_confidence=0.3)\n"
        "top = dedup_by_itemset(rules, top_n=10)\n"
        "for r in top.itertuples():\n"
        "    print(format_itemset(r.antecedents), '->', format_itemset(r.consequents), round(r.lift, 6))\n"
    )
    outputs = []
    for seed in ('0', '1', '2', '3'):
        env = {**os.environ, 'PYTHONHASHSEED': seed}
        res = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, env=env, check=True)
        outputs.append(res.stdout)

    assert outputs[0].strip()
    assert all(o == outputs[0] for o in outputs)
