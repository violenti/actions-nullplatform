#!/usr/bin/env python3
"""Run real local actions/workflows with act and verify expected failures."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ("feature", "feat/add-login", "", True),
    ("fix", "fix/bug-123", "", True),
    ("dependabot", "dependabot/npm/pkg-1", "", True),
    ("release-please", "release-please--branches--main", "", True),
    ("invalid", "my-feature", "", False),
    ("empty-description", "feat/", "", False),
    ("unknown-type", "unknown/change", "", False),
    ("custom-valid", "ticket/ABC-123", "^ticket/[A-Z]+-[0-9]+$", True),
    ("custom-invalid", "feat/change", "^ticket/[A-Z]+-[0-9]+$", False),
    ("push", None, "", True),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["all", "run-first", "branch"], default="all")
    parser.add_argument("--list", action="store_true", help="List cases without Docker")
    parser.add_argument("--dry-run", action="store_true", help="Validate act execution plans only")
    args = parser.parse_args()
    if args.list:
        if args.suite != "branch":
            print("run-first: priority, fallback, reversed, exact-match, missing, empty, failure, manager")
        if args.suite != "run-first":
            for name, *_ in CASES:
                print(f"branch: {name}")
        return 0
    act = shutil.which(os.environ.get("ACT_BIN", "act"))
    if not act:
        parser.exit(2, "act not found. Install nektos/act or set ACT_BIN.\n")
    if not args.dry_run:
        docker = shutil.which("docker")
        if not docker or subprocess.run([docker, "info"], capture_output=True).returncode:
            parser.exit(2, "Docker is unavailable. Start Docker and retry.\n")
    failed = []
    with tempfile.TemporaryDirectory(prefix="nullplatform-act-") as temp:
        empty = Path(temp) / "empty"
        empty.touch()
        common = [act, "--directory", str(ROOT), "--platform",
                  "ubuntu-24.04=" + os.environ.get("ACT_RUNNER_IMAGE", "catthehacker/ubuntu:act-24.04"),
                  "--container-architecture", os.environ.get("ACT_ARCH", "linux/amd64"),
                  "--secret-file", str(empty), "--env-file", str(empty),
                  "--var-file", str(empty), "--input-file", str(empty)]
        if args.dry_run:
            common.append("--dryrun")

        def run(name, workflow, event, payload, success=True, marker=""):
            event_file = Path(temp) / "event.json"
            event_file.write_text(json.dumps(payload))
            command = common + [event, "-W", str(ROOT / "tests/act/workflows" / workflow),
                                "--eventpath", str(event_file)]
            print(f"\n=== {name} ===", flush=True)
            with subprocess.Popen(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT) as process:
                lines = []
                for line in process.stdout:
                    print(line, end="", flush=True)
                    lines.append(line)
                returncode = process.wait()
            output = "".join(lines)
            if args.dry_run:
                passed = returncode == 0
            else:
                passed = (returncode == 0) == success
                if marker:
                    passed = passed and marker in output
            print(f"{'PASS' if passed else 'FAIL'}: {name}", flush=True)
            if not passed:
                failed.append(name)

        if args.suite != "branch":
            run("run-first matrix", "run-first.yml", "push", {})
        if args.suite != "run-first":
            for name, branch, pattern, success in CASES:
                payload = {"test_pattern": pattern}
                if branch is not None:
                    payload["pull_request"] = {"head": {"ref": branch}, "base": {"ref": "main"}}
                if not success:
                    marker = f"Invalid branch name: {branch}"
                elif branch is None:
                    marker = "No branch name found"
                elif branch.startswith("dependabot/"):
                    marker = "Skipping validation for dependabot branch:"
                elif branch.startswith("release-please--"):
                    marker = "Skipping validation for release-please branch:"
                else:
                    marker = f"Branch name is valid: {branch}"
                run(f"branch/{name}", "branch.yml", "push" if branch is None else "pull_request",
                    payload, success, marker)
    print(f"\n{'FAILED: ' + ', '.join(failed) if failed else 'All selected cases passed.'}")
    return bool(failed)


if __name__ == "__main__":
    sys.exit(main())
