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
    best_rules, results = run_apriori(df, min_supports=[0.2, 0.4, 0.6], min_lift=1.0)
    
    # Assert return types and structures
    assert isinstance(best_rules, pd.DataFrame)
    assert isinstance(results, dict)
    
    # Verify results dict
    assert 0.2 in results
    assert 0.4 in results
    assert 0.6 in results
    
    # Verify best_rules
    if not best_rules.empty:
        assert 'antecedents' in best_rules.columns
        assert 'consequents' in best_rules.columns
        assert 'support' in best_rules.columns
        assert 'confidence' in best_rules.columns
        assert 'lift' in best_rules.columns
        assert 'min_support_used' in best_rules.columns
        
        # Test lift filtering condition
        assert all(best_rules['lift'] >= 1.0)
