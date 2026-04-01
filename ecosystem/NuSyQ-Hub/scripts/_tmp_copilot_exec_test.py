import os
import shutil
import subprocess

cmd = ["copilot", "-p", "Hello", "--allow-all", "--output-format", "json"]
resolved = shutil.which(cmd[0])
print("which", resolved)
print("exists", os.path.exists(resolved) if resolved else None)
if resolved:
    cmd = [resolved, *cmd[1:]]
print("cmd", cmd)
try:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    print("rc", p.returncode)
    print("out", p.stdout)
    print("err", p.stderr)
except FileNotFoundError as e:
    print("FileNotFoundError", e)
except Exception as e:
    print("Exception", type(e).__name__, e)
