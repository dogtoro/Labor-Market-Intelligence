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
MIN_CLUSTER_SIZE = 15         # cụm < 15 tin coi là nhiễu/ngoại lai (nhãn -1), báo cáo riêng
MAX_NOISE_SHARE = 0.05        # k hợp lệ khi tổng tin nhiễu ≤ 5% số tin phân cụm
MIN_REAL_CLUSTERS = 3         # và có ≥ 3 cụm thật
NOISE_LABEL = -1
K_RANGE = range(4, 9)
MANUAL_DROPS = ['communication', 'teamwork', 'english', 'japanese', 'agile', 'jira', 'confluence']


def assign_noise(labels: np.ndarray, min_size: int = MIN_CLUSTER_SIZE) -> np.ndarray:
    """Cụm < min_size tin → NOISE_LABEL; cụm thật đánh số lại 1..m theo kích thước giảm dần
    (hoà thì theo nhãn gốc) để số cụm ổn định và dễ đọc."""
    sizes = pd.Series(labels).value_counts()
    real = sorted(sizes[sizes >= min_size].index, key=lambda c: (-sizes[c], c))
    remap = {old: new for new, old in enumerate(real, start=1)}
    return np.array([remap.get(l, NOISE_LABEL) for l in labels])


def evaluate_k(labels_raw: np.ndarray, D_square: np.ndarray, groups: np.ndarray) -> dict:
    """Đánh giá 1 giá trị k theo quy tắc nhiễu: silhouette, purity, baseline tính trên tin không phải nhiễu."""
    labels = assign_noise(labels_raw)
    keep = labels != NOISE_LABEL
    real_sizes = pd.Series(labels[keep]).value_counts().sort_index()
    n_noise = int((~keep).sum())
    n_real = len(real_sizes)
    sil = (silhouette_score(D_square[np.ix_(keep, keep)], labels[keep], metric='precomputed')
           if n_real >= 2 else float('nan'))
    crosstab = pd.crosstab(labels[keep], groups[keep])
    purity, baseline, f_measure = calculate_purity_fmeasure(crosstab)
    return {
        'labels': labels,
        'real_sizes': real_sizes.tolist(),
        'n_noise': n_noise,
        'noise_share': n_noise / len(labels),
        'silhouette': sil,
        'purity': purity,
        'baseline': baseline,
        'f_measure': f_measure,
        'valid': n_real >= MIN_REAL_CLUSTERS and n_noise <= MAX_NOISE_SHARE * len(labels),
    }


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
    drop_columns = [c for c in sorted(set(frequent_skills + MANUAL_DROPS + rare_skills)) if c in skills_df.columns]
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

    with open(PROJECT_ROOT / 'src' / 'models' / 'expertise_groups.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    jobs_df_eval = jobs_df.copy()
    jobs_df_eval['expertise_group'] = map_expertise_groups(jobs_df_eval['category'], mapping)
    groups = jobs_df_eval.set_index('job_id')['expertise_group'].reindex(skills_final.index).to_numpy()

    D_square = squareform(D)
    k_results = []
    for k in K_RANGE:
        res = evaluate_k(fcluster(Z, k, criterion='maxclust'), D_square, groups)
        res['k'] = k
        k_results.append(res)

    valid = [r for r in k_results if r['valid']]
    if not valid:
        raise ValueError(
            f"Không có k nào trong {list(K_RANGE)} hợp lệ (≥ {MIN_REAL_CLUSTERS} cụm thật, nhiễu ≤ {MAX_NOISE_SHARE:.0%}). "
            "Xem lại ngưỡng lọc hoặc khoảng k — không tự chọn k ngoài điều kiện."
        )
    best = max(valid, key=lambda r: (r['silhouette'], -r['k']))
    best_labels = best['labels']

    cluster_df = pd.DataFrame({'job_id': skills_final.index, 'cluster': best_labels}).sort_values('job_id')
    cluster_df.to_csv(PROJECT_ROOT / 'data' / 'processed' / 'cluster_labels.csv', index=False)

    top5_dict = {}
    for cluster_id in sorted(set(best_labels)):
        cluster_data = skills_final[best_labels == cluster_id]
        freqs = cluster_data.mean().sort_values(ascending=False, kind='mergesort')
        top5_dict[cluster_id] = ", ".join(f"{c} ({v:.0%})" for c, v in freqs.head(5).items())

    stats = {
        'drop_columns': drop_columns,
        'dropped_jobs_count': len(dropped_jobs),
        'best_k': best['k'],
        'best_score': best['silhouette'],
        'k_results': k_results,
        'top5': top5_dict,
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
    real = merged[merged['cluster'] != NOISE_LABEL]
    crosstab = pd.crosstab(real['cluster'], real['expertise_group'])
    purity, baseline_purity, overall_f = calculate_purity_fmeasure(crosstab)

    n_total = jobs_df['job_id'].nunique()
    n_used = len(cluster_df)
    sizes = cluster_df.loc[cluster_df['cluster'] != NOISE_LABEL, 'cluster'].value_counts().sort_index()
    n_noise = int((cluster_df['cluster'] == NOISE_LABEL).sum())
    n_real_jobs = n_used - n_noise

    report_path = PROJECT_ROOT / 'reports' / 'purity_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Báo Cáo Phân Cụm & Purity\n\n")
        f.write(f"- **K đã chọn:** {stats['best_k']} → **{len(sizes)} cụm thật** + {n_noise} tin nhiễu "
                f"({n_noise / n_used:.1%}); silhouette = {stats['best_score']:.4f}\n")
        f.write(f"- **Quy tắc chọn k(DECISIONS 04/10):** cụm < {MIN_CLUSTER_SIZE} tin coi là "
                f"**nhiễu/ngoại lai** (nhãn `{NOISE_LABEL}` trong `cluster_labels.csv`); k hợp lệ khi có ≥ {MIN_REAL_CLUSTERS} cụm thật "
                f"và nhiễu ≤ {MAX_NOISE_SHARE:.0%}; chọn silhouette cao nhất (tính trên tin không phải nhiễu).\n")
        f.write(f"- **Số tin dùng để phân cụm:** {n_used}; bị loại (còn < {MIN_SKILLS_PER_JOB} kỹ năng sau khi lọc): {stats['dropped_jobs_count']}\n")
        f.write(f"- **Kỹ năng bị loại** (xuất hiện > {FREQUENT_SKILL_RATIO:.0%} số tin, < {RARE_SKILL_MIN} tin, hoặc kỹ năng mềm/công cụ quản lý): {', '.join(stats['drop_columns'])}\n\n")

        f.write("## Kết quả các K đã thử\n\n")
        f.write("| K | Cụm thật (số tin) | Tin nhiễu | Silhouette | Purity | Baseline | Hợp lệ |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for res in stats['k_results']:
            real_sizes = " / ".join(map(str, sorted(res['real_sizes'], reverse=True)))
            mark = "✅" if res['valid'] else "—"
            f.write(f"| {res['k']} | {real_sizes} | {res['n_noise']} ({res['noise_share']:.1%}) | {res['silhouette']:.4f} "
                    f"| {res['purity']:.4f} | {res['baseline']:.4f} | {mark} |\n")

        f.write("\n## Top 5 kỹ năng mỗi cụm\n\n")
        for c, t5 in stats['top5'].items():
            name = "Nhiễu" if c == NOISE_LABEL else f"Cụm {c}"
            n = n_noise if c == NOISE_LABEL else int(sizes[c])
            f.write(f"- **{name}** ({n} tin): {t5}\n")

        f.write("\n## Đánh giá (trên tin không phải nhiễu)\n")
        f.write(f"- **Purity:** {purity:.4f}\n")
        f.write(f"- **Baseline Purity:** {baseline_purity:.4f}\n")
        f.write(f"- **Weighted F-measure:** {overall_f:.4f}\n\n")

        big_id, big_n = sizes.idxmax(), int(sizes.max())
        small = [c for c in sizes.index if c != big_id]
        f.write("## Nhận xét & hạn chế\n\n")
        f.write(f"- **Cấu trúc cụm yếu:** silhouette = {stats['best_score']:.3f} (gần 0) — tổ hợp kỹ năng trên ITviec "
                "**không tách thành các nhóm nghề rõ ràng**. Đây là kết quả, không phải lỗi.\n")
        f.write("- **Kết quả nhạy với từ điển:** sau khi bổ sung dạng số nhiều (vd. \"APIs\", 04/10), `api` vượt ngưỡng 40% và bị loại; "
                "quy tắc cũ (mọi cụm ≥ 15 tin) không còn k nào hợp lệ vì luôn có vài cụm 2–13 tin. "
                "Đổi sang quy tắc nhiễu (`docs/DECISIONS.md` 04/10) — đây cũng là bằng chứng phân cụm không ổn định.\n")
        f.write(f"- **Một cụm \"chung\" chiếm {big_n}/{n_real_jobs} tin không phải nhiễu ({big_n / n_real_jobs:.0%})** "
                f"(cụm {big_id}: {stats['top5'][big_id]}) và trộn lẫn mọi nhóm nghề (xem crosstab).\n")
        f.write("- **Các cụm nhỏ có đặc trưng rõ hơn:** "
                + "; ".join(f"cụm {c} ({int(sizes[c])} tin): {', '.join(stats['top5'][c].split(', ')[:2])}" for c in small)
                + ".\n")
        f.write(f"- **Purity {purity:.3f} so với baseline {baseline_purity:.3f}** (baseline = gom tất cả vào 1 cụm, "
                "tức tỷ lệ nhóm nghề đông nhất): cụm kỹ năng khớp nhóm nghề tốt hơn baseline nhưng còn xa mức tách bạch; "
                f"F-measure {overall_f:.3f}.\n")
        f.write(f"- **Phạm vi:** {n_used}/{n_total} tin ({n_used / n_total:.0%}) được phân cụm, trong đó {n_noise} tin là nhiễu; "
                f"{n_total - n_used} tin ({(n_total - n_used) / n_total:.0%}) bị loại vì không bắt được kỹ năng nào "
                f"hoặc còn < {MIN_SKILLS_PER_JOB} kỹ năng sau khi bỏ kỹ năng mềm/hiếm/quá phổ biến.\n")
        f.write("- Nhóm nghề so sánh lấy từ 72 giá trị \"Job Expertise\" gộp thành 10 nhóm (`src/models/expertise_groups.json`, "
                "ASSUMPTIONS A16 — đã review 04/10).\n\n")

        f.write("## Crosstab (Cluster x Expertise Group, không gồm nhiễu)\n\n")
        headers = ["Cluster"] + list(crosstab.columns)
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
        for cluster, row in crosstab.iterrows():
            f.write("| " + str(cluster) + " | " + " | ".join(map(str, row.values)) + " |\n")

if __name__ == '__main__':
    run_clustering()
