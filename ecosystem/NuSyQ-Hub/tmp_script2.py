import json

with open("docs/comprehensive_modernization_audit.json", encoding="utf-8") as f:
    data = json.load(f)
for repo, repo_data in data["repositories"].items():
    print("repo", repo)
    for entry in repo_data.get("incomplete_modules", [])[:5]:
        print(" -", entry["file"], entry["issues"])
