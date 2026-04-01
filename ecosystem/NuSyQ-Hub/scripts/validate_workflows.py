import os
import sys

wkdir = os.path.join(os.path.dirname(__file__), "..", ".github", "workflows")
errors = []
for fn in os.listdir(wkdir):
    path = os.path.join(wkdir, fn)
    if not os.path.isfile(path):
        continue
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        errors.append((fn, "binary or non-utf8"))
        continue
    issues = []
    if size == 0:
        issues.append("empty file")
    if "\t" in text:
        issues.append("contains TAB characters")
    if "```" in text:
        issues.append("contains code fence ```")
    # naive check for starting with code fence
    if text.lstrip().startswith("```"):
        issues.append("starts with code fence")
    if issues:
        errors.append((fn, ", ".join(issues)))

if not errors:
    print("No obvious issues found in workflow files")
    sys.exit(0)

print("Detected issues:")
for fn, reason in errors:
    print(f"- {fn}: {reason}")
sys.exit(2)
