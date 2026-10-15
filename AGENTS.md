# Repository Instructions

## Architecture Graph

- Keep this repository's Graphify outputs and cache in the root `.graphify/` directory. It is intentionally tracked; do not put it under `src/` or add it to `.gitignore`.
- Run Graphify through `python scripts/graphify_project.py ...`. The wrapper sets Graphify's output to the repository-root `.graphify/` directory and runs commands from the repository root.
- `python scripts/graphify_project.py update` refreshes the code graph for `src`. Other Graphify commands, such as `query`, `path`, and `explain`, are passed through to the CLI.
- Use the wrapper for updates so Graphify's scan-root marker stays repository-relative across machines.
