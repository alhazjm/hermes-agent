"""Container entrypoint.

Starts Hermes in the configured RUN_MODE, registers the template skill,
loads cron jobs, and installs the budget guard hook.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from budget_guard import load_from_env, write_summary

APP = Path("/app")
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/root/.hermes"))


def install_skill() -> None:
    """Copy the template skill into Hermes' user-skills directory."""
    target = HERMES_HOME / "skills"
    target.mkdir(parents=True, exist_ok=True)
    src = APP / "skills"
    for skill_dir in src.iterdir():
        if skill_dir.is_dir():
            dest = target / skill_dir.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(skill_dir, dest)


def install_crons() -> None:
    """Translate crons/jobs.yaml into Hermes cron entries."""
    subprocess.run(
        ["hermes", "cron", "import", str(APP / "crons" / "jobs.yaml")],
        check=True,
    )


def main() -> int:
    state = load_from_env()
    os.environ["__BUDGET_STATE_JSON"] = str(state.summary())

    install_skill()
    install_crons()

    mode = os.environ.get("RUN_MODE", "cli").lower()
    try:
        if mode == "cli":
            rc = subprocess.run(["hermes"], check=False).returncode
        elif mode == "telegram":
            rc = subprocess.run(["hermes", "gateway", "start"], check=False).returncode
        else:
            print(f"Unknown RUN_MODE: {mode}", file=sys.stderr)
            return 2
    finally:
        write_summary(state, APP / "out" / "session_budget.json")
    return rc


if __name__ == "__main__":
    sys.exit(main())
