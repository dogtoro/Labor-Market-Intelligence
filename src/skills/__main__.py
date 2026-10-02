import pandas as pd
from pathlib import Path
from src.skills.extractor import build_skill_matrix

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def main():
    print("Loading jobs_clean.parquet...")
    clean_path = PROJECT_ROOT / "data" / "processed" / "jobs_clean.parquet"
    if not clean_path.exists():
        print(f"Error: File not found {clean_path}")
        return
        
    df = pd.read_parquet(clean_path)
    print(f"Loaded {len(df)} jobs.")
    
    if "is_duplicate" in df.columns:
        df = df[~df["is_duplicate"]]
        print(f"After deduplication filter: {len(df)} jobs.")
    
    print("Extracting skills...")
    dict_path = PROJECT_ROOT / "src" / "skills" / "skill_dict.json"
    matrix = build_skill_matrix(df, dict_path=dict_path)
    
    # Filter jobs with no skills
    skill_cols = [c for c in matrix.columns if c != "job_id"]
    matrix = matrix[matrix[skill_cols].sum(axis=1) > 0]
    print(f"Filtered jobs with no skills, remaining: {len(matrix)}")
    
    from src.contract import validate_skills
    validate_skills(matrix)
    
    out_path = PROJECT_ROOT / "data" / "processed" / "skill_matrix.parquet"
    print(f"Saving to {out_path}...")
    matrix.to_parquet(out_path, index=False)
    print("Done! Matrix shape:", matrix.shape)

if __name__ == "__main__":
    main()
