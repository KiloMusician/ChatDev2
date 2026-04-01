import json

with open("docs/comprehensive_modernization_audit.json", encoding="utf-8") as f:
    data = json.load(f)
print("timestamp", data["timestamp"])
for repo, repo_data in data["repositories"].items():
    print("repo", repo)
    if "incomplete_modules" in repo_data:
        print("  incomplete modules tracked", len(repo_data["incomplete_modules"]))
