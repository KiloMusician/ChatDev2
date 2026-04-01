"""Script to download failed GitHub Actions run logs for a given repo/branch."""

import json
import os
import subprocess

REPO = "KiloMusician/NuSyQ-Hub"
BRANCH = "feature/batch-001"
OUTDIR = os.path.join(os.path.dirname(__file__), "ci_logs")
os.makedirs(OUTDIR, exist_ok=True)


def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


# Get runs
gh_run_list_cmd = (
    f"gh run list --repo {REPO} --branch {BRANCH} --limit 200 --json url,number,conclusion,workflowName,createdAt"
)
rc, out, err = run_cmd(gh_run_list_cmd)
if rc != 0:
    print("gh run list failed", err)
    raise SystemExit(1)

runs = json.loads(out)
print(f"Found {len(runs)} runs for branch {BRANCH}")
found_any = False
for r in runs:
    if r.get("conclusion") != "failure":
        continue
    url = r.get("url") or ""
    run_id = url.rstrip("/").split("/")[-1]
    wf = r.get("workflowName")
    print(f"Checking run {run_id} ({wf})")
    jobs_cmd = f"gh api repos/{REPO}/actions/runs/{run_id}/jobs"
    rc2, out2, err2 = run_cmd(jobs_cmd)
    if rc2 != 0:
        print(f"  failed to fetch jobs for run {run_id}: {err2}")
        continue
    jobs_obj = json.loads(out2)
    jobs = jobs_obj.get("jobs", [])
    print(f"  jobs count: {len(jobs)}")
    if len(jobs) == 0:
        continue
    found_any = True
    # download log
    outpath = os.path.join(OUTDIR, f"run_{run_id}.log")
    print(f"  streaming logs to {outpath}")
    log_cmd = f"gh run view {run_id} --repo {REPO} --log"
    rc3, out3, err3 = run_cmd(log_cmd)
    if rc3 != 0:
        print(f"  failed to view logs for {run_id}: {err3}")
        continue
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(out3)
    print(f"  saved logs for run {run_id}")

if not found_any:
    print("No failed runs with job logs found.")
else:
    print("Saved logs in", OUTDIR)
