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
        best_rules['min_support_used'] = used_support
    return best_rules, results

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

def format_itemset(frozen_set):
    return ", ".join(list(frozen_set))

def main():
    print("Loading data...")
    jobs_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "jobs_clean.parquet")
    skills_df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "skill_matrix.parquet")
    
    df = pd.merge(skills_df, jobs_df[['job_id', 'posted_date']], on='job_id', how='inner')
    df['posted_date'] = pd.to_datetime(df['posted_date'])
    df = df.sort_values('posted_date')
    
    feature_cols = [c for c in df.columns if c not in ('job_id', 'posted_date')]
    if len(feature_cols) == 0:
        print("No skills available to run Apriori.")
        return
        
    split_idx = int(len(df) * 0.7)
    train_df = df.iloc[:split_idx][feature_cols]
    test_df = df.iloc[split_idx:][feature_cols]
    
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
        # Sort and remove symmetric rules
        sorted_rules = train_rules.sort_values('lift', ascending=False)
        unique_rules = []
        seen_pairs = set()
        
        for idx, row in sorted_rules.iterrows():
            ant = row['antecedents']
            con = row['consequents']
            pair = frozenset([ant, con])
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_rules.append(idx)
            if len(unique_rules) == 10:
                break
                
        top_rules = sorted_rules.loc[unique_rules]
        test_results = evaluate_rules_on_test(top_rules, test_df)
        
        eval_lines.append("## Top 10 luật kết hợp (theo Lift, đã bỏ luật đối xứng)")
        eval_lines.append("| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |")
        eval_lines.append("|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|")
        
        test_lift_above_1_2 = 0
        
        for idx, row in top_rules.iterrows():
            ant = list(row['antecedents'])
            con = list(row['consequents'])
            ant_str = ", ".join(ant)
            con_str = ", ".join(con)
            
            res = test_results[idx]
            test_supp = res['test_support']
            test_conf = res['test_confidence']
            test_lift = res['test_lift']
            
            if test_lift > 1.2:
                test_lift_above_1_2 += 1
                
            eval_lines.append(
                f"| {ant_str} | {con_str} | {row['support']:.3f} | {row['confidence']:.3f} | {row['lift']:.3f} "
                f"| {test_supp:.3f} | {test_conf:.3f} | {test_lift:.3f} |"
            )
            
        eval_lines.append("")
        eval_lines.append("## Nhận xét (Overfit / Rule drift)")
        
        eval_lines.append(f"Có {test_lift_above_1_2}/{len(top_rules)} luật trong top 10 vẫn đạt ngưỡng lift > 1.2 trên tập Test.")
        
        eval_lines.append("")
        eval_lines.append("> **Hạn chế dữ liệu:** Dữ liệu thu thập là một snapshot các tin tuyển dụng còn active tính đến ngày 29/09. "
                          "Do đó, việc chia Train/Test theo `posted_date` phản ánh sự khác biệt theo độ tuổi của tin (tin cũ vs tin mới đăng), "
                          "chứ không hoàn toàn đo lường được sự thay đổi của thị trường theo thời gian dài.")

    out_eval = PROJECT_ROOT / "reports" / "rules_eval.md"
    out_eval.parent.mkdir(parents=True, exist_ok=True)
    with open(out_eval, "w", encoding="utf-8") as f:
        f.write("\n".join(eval_lines))
    print(f"Saved evaluation to {out_eval}")

if __name__ == "__main__":
    main()
