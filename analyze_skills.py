import pandas as pd
import re
import ast


# 1. THE DICTIONARY (The "Brain")

# We use Regex patterns to catch variations (e.g., "Node.js" or "NodeJS")
SKILL_KEYWORDS = {
    # Languages
    "Python": r"\bpython\b",
    "SQL": r"\bsql\b",
    "Java": r"\bjava\b",  # Will not match "Javascript" due to \b
    "JavaScript": r"\b(javascript|js)\b",
    "TypeScript": r"\btypescript\b",
    "C++": r"\bc\+\+\b",
    "C#": r"\bc#|csharp\b",
    "R": r"\bR\b",  # Capital R only, with boundaries
    "PHP": r"\bphp\b",
    "Go": r"\bgolang\b|\bGo\b",
    "VBA": r"\bvba\b",
    # Frameworks & Libraries (Data & Web)
    "React": r"\breact(?:\.js)?\b",
    "Angular": r"\bangular\b",
    "Vue.js": r"\bvue(?:\.js)?\b",
    "Spring Boot": r"\bspring\s?boot\b",
    "Django": r"\bdjango\b",
    "Flask": r"\bflask\b",
    "FastAPI": r"\bfastapi\b",
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "Scikit-Learn": r"\bscikit-learn|sklearn\b",
    "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b",
    "Spark": r"\bspark\b",
    "Hadoop": r"\bhadoop\b",
    "Airflow": r"\bairflow\b",
    # Tools & Platforms
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes|k8s\b",
    "AWS": r"\baws|amazon web services\b",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp|google cloud\b",
    "Git": r"\bgit\b",
    "Jenkins": r"\bjenkins\b",
    "Terraform": r"\bterraform\b",
    "Snowflake": r"\bsnowflake\b",
    "Databricks": r"\bdatabricks\b",
    # Visualization & BI
    "Power BI": r"\bpower\s?bi\b",
    "Tableau": r"\btableau\b",
    "Excel": r"\bexcel\b",
    # Concepts (Good for Analytics)
    "Machine Learning": r"\bmachine learning|ml\b",
    "Deep Learning": r"\bdeep learning|dl\b",
    "NLP": r"\bnlp|natural language processing\b",
    "Big Data": r"\bbig data\b",
    "DevOps": r"\bdevops\b",
    "Agile": r"\bagile|scrum\b",
}


def clean_text(text):
    """
    Cleans the description text:
    1. Removes new lines and extra spaces.
    2. Converts to lowercase for easier matching.
    """
    if pd.isna(text):
        return ""
    # Replace newlines with space
    text = text.replace("\n", " ").replace("\r", "")
    return text.lower()


def extract_skills(description):
    """
    Scans the description against the SKILL_KEYWORDS dictionary.
    Returns a list of unique skills found.
    """
    found_skills = []
    clean_desc = clean_text(description)

    for skill_name, pattern in SKILL_KEYWORDS.items():
        # Search using Regex (Ignore Case)
        if re.search(pattern, clean_desc):
            found_skills.append(skill_name)

    return found_skills


# 2. EXECUTION LOGIC

print("📂 Loading data...")
# Load the CSV you generated in Phase 1
df = pd.read_csv("morocco_data_market.csv")

print(f"📊 Analyzing {len(df)} job descriptions...")

# Apply the extraction function to the 'description' column
# We use a lambda function to apply it row by row
df["extracted_skills"] = df["description"].apply(extract_skills)

# Count how many skills we found on average
avg_skills = df["extracted_skills"].apply(len).mean()
print(f"✅ Extraction complete. Average skills per job: {avg_skills:.1f}")

# 3. SAVE THE CLEAN DATA

# We only keep the columns we need for the App
final_df = df[
    [
        "title",
        "company",
        "location",
        "date_posted",
        "job_url",
        "searched_city",
        "searched_role",
        "extracted_skills",
    ]
]

output_file = "processed_jobs_for_api.json"

# Save as JSON (Better for Web Apps/API than CSV because it handles Lists [] better)
final_df.to_json(output_file, orient="records", indent=2)

print(f"💾 Saved processed data to {output_file}")

# 4. BONUS: PRINT TOP INSIGHTS (To verify it works)



print("\n🚀 TOP 10 SKILLS IN MOROCCO (Based on your data):")
all_skills = [skill for sublist in df["extracted_skills"] for skill in sublist]
from collections import Counter

top_skills = Counter(all_skills).most_common(10)

for skill, count in top_skills:
    print(f"{skill}: {count} jobs")

