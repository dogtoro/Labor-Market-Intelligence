import pandas as pd
import json
import re

# Load data
df = pd.read_parquet('data/processed/jobs_clean.parquet')
sample = df.sample(20, random_state=42)

with open('src/skills/skill_dict.json', 'r', encoding='utf-8') as f:
    skill_dict = json.load(f)

patterns = {}
for skill, aliases in skill_dict.items():
    escaped = [re.escape(a) for a in aliases]
    pat = '|'.join(escaped)
    patterns[skill] = re.compile(rf'(?<![\w+#.])(?:{pat})(?![\w+#])', re.IGNORECASE)

with open('reports/A7_evaluation.md', 'w', encoding='utf-8') as f:
    f.write('# A7 Evaluation - 20 Random JDs\n\n')
    for i, row in sample.iterrows():
        text = str(row['jd_text'])
        f.write(f'## Job: {row["title"]} ({row["company"]})\n')
        extracted = []
        for skill, pattern in patterns.items():
            if pattern.search(text):
                extracted.append(skill)
        f.write(f'**Extracted Skills:** {", ".join(extracted)}\n\n')

print("A7 Evaluation generated.")
