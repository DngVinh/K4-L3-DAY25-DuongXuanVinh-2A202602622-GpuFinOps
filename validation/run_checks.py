"""Capture reproducible validation evidence inside the workspace."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["MPLCONFIGDIR"] = str(ROOT / ".venv" / "mplconfig")
    commands = [
        [sys.executable, "verify.py"],
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "validation/check_extensions.py"],
        [sys.executable, "bonus/litellm_tracker/demo.py"],
        ["git", "diff", "--exit-code", "--", "tests", "verify.py", "data"],
        ["git", "diff", "--check"],
    ]
    logs = [f"Python: {sys.version}\nWorkspace: {ROOT}\n"]
    failed = False
    for cmd in commands:
        result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
        label = " ".join(cmd[1:]) if cmd[0] == sys.executable else " ".join(cmd)
        logs.append(f"$ {label}\nExit code: {result.returncode}\n{result.stdout}{result.stderr}\n")
        print(f"{'PASS' if result.returncode == 0 else 'FAIL'}: {label}")
        failed |= result.returncode != 0
    target = (ROOT / "validation" / "results.txt").resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError("Evidence path must stay in workspace")
    target.write_text("\n".join(logs).rstrip() + "\n", encoding="utf-8")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
