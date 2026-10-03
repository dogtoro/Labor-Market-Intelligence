import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import fisher_exact, chi2_contingency, false_discovery_control

from src.models.features import (
    load_and_verify_data,
    extract_location_flags,
    clean_level_feature
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = PROJECT_ROOT / "reports"
FIG_DIR = REPORT_DIR / "figures"

MIN_SKILL_TOTAL = 5   # bỏ kỹ năng xuất hiện < 5 tin (cả 2 nhóm) — quá hiếm để kiểm định
ALPHA = 0.05
PCT_HAS, PCT_NO, DIFF = 'Có lương (%)', 'Không lương (%)', 'Chênh lệch (%)'


def compare_groups(flags: pd.DataFrame, has_mask: pd.Series, min_total: int = 0) -> pd.DataFrame:
    """So sánh tỷ lệ xuất hiện của từng cột nhị phân giữa nhóm có lương và không lương.

    Fisher exact (2 phía) cho từng cột, hiệu chỉnh Benjamini–Hochberg trên tất cả các cột được kiểm định.
    Bỏ các cột có tổng số tin < min_total.

    Returns:
        DataFrame index = tên cột, gồm PCT_HAS, PCT_NO, DIFF (tỷ lệ 0–1), p_value, adj_p_value.
    """
    has_mask = has_mask.astype(bool)
    n_has, n_no = int(has_mask.sum()), int((~has_mask).sum())
    rows = {}
    for col in flags.columns:
        c_has = int(flags.loc[has_mask, col].sum())
        c_no = int(flags.loc[~has_mask, col].sum())
        if c_has + c_no < min_total:
            continue
        p_val = fisher_exact([[c_has, n_has - c_has], [c_no, n_no - c_no]], alternative='two-sided').pvalue
        rows[col] = {PCT_HAS: c_has / n_has, PCT_NO: c_no / n_no, DIFF: c_has / n_has - c_no / n_no, 'p_value': p_val}

    result = pd.DataFrame.from_dict(rows, orient='index')
    result['adj_p_value'] = false_discovery_control(result['p_value'], method='bh')
    return result


def top_by_abs_diff(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Top n theo |chênh lệch| giảm dần; hoà thì theo tên (thứ tự ổn định giữa các lần chạy)."""
    order = (
        pd.DataFrame({'abs_diff': df[DIFF].abs().round(10), 'name': df.index}, index=df.index)
        .sort_values(['abs_diff', 'name'], ascending=[False, True], kind='mergesort')
        .index
    )
    return df.loc[order].head(n)


def _format_pct_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in (PCT_HAS, PCT_NO):
        out[col] = out[col].apply(lambda x: f"{x:.1%}")
    out[DIFF] = out[DIFF].apply(lambda x: f"{x:+.1%}")
    for col in ('p_value', 'adj_p_value'):
        out[col] = out[col].apply(lambda x: f"{x:.4f}")
    return out

def _md_table(df: pd.DataFrame, index_name: str) -> list[str]:
    cols = [index_name] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for idx, row in df.iterrows():
        lines.append("| " + " | ".join([str(idx)] + [str(v) for v in row.values]) + " |")
    return lines

def run_bias_analysis():
    print("Loading data for Bias Analysis...")
    jobs_df, skills_df = load_and_verify_data()
    
    jobs_df['has_salary'] = jobs_df['salary_status'] != 'undisclosed'
    
    jobs_df = jobs_df.set_index('job_id')
    if 'job_id' in skills_df.columns:
        skills_df = skills_df.set_index('job_id')
        
    merged = jobs_df.join(skills_df, how='left')
    skill_columns = [c for c in skills_df.columns if c in merged.columns]
    merged[skill_columns] = merged[skill_columns].fillna(0).astype(int)
    
    has_mask = merged['has_salary']
    no_mask = ~has_mask
    
    n_has = has_mask.sum()
    n_no = no_mask.sum()
    
    print(f"Có lương: {n_has} tin. Không lương: {n_no} tin.")
    
    lines = [
        "# Phân Tích Thiên Lệch (Bias Analysis)",
        "",
        "Báo cáo này phân tích sự khác biệt (thiên lệch) giữa nhóm tin có công bố lương (dùng để train Decision Tree) và nhóm không công bố lương.",
        f"- **Nhóm có lương (Train):** {n_has} tin",
        f"- **Nhóm không lương:** {n_no} tin",
        "",
        "## 1. Thiên lệch theo Kỹ năng",
        ""
    ]
    
    # ---------------------------
    # 1. Kỹ năng
    # ---------------------------
    print("Analyzing Skills...")
    sk_df = compare_groups(merged[skill_columns], has_mask, min_total=MIN_SKILL_TOTAL)
    sk_df.index.name = 'Kỹ năng'
    top_diff_skills = top_by_abs_diff(sk_df, 15)
    format_sk_df = _format_pct_table(top_diff_skills)

    sig_count = int((sk_df['adj_p_value'] < ALPHA).sum())
    if sig_count == 0:
        lines.append(f"Fisher exact cho {len(sk_df)} kỹ năng (xuất hiện ≥ {MIN_SKILL_TOTAL} tin), hiệu chỉnh Benjamini–Hochberg. Không có kỹ năng nào khác biệt có ý nghĩa thống kê sau khi hiệu chỉnh bội (adj_p < 0.05). Dưới đây là top 15 kỹ năng có chênh lệch tuyệt đối lớn nhất:")
    else:
        lines.append(f"Fisher exact cho {len(sk_df)} kỹ năng (xuất hiện ≥ {MIN_SKILL_TOTAL} tin), hiệu chỉnh Benjamini–Hochberg. Có {sig_count} kỹ năng khác biệt ý nghĩa thống kê (adj_p < 0.05). Dưới đây là top 15 kỹ năng có chênh lệch tuyệt đối lớn nhất:")
        
    lines.append("")
    lines.extend(_md_table(format_sk_df, "Kỹ năng"))
    lines.append("")
        
    # Biểu đồ top 10 kỹ năng chênh lệch nhiều nhất
    top_plot = top_diff_skills.head(10).iloc[::-1]  # đảo để mục chênh lệch lớn nhất nằm trên cùng
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['green' if x > 0 else 'red' for x in top_plot['Chênh lệch (%)']]
    ax.barh(top_plot.index, top_plot['Chênh lệch (%)'] * 100, color=colors)
    ax.set_xlabel('Chênh lệch % (Có lương - Không lương)')
    ax.set_title(f'Top 10 kỹ năng chênh lệch nhiều nhất ({sig_count} kỹ năng có adj p < 0.05)')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIG_DIR / "bias_skills.png")
    plt.close()
        
    # ---------------------------
    # 2. Địa điểm
    # ---------------------------
    print("Analyzing Location...")
    loc_flags = extract_location_flags(merged)
    loc_df = compare_groups(loc_flags, has_mask)
    loc_df.index = [c.replace('loc_', '').upper() for c in loc_df.index]
    loc_df.index.name = 'Địa điểm'
    loc_sig = loc_df[loc_df['adj_p_value'] < ALPHA]

    loc_display = _format_pct_table(loc_df)

    lines.append("## 2. Thiên lệch theo Địa điểm")
    lines.append("")
    lines.append("Multi-hot theo 3 thành phố chính và 'Khác' (một tin có thể ở nhiều nơi nên tổng % mỗi cột có thể > 100%). "
                 "Fisher exact cho từng địa điểm, hiệu chỉnh Benjamini–Hochberg cho 4 phép kiểm định.")
    lines.append("")
    lines.extend(_md_table(loc_display, "Địa điểm"))
    lines.append("")
    
    # ---------------------------
    # 3. Cấp bậc
    # ---------------------------
    print("Analyzing Level...")
    merged['level_group'] = clean_level_feature(merged)
    
    level_crosstab = pd.crosstab(merged['level_group'], merged['has_salary'])
    # format columns
    level_crosstab.columns = ['Không lương', 'Có lương']
    
    chi2, p_level, dof, exp = chi2_contingency(level_crosstab)
    
    # Calculate % within column
    level_pct = level_crosstab.div(level_crosstab.sum(axis=0), axis=1) * 100
    level_pct['Chênh lệch (%)'] = level_pct['Có lương'] - level_pct['Không lương']
    
    level_display = level_crosstab.copy()
    level_display['Có lương (%)'] = level_pct['Có lương'].apply(lambda x: f"{x:.1f}%")
    level_display['Không lương (%)'] = level_pct['Không lương'].apply(lambda x: f"{x:.1f}%")
    level_display['Chênh lệch (%)'] = level_pct['Chênh lệch (%)'].apply(lambda x: f"{x:+.1f}%")
    
    lines.append("## 3. Thiên lệch theo Cấp bậc (Level)")
    lines.append("")
    lines.append(f"Kiểm định Chi-Square test trên toàn bộ bảng chéo: p-value = {p_level:.4e}")
    if p_level < ALPHA:
        lines.append("→ Có sự khác biệt ý nghĩa về phân phối cấp bậc giữa 2 nhóm.")
    lines.append("")
    lines.extend(_md_table(level_display[['Có lương', 'Có lương (%)', 'Không lương', 'Không lương (%)', 'Chênh lệch (%)']], "Cấp bậc"))
    lines.append("")
    
    # Plot Level
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(level_pct))
    width = 0.35
    ax.bar(x - width/2, level_pct['Có lương'], width, label='Có lương')
    ax.bar(x + width/2, level_pct['Không lương'], width, label='Không lương')
    ax.set_ylabel('% trong nhóm')
    ax.set_title('Phân bố Cấp Bậc: Có Lương vs Không Lương')
    ax.set_xticks(x)
    ax.set_xticklabels(level_pct.index)
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "bias_levels.png")
    plt.close()
    
    # ---------------------------
    # 4. Tiền tệ — chỉ mô tả nhóm có lương (tin không lương không có thông tin tiền tệ)
    # ---------------------------
    print("Analyzing Currency...")
    currency_counts = merged.loc[has_mask, 'currency_original'].value_counts().sort_index()
    usd_count = int(currency_counts.get('USD', 0))

    lines.append("## 4. Đặc điểm nhóm có lương: tiền tệ (mô tả, không phải so sánh)")
    lines.append("")
    lines.append("Tin không công bố lương không có thông tin tiền tệ, nên đây **không phải** phép so sánh 2 nhóm.")
    lines.append("")
    lines.extend(_md_table(currency_counts.to_frame("Số tin"), "Tiền tệ (`currency_original`)"))
    lines.append("")
    lines.append(f"{usd_count}/{n_has} tin có lương ({usd_count / n_has:.1%}) ghi bằng USD. "
                 "**Giả thuyết (chưa kiểm chứng):** nhóm có lương có thể lệch về công ty nước ngoài/outsourcing; "
                 "tuy nhiên ghi lương bằng USD cũng là cách hiển thị phổ biến trên ITviec, nên không suy ra được loại công ty.")
    lines.append("")

    # ---------------------------
    # 5. Kết luận — chỉ khẳng định điều có ý nghĩa thống kê
    # ---------------------------
    lines.append("## 5. Kết luận phạm vi áp dụng")
    lines.append("")
    lines.append("Mô hình lương ở Task 3 chỉ học từ tin có công bố lương. So với tin không công bố lương:")
    lines.append("")
    if len(loc_sig):
        parts = [f"{loc} {row['Có lương (%)']:.1%} so với {row['Không lương (%)']:.1%} (adj p = {row['adj_p_value']:.4f})"
                 for loc, row in loc_sig.iterrows()]
        lines.append(f"1. **Địa điểm — có thiên lệch có ý nghĩa thống kê:** {'; '.join(parts)}. "
                     "Kết quả dự đoán lương vì vậy đại diện cho tin ở Hà Nội nhiều hơn so với thị trường chung.")
    else:
        lines.append("1. **Địa điểm:** không có khác biệt có ý nghĩa thống kê (adj p ≥ 0.05).")
    if sig_count == 0:
        lines.append("2. **Kỹ năng — không có thiên lệch có ý nghĩa thống kê:** không kỹ năng nào có adj p < 0.05 "
                     "(các chênh lệch trong bảng mục 1 chỉ là quan sát, không đủ bằng chứng).")
    else:
        sig_names = ", ".join(sk_df[sk_df['adj_p_value'] < 0.05].index)
        lines.append(f"2. **Kỹ năng — {sig_count} kỹ năng khác biệt có ý nghĩa thống kê:** {sig_names}.")
    if p_level < ALPHA:
        lines.append(f"3. **Cấp bậc — phân phối khác biệt có ý nghĩa thống kê** (chi-square p = {p_level:.4f}).")
    else:
        unk = level_pct.loc['Unknown'] if 'Unknown' in level_pct.index else None
        note = (f" Quan sát: tỷ lệ không suy được cấp bậc ở nhóm có lương thấp hơn ({unk['Có lương']:.1f}% so với "
                f"{unk['Không lương']:.1f}%), nhưng chưa đủ bằng chứng.") if unk is not None else ""
        lines.append(f"3. **Cấp bậc — không khác biệt có ý nghĩa thống kê** (chi-square p = {p_level:.4f} ≥ 0.05).{note}")
    lines.append(f"4. **Tiền tệ:** {usd_count / n_has:.1%} tin có lương ghi USD — chỉ là đặc điểm mô tả (mục 4), không kết luận về loại công ty.")
    lines.append("")
    lines.append("**Liên hệ với mô hình Task 3:** cây quyết định dựa chủ yếu vào cấp bậc, mà phân phối cấp bậc không khác biệt "
                 "có ý nghĩa giữa 2 nhóm; nhưng địa điểm thì có. Vì vậy kết quả dự đoán lương nên được hiểu là đại diện "
                 "cho tin có công bố lương, nghiêng về Hà Nội, chứ không phải toàn bộ thị trường.")
    lines.append("")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "bias_analysis.md").write_text("\n".join(lines) + "\n", encoding='utf-8')
    print(f"Report -> {REPORT_DIR / 'bias_analysis.md'}")

if __name__ == '__main__':
    run_bias_analysis()
