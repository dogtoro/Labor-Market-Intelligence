import pandas as pd
import numpy as np
from pathlib import Path
from mlxtend.frequent_patterns import apriori, association_rules
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def run_apriori(df: pd.DataFrame, min_supports: list[float] = [0.03, 0.04, 0.05, 0.06, 0.10], min_lift: float = 1.2, min_confidence: float = 0.5):
    bool_df = df.astype(bool)
    results = {}
    best_rules = pd.DataFrame()
    used_support = min_supports[0]
    
    all_rules_by_supp = {}
    
    for ms in min_supports:
        try:
            frequent_itemsets = apriori(bool_df, min_support=ms, use_colnames=True)
            if frequent_itemsets.empty:
                results[ms] = 0
                continue
            rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
            rules = rules[rules['confidence'] >= min_confidence].copy()
            results[ms] = len(rules)
            all_rules_by_supp[ms] = rules
        except Exception as e:
            print(f"Error with min_support {ms}: {e}")
            results[ms] = 0
            
    # Choose min_support that gives between 20 and 100 rules, preferably
    for ms, count in results.items():
        if 20 <= count <= 100:
            best_rules = all_rules_by_supp[ms]
            used_support = ms
            break
            
    # Fallback to the first non-empty if none match criteria
    if best_rules.empty:
        for ms, rules in all_rules_by_supp.items():
            if not rules.empty:
                best_rules = rules
                used_support = ms
                break

    if not best_rules.empty:
        best_rules = sort_rules(best_rules)
        best_rules['min_support_used'] = used_support
    return best_rules, results

def format_itemset(itemset) -> str:
    """Join skill names in sorted order — frozenset order changes with PYTHONHASHSEED."""
    return ", ".join(sorted(itemset))

def sort_rules(rules: pd.DataFrame) -> pd.DataFrame:
    """Deterministic order: lift desc, confidence desc, then antecedents/consequents names.

    A→B and B→A always share the same lift, so confidence and names are needed
    as tie-breakers; otherwise the kept rule depends on frozenset iteration order.
    Lift/confidence are rounded so float noise in the last bits cannot reorder ties.
    """
    if rules.empty:
        return rules
    keys = pd.DataFrame({
        '_lift': rules['lift'].round(10),
        '_conf': rules['confidence'].round(10),
        '_ant': rules['antecedents'].map(format_itemset),
        '_con': rules['consequents'].map(format_itemset),
    }, index=rules.index)
    order = keys.sort_values(
        ['_lift', '_conf', '_ant', '_con'],
        ascending=[False, False, True, True],
        kind='mergesort',
    ).index
    return rules.loc[order].reset_index(drop=True)

