"""Run Graphify with this repository's root-level .graphify directory."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOT = Path("src")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(
            "Usage: python scripts/graphify_project.py <graphify-command> [args...]\n"
            'Example: python scripts/graphify_project.py query "How does SREWebApp route decisions?"\n'
            "Example: python scripts/graphify_project.py update",
            file=sys.stderr,
        )
        return 2

    executable = shutil.which("graphify")
    if executable is None:
        print(
            "graphify was not found on PATH; install Graphify before running this command.",
            file=sys.stderr,
        )
        return 127

    # Graphify reads GRAPHIFY_OUT once at startup. Use an absolute path so an
    # update of src still writes to the repository-root .graphify.
    env = os.environ.copy()
    env["GRAPHIFY_OUT"] = str((REPO_ROOT / ".graphify").resolve())

    # The project graph covers src; passing the path explicitly keeps updates
    # portable and avoids depending on a machine-specific marker.
    if args[0] == "update" and not any(not arg.startswith("-") for arg in args[1:]):
        args.insert(1, str(DEFAULT_SCAN_ROOT))

    try:
        result = subprocess.run(
            [executable, *args], cwd=REPO_ROOT, env=env, check=False
        )
    except OSError as exc:
        print(f"Could not start graphify: {exc}", file=sys.stderr)
        return 127

    if result.returncode == 0 and args[0] == "update":
        # Graphify writes an absolute .graphify_root when GRAPHIFY_OUT is
        # absolute. Store a repository-relative scan root in the tracked graph
        # so clones on other machines can use it too.
        scan_root = next((arg for arg in args[1:] if not arg.startswith("-")), str(DEFAULT_SCAN_ROOT))
        scan_path = Path(scan_root)
        if not scan_path.is_absolute():
            scan_path = (REPO_ROOT / scan_path).resolve()
        try:
            marker_value = scan_path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            marker_value = str(scan_path)
        marker = REPO_ROOT / ".graphify" / ".graphify_root"
        if marker.exists():
            marker.write_text(marker_value, encoding="utf-8")

        report = REPO_ROOT / ".graphify" / "GRAPH_REPORT.md"
        if report.exists():
            report_text = report.read_text(encoding="utf-8")
            report_text = report_text.replace(
                "graphify update .", "python scripts/graphify_project.py update"
            )
            report_text = report_text.replace(
                "graphify query", "python scripts/graphify_project.py query"
            )
            report.write_text(report_text, encoding="utf-8")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
