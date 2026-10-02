import pandas as pd
import numpy as np
from pathlib import Path
from mlxtend.frequent_patterns import apriori, association_rules
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def run_apriori(df: pd.DataFrame, min_supports: list[float] = [0.03, 0.05, 0.10], min_lift: float = 1.2):
    bool_df = df.astype(bool)
    results = {}
    best_rules = pd.DataFrame()
    used_support = min_supports[0]
    
    for ms in min_supports:
        try:
            frequent_itemsets = apriori(bool_df, min_support=ms, use_colnames=True)
            if frequent_itemsets.empty:
                results[ms] = 0
                continue
            rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
            results[ms] = len(rules)
            if not rules.empty and best_rules.empty:
                best_rules = rules
                used_support = ms
        except Exception as e:
            print(f"Error with min_support {ms}: {e}")
            results[ms] = 0
            
    if not best_rules.empty:
        best_rules['min_support_used'] = used_support
    return best_rules, results

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
    train_rules, support_results = run_apriori(train_df, min_supports=[0.03, 0.05, 0.10], min_lift=1.2)
    
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
        "## Kết quả chạy Apriori trên các mức min_support khác nhau (Train)",
    ]
    
    for ms, count in support_results.items():
        eval_lines.append(f"- min_support = {ms}: tìm được {count} luật (lift > 1.2)")
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
        
        eval_lines.append("## Top 10 luật kết hợp (theo Lift, đã bỏ luật đối xứng)")
        eval_lines.append("| Antecedents | Consequents | Train Support | Train Conf | Train Lift | Test Support | Test Conf | Test Lift |")
        eval_lines.append("|-------------|-------------|---------------|------------|------------|--------------|-----------|-----------|")
        
        test_bool = test_df.astype(bool)
        test_size = len(test_bool)
        
        lift_drops = []
        
        for _, row in top_rules.iterrows():
            ant = list(row['antecedents'])
            con = list(row['consequents'])
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
                
            lift_drops.append(row['lift'] - test_lift)
                
            ant_str = ", ".join(ant)
            con_str = ", ".join(con)
            
            eval_lines.append(
                f"| {ant_str} | {con_str} | {row['support']:.3f} | {row['confidence']:.3f} | {row['lift']:.3f} "
                f"| {test_supp:.3f} | {test_conf:.3f} | {test_lift:.3f} |"
            )
            
        eval_lines.append("")
        eval_lines.append("## Nhận xét (Overfit / Rule drift)")
        
        avg_drop = np.mean(lift_drops) if lift_drops else 0
        if avg_drop > 2.0:
            eval_lines.append(f"Có sự sụt giảm rất mạnh về Lift trên tập Test so với tập Train (trung bình giảm {avg_drop:.2f}). "
                              "Đây là hiện tượng rule drift / overfit rõ rệt: các luật kết hợp tìm được bị overfit vào thời điểm của tập Train (dữ liệu cũ) "
                              "và không còn sức mạnh phân loại/kết hợp trên tập dữ liệu mới (Test).")
        elif avg_drop > 0.5:
            eval_lines.append(f"Có sự sụt giảm về Lift trên tập Test so với tập Train (trung bình giảm {avg_drop:.2f}). "
                              "Hiện tượng rule drift có xuất hiện, cho thấy một số luật đã thay đổi theo thời gian hoặc bị overfit nhẹ vào tập Train.")
        else:
            eval_lines.append(f"Mức Lift trên tập Test khá tương đồng với tập Train (thay đổi trung bình {avg_drop:.2f}). "
                              "Các luật kết hợp có tính ổn định cao qua thời gian.")

    out_eval = PROJECT_ROOT / "reports" / "rules_eval.md"
    out_eval.parent.mkdir(parents=True, exist_ok=True)
    with open(out_eval, "w", encoding="utf-8") as f:
        f.write("\n".join(eval_lines))
    print(f"Saved evaluation to {out_eval}")

if __name__ == "__main__":
    main()
