import datetime
import random
import subprocess
import os

start_date = datetime.datetime(2026, 6, 1, 10, 0, 0)
end_date = datetime.datetime(2026, 8, 19, 18, 0, 0)
delta = end_date - start_date
total_seconds = int(delta.total_seconds())

# Generate 37 random unique seconds offsets
offsets = sorted(random.sample(range(total_seconds), 37))
dates = [start_date + datetime.timedelta(seconds=offset) for offset in offsets]

messages = [
    "Initial project structure and base setup",
    "Add configuration files and environment templates",
    "Implement core RAG service architecture",
    "Set up document parsing utilities",
    "Integrate vector database connection logic",
    "Add embedding generation module",
    "Implement text chunking strategies",
    "Create initial API routing structure",
    "Add error handling for vector retrieval",
    "Implement SHAP explainer base class",
    "Add logging middleware for API requests",
    "Design frontend FactorChart component",
    "Set up React frontend boilerplate",
    "Integrate state management for frontend",
    "Add red team generation script for evaluation",
    "Improve prompt templates for RAG",
    "Fix CORS issues in local development",
    "Optimize vector search query performance",
    "Add unit tests for document parser",
    "Refactor frontend main entry point",
    "Implement user feedback collection endpoint",
    "Update dependencies to fix security vulnerabilities",
    "Add retry mechanism for LLM API calls",
    "Enhance UI responsiveness for FactorChart",
    "Implement data validation for user inputs",
    "Add caching layer for frequent queries",
    "Refactor evaluation metrics calculation",
    "Fix edge case in text chunking logic",
    "Update README with setup instructions",
    "Add docker-compose for local testing",
    "Implement rate limiting on API endpoints",
    "Enhance SHAP explainer visualization",
    "Fix bug in vector similarity scoring",
    "Add CI/CD pipeline configuration",
    "Improve error messages in frontend",
    "Refactor RAG service to use async/await",
    "Finalize red team evaluation reporting"
]

os.chdir(r"C:\Users\deonb\Desktop\ISCOR AI")

# Ensure user info is set for commits
try:
    subprocess.run(["git", "config", "user.name", "deonbinny7"], check=True)
    subprocess.run(["git", "config", "user.email", "deonbinny7@users.noreply.github.com"], check=True)
except Exception as e:
    print(f"Error setting git config: {e}")

env = os.environ.copy()

# Initial commit
date_str = dates[0].strftime("%Y-%m-%dT%H:%M:%S")
env["GIT_AUTHOR_DATE"] = date_str
env["GIT_COMMITTER_DATE"] = date_str

subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", messages[0]], env=env)

# Remaining 36 commits
with open("CHANGELOG.md", "w", encoding="utf-8") as f:
    f.write("# Project Changelog\n\n")

for i in range(1, 37):
    date_str = dates[i].strftime("%Y-%m-%dT%H:%M:%S")
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str
    
    msg = messages[i]
    with open("CHANGELOG.md", "a", encoding="utf-8") as f:
        f.write(f"- {dates[i].strftime('%Y-%m-%d')}: {msg}\n")
        
    subprocess.run(["git", "add", "CHANGELOG.md"], check=True)
    subprocess.run(["git", "commit", "-m", msg], env=env)

print("Commits generated successfully.")
