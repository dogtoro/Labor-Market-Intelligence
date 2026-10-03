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