def evaluate_rules_on_test(top_rules: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    test_bool = test_df.astype(bool)
    test_size = len(test_bool)
    
    results = {}
    for idx, row in top_rules.iterrows():
        ant = list(row['antecedents']) if isinstance(row['antecedents'], (list, frozenset, set, tuple)) else row['antecedents'].split(", ")
        con = list(row['consequents']) if isinstance(row['consequents'], (list, frozenset, set, tuple)) else row['consequents'].split(", ")
        both = ant + con
        
        valid = all(f in test_bool.columns for f in both)
        
        if valid and test_size > 0:
            ant_mask = test_bool[ant].all(axis=1)
            con_mask = test_bool[con].all(axis=1)
            both_mask = test_bool[both].all(axis=1)
            
            test_ant_supp = ant_mask.sum() / test_size
            test_con_supp = con_mask.sum() / test_size
            test_supp = both_mask.sum() / test_size
            
            test_conf = test_supp / test_ant_supp if test_ant_supp > 0 else 0
            test_lift = test_conf / test_con_supp if test_con_supp > 0 else 0
        else:
            test_supp, test_conf, test_lift = 0, 0, 0
            
        results[idx] = {
            'test_support': test_supp,
            'test_confidence': test_conf,
            'test_lift': test_lift
        }
    return results

DATA_SKILLS = {
    'python', 'sql', 'spark', 'airflow', 'etl', 'data_pipeline', 'pandas', 'numpy',
    'kafka', 'dbt', 'hadoop', 'databricks', 'snowflake', 'bigquery', 'redshift',
    'data_warehouse', 'data_lake', 'data_modeling', 'power_bi', 'tableau',
    'machine_learning', 'deep_learning', 'statistics',
}

def dedup_by_itemset(rules: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Keep only the best rule (see sort_rules) for each antecedents ∪ consequents itemset."""
    sorted_rules = sort_rules(rules)
    kept = []
    seen = set()
    for idx, row in sorted_rules.iterrows():
        union_set = frozenset(row['antecedents']) | frozenset(row['consequents'])
        if union_set not in seen:
            seen.add(union_set)
            kept.append(idx)
        if len(kept) == top_n:
            break
    return sorted_rules.loc[kept]

def filter_rules_with_skills(rules: pd.DataFrame, skills: set) -> pd.DataFrame:
    """Keep rules that contain at least one of the given skills."""
    if rules.empty:
        return rules
    mask = rules.apply(
        lambda r: bool((set(r['antecedents']) | set(r['consequents'])) & skills), axis=1
    )
    return rules[mask]

def mine_data_rules(
    train_df: pd.DataFrame,
    min_supports: list[float] = [0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03],
    min_lift: float = 1.2,
    min_confidence: float = 0.5,
    skills: set = DATA_SKILLS,
    min_rules: int = 10,
):
    """Choose min_support by the number of DATA rules (not total rules).

    Tries supports from high to low and keeps the first one yielding at least
    ``min_rules`` rules that contain a data skill. Falls back to the support
    with the most data rules. Returns (data_rules, used_support, counts).
    """
    counts = {}
    by_supp = {}
    for ms in min_supports:
        rules, _ = run_apriori(train_df, min_supports=[ms], min_lift=min_lift, min_confidence=min_confidence)
        data = sort_rules(filter_rules_with_skills(rules, skills))
        counts[ms] = len(data)
        by_supp[ms] = data
        if len(data) >= min_rules:
            return data, ms, counts

    if not counts or max(counts.values()) == 0:
        return pd.DataFrame(), None, counts
    best_ms = max(counts, key=counts.get)
    return by_supp[best_ms], best_ms, counts

def chronological_split(df: pd.DataFrame, train_frac: float = 0.7):
    """Split by posted_date (old → train). Stable sort with job_id as secondary key,
    so jobs sharing the boundary date always land on the same side."""
    ordered = df.sort_values(['posted_date', 'job_id'], kind='mergesort')
    split_idx = int(len(ordered) * train_frac)
    return ordered.iloc[:split_idx], ordered.iloc[split_idx:]

def main():
    print("Loading data...")
    jobs_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "jobs_clean.parquet")
    skills_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "skill_matrix.parquet")
    
    df = pd.merge(skills_df, jobs_df[['job_id', 'posted_date']], on='job_id', how='inner')
    df['posted_date'] = pd.to_datetime(df['posted_date'])

    feature_cols = [c for c in df.columns if c not in ('job_id', 'posted_date')]
    if len(feature_cols) == 0:
        print("No skills available to run Apriori.")
        return

    train_part, test_part = chronological_split(df, train_frac=0.7)
    train_df = train_part[feature_cols]
    test_df = test_part[feature_cols]
    
    print(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    print("Running Apriori on Train...")
    train_rules, support_results = run_apriori(train_df, min_supports=[0.03, 0.04, 0.05, 0.06, 0.10], min_lift=1.2, min_confidence=0.5)
    
    out_csv = PROJECT_ROOT / "data" / "processed" / "rules_train.csv"
    if not train_rules.empty:
        train_rules_csv = train_rules.copy()
        train_rules_csv['antecedents'] = train_rules_csv['antecedents'].apply(format_itemset)
        train_rules_csv['consequents'] = train_rules_csv['consequents'].apply(format_itemset)
        train_rules_csv.to_csv(out_csv, index=False)
        print(f"Saved {len(train_rules_csv)} rules to {out_csv}")
    else:
        pd.DataFrame().to_csv(out_csv, index=False)
        
    print("Evaluating on Test...")
    eval_lines = [
        "# Đánh giá Association Rules (Train vs Test)",
        "",
        "## Kích thước tập dữ liệu",
        f"- Train: {len(train_df)} bản ghi (70% tin cũ)",
        f"- Test: {len(test_df)} bản ghi (30% tin mới)",
        "",
        "## Lựa chọn tham số",
        "- `min_confidence` = 0.5: Đảm bảo độ tin cậy của luật cao (ít nhất 50% khả năng kéo theo).",
        "- `min_lift` = 1.2: Lọc các luật có tương quan tích cực rõ rệt.",
        "Kết quả chạy Apriori trên các mức min_support khác nhau (Train):",
    ]
    
    for ms, count in support_results.items():
        eval_lines.append(f"- min_support = {ms}: tìm được {count} luật")
        
    if not train_rules.empty:
        ms_used = train_rules['min_support_used'].iloc[0]
        eval_lines.append(f"\n=> Chọn `min_support` = {ms_used} vì số lượng luật tìm được ({len(train_rules)}) nằm trong khoảng vừa phải (không quá ít để phân tích, không quá nhiều dẫn đến nhiễu).")
        
    eval_lines.append("")
    
    if train_rules.empty:
        eval_lines.append("Không tìm thấy luật kết hợp nào trên tập Train.")
    else:
        top_rules = dedup_by_itemset(train_rules, top_n=10)
        test_results = evaluate_rules_on_test(top_rules, test_df)

        eval_lines.append("## Top 10 luật kết hợp (theo Lift, mỗi tập kỹ năng chỉ giữ 1 luật)")
        eval_lines.append("| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |")
        eval_lines.append("|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|")
        
        test_lift_above_1_2 = 0
        
        for idx, row in top_rules.iterrows():
            ant_str = format_itemset(row['antecedents'])
            con_str = format_itemset(row['consequents'])
            
            res = test_results[idx]
            test_supp = res['test_support']
            test_conf = res['test_confidence']
            test_lift = res['test_lift']
            
            if test_lift > 1.2 and test_conf >= 0.5:
                test_lift_above_1_2 += 1
                
            eval_lines.append(
                f"| {ant_str} | {con_str} | {row['support']:.3f} | {row['confidence']:.3f} | {row['lift']:.3f} "
                f"| {test_supp:.3f} | {test_conf:.3f} | {test_lift:.3f} |"
            )
            
        eval_lines.append("")
        eval_lines.append("## Nhận xét (Overfit / Rule drift)")
        
        eval_lines.append(f"Có {test_lift_above_1_2}/{len(top_rules)} luật trong top 10 vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.")
        
        eval_lines.append("")
        eval_lines.append("> **Hạn chế dữ liệu:** Dữ liệu thu thập là một snapshot các tin tuyển dụng còn active tính đến ngày 29/09. "
                          "Do đó, việc chia Train/Test theo `posted_date` phản ánh sự khác biệt theo độ tuổi của tin (tin cũ vs tin mới đăng), "
                          "chứ không hoàn toàn đo lường được sự thay đổi của thị trường theo thời gian dài.")

    
    # --- THÊM BẢNG LUẬT DATA ---
    print("Running Apriori for Data rules on Train...")
    data_rules, data_ms, data_counts = mine_data_rules(train_df, min_lift=1.2, min_confidence=0.5)

    eval_lines.append("")
    eval_lines.append("## Top luật có kỹ năng data")
    eval_lines.append(f"Kỹ năng data dùng để lọc: {', '.join(sorted(DATA_SKILLS))}.")
    eval_lines.append("")
    eval_lines.append("Số luật có kỹ năng data theo min_support (Train, lift > 1.2, confidence >= 0.5):")
    for ms, count in data_counts.items():
        eval_lines.append(f"- min_support = {ms}: {count} luật")
    eval_lines.append("")

    if data_rules.empty:
        eval_lines.append("Không tìm thấy luật nào chứa kỹ năng data ở các mức min_support đã thử.")
    else:
        eval_lines.append(f"=> Chọn `min_support` = {data_ms} (mức cao nhất cho ra ≥10 luật có kỹ năng data; nếu không có thì lấy mức nhiều luật nhất).")
        eval_lines.append("")
        top_data = dedup_by_itemset(data_rules, top_n=10)
        data_test_results = evaluate_rules_on_test(top_data, test_df)

        eval_lines.append("| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |")
        eval_lines.append("|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|")

        data_pass = 0
        for idx, row in top_data.iterrows():
            ant_str = format_itemset(row['antecedents'])
            con_str = format_itemset(row['consequents'])
            res = data_test_results[idx]
            if res['test_lift'] > 1.2 and res['test_confidence'] >= 0.5:
                data_pass += 1
            eval_lines.append(
                f"| {ant_str} | {con_str} | {row['support']:.3f} | {row['confidence']:.3f} | {row['lift']:.3f} "
                f"| {res['test_support']:.3f} | {res['test_confidence']:.3f} | {res['test_lift']:.3f} |"
            )
        eval_lines.append("")
        eval_lines.append(f"Có {data_pass}/{len(top_data)} luật data vẫn đạt cả lift > 1.2 và confidence >= 0.5 trên tập Test.")
    
    out_eval = PROJECT_ROOT / "reports" / "rules_eval.md"
    out_eval.parent.mkdir(parents=True, exist_ok=True)
    with open(out_eval, "w", encoding="utf-8") as f:
        f.write("\n".join(eval_lines))
    print(f"Saved evaluation to {out_eval}")

if __name__ == "__main__":
    main()
