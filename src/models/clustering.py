import pandas as pd
import numpy as np
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import json

from src.models.features import load_and_verify_data

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

FREQUENT_SKILL_RATIO = 0.40   # bỏ kỹ năng xuất hiện ở > 40% số tin
RARE_SKILL_MIN = 10           # bỏ kỹ năng xuất hiện ở < 10 tin (DECISIONS 03/10)
MIN_SKILLS_PER_JOB = 2        # bỏ tin còn < 2 kỹ năng sau khi lọc
MIN_CLUSTER_SIZE = 15         # k chỉ hợp lệ khi cụm nhỏ nhất có ≥ 15 tin
K_RANGE = range(4, 9)
MANUAL_DROPS = ['communication', 'teamwork', 'english', 'japanese', 'agile', 'jira', 'confluence']

def run_clustering():
    print("Loading data...")
    jobs_df, skills_df = load_and_verify_data()
    
    print("Processing skill matrix...")
    if 'job_id' in skills_df.columns:
        skills_df = skills_df.set_index('job_id')
    skills_df = skills_df.sort_index(axis=1)
    
    skill_counts = skills_df.sum()
    skill_freq = skills_df.mean()
    
    frequent_skills = skill_freq[skill_freq > FREQUENT_SKILL_RATIO].index.tolist()
    rare_skills = skill_counts[skill_counts < RARE_SKILL_MIN].index.tolist()
    
    drop_columns = sorted(set(frequent_skills + MANUAL_DROPS + rare_skills))
    drop_columns = [col for col in drop_columns if col in skills_df.columns]
    
    skills_filtered = skills_df.drop(columns=drop_columns)
    
    # Loại các tin có < 2 kỹ năng
    jobs_skill_counts = skills_filtered.sum(axis=1)
    dropped_jobs = jobs_skill_counts[jobs_skill_counts < MIN_SKILLS_PER_JOB].index.tolist()
    
    skills_final = skills_filtered.drop(index=dropped_jobs).astype(bool)
    
    print("Computing Jaccard distance and linkage (weighted)...")
    D = pdist(skills_final, metric='jaccard')
    Z = linkage(D, method='weighted')
    
    plt.figure(figsize=(10, 7))
    dendrogram(Z, truncate_mode='lastp', p=30)
    plt.title('Hierarchical Clustering (Weighted Linkage, Jaccard)')
    plt.xlabel('Cluster size')
    plt.ylabel('Distance')
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'reports' / 'figures' / 'dendrogram.png')
    plt.close()
    
    D_square = squareform(D)
    
    best_k = None
    best_score = -1
    best_labels = None
    
    k_results = []
    
    # Need to load mapping for evaluating Purity directly
    with open(PROJECT_ROOT / 'src' / 'models' / 'expertise_groups.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)
        
    jobs_df_eval = jobs_df.copy()
    jobs_df_eval['expertise_group'] = map_expertise_groups(jobs_df_eval['category'], mapping)
    
    for k in K_RANGE:
        labels = fcluster(Z, k, criterion='maxclust')
        score = silhouette_score(D_square, labels, metric='precomputed')
        
        cluster_sizes = pd.Series(labels).value_counts()
        valid = bool(cluster_sizes.min() >= MIN_CLUSTER_SIZE)
        
        # Đánh giá purity
        temp_cluster = pd.DataFrame({'job_id': skills_final.index, 'cluster': labels})
        merged = temp_cluster.merge(jobs_df_eval[['job_id', 'expertise_group']], on='job_id', how='inner')
        crosstab = pd.crosstab(merged['cluster'], merged['expertise_group'])
        
        N = crosstab.sum().sum()
        purity = crosstab.max(axis=1).sum() / N
        
        k_results.append({
            'k': k,
            'sizes': cluster_sizes.values.tolist(),
            'silhouette': score,
            'purity': purity,
            'valid': valid
        })
        
        if valid and score > best_score:
            best_score = score
            best_k = k
            best_labels = labels
            
    if best_k is None:
        raise ValueError(
            f"Không có k nào trong {list(K_RANGE)} có cụm nhỏ nhất ≥ {MIN_CLUSTER_SIZE} tin. "
            "Xem lại ngưỡng lọc hoặc khoảng k — không tự chọn k ngoài điều kiện."
        )
        
    cluster_df = pd.DataFrame({
        'job_id': skills_final.index,
        'cluster': best_labels
    }).sort_values('job_id')
    cluster_df.to_csv(PROJECT_ROOT / 'data' / 'processed' / 'cluster_labels.csv', index=False)
    
    skills_final['cluster'] = best_labels
    top5_dict = {}
    for cluster_id in range(1, best_k + 1):
        cluster_data = skills_final[skills_final['cluster'] == cluster_id].drop(columns=['cluster'])
        freqs = cluster_data.mean().sort_values(ascending=False)
        top5 = freqs.head(5)
        top5_str = ", ".join([f"{c} ({v:.0%})" for c, v in top5.items()])
        top5_dict[cluster_id] = top5_str

    stats = {
        'drop_columns': drop_columns,
        'dropped_jobs_count': len(dropped_jobs),
        'best_k': best_k,
        'best_score': best_score,
        'k_results': k_results,
        'top5': top5_dict
    }
    
    evaluate_clusters(cluster_df, jobs_df_eval, stats)
    return stats


def map_expertise_groups(categories: pd.Series, mapping: dict) -> pd.Series:
    """Gộp 'Job Expertise' (cột category) thành nhóm nghề; báo lỗi nếu còn giá trị chưa gộp."""
    unmapped = sorted(set(categories.dropna()) - set(mapping))
    if unmapped:
        raise ValueError(f"Chưa gộp category: {unmapped}. Bổ sung vào expertise_groups.json.")
    return categories.map(mapping)


def calculate_purity_fmeasure(crosstab):
    N = crosstab.sum().sum()
    purity = crosstab.max(axis=1).sum() / N
    
    f_measures = []
    weights = []
    for group in crosstab.columns:
        group_total = crosstab[group].sum()
        if group_total == 0: continue
        best_f = 0
        for cluster in crosstab.index:
            tp = crosstab.loc[cluster, group]
            cluster_total = crosstab.loc[cluster].sum()
            precision = tp / cluster_total if cluster_total > 0 else 0
            recall = tp / group_total if group_total > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            if f1 > best_f: best_f = f1
        f_measures.append(best_f)
        weights.append(group_total)
        
    overall_f = sum(f * w for f, w in zip(f_measures, weights)) / sum(weights) if sum(weights) > 0 else 0
    baseline_purity = crosstab.sum(axis=0).max() / N
    
    return purity, baseline_purity, overall_f

def evaluate_clusters(cluster_df, jobs_df, stats):
    merged = cluster_df.merge(jobs_df[['job_id', 'expertise_group']], on='job_id', how='inner')
    crosstab = pd.crosstab(merged['cluster'], merged['expertise_group'])
    purity, baseline_purity, overall_f = calculate_purity_fmeasure(crosstab)
    
    report_path = PROJECT_ROOT / 'reports' / 'purity_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Báo Cáo Phân Cụm & Purity\n\n")
        f.write(f"- **K đã chọn:** {stats['best_k']} — silhouette cao nhất trong các k hợp lệ (cụm nhỏ nhất ≥ {MIN_CLUSTER_SIZE} tin), silhouette = {stats['best_score']:.4f}\n")
        f.write(f"- **Số tin dùng để phân cụm:** {len(cluster_df)}; bị loại (còn < {MIN_SKILLS_PER_JOB} kỹ năng sau khi lọc): {stats['dropped_jobs_count']}\n")
        f.write(f"- **Kỹ năng bị loại** (xuất hiện > {FREQUENT_SKILL_RATIO:.0%} số tin, < {RARE_SKILL_MIN} tin, hoặc kỹ năng mềm/công cụ quản lý): {', '.join(stats['drop_columns'])}\n\n")
        
        f.write("## Kết quả các K đã thử\n\n")
        f.write(f"| K | Kích thước các cụm | Silhouette | Purity | Hợp lệ (cụm nhỏ nhất ≥ {MIN_CLUSTER_SIZE}) |\n")
        f.write("|---|---|---|---|---|\n")
        for res in stats['k_results']:
            sizes = " / ".join(map(str, sorted(res['sizes'], reverse=True)))
            mark = "✅" if res['valid'] else "—"
            f.write(f"| {res['k']} | {sizes} | {res['silhouette']:.4f} | {res['purity']:.4f} | {mark} |\n")
            
        f.write("\n## Top 5 kỹ năng mỗi cụm\n\n")
        for c, t5 in stats['top5'].items():
            f.write(f"- **Cụm {c}:** {t5}\n")
            
        f.write("\n## Đánh giá\n")
        f.write(f"- **Purity:** {purity:.4f}\n")
        f.write(f"- **Baseline Purity:** {baseline_purity:.4f}\n")
        f.write(f"- **Weighted F-measure:** {overall_f:.4f}\n\n")
        
        f.write("## Crosstab (Cluster x Expertise Group)\n\n")
        headers = ["Cluster"] + list(crosstab.columns)
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
        for cluster, row in crosstab.iterrows():
            f.write("| " + str(cluster) + " | " + " | ".join(map(str, row.values)) + " |\n")

if __name__ == '__main__':
    run_clustering()
