# Repository Guidelines

## Project Structure & Module Organization
- `skills/` contains each skill as a folder. Example: `skills/investment-asset-analysis/`.
- Each skill entry point is `SKILL.md`, which includes YAML frontmatter (`name`, `description`) plus usage guidance.
- Skill-specific scripts live alongside the `SKILL.md` (for this repo) as Python files, e.g. `calculate_ratios.py`, `interpret_ratios.py`.
- Top-level docs and metadata live in `README.md` and `LICENSE`.

## Build, Test, and Development Commands
This repository is documentation- and script-first; there is no build system configured.
- `python3 skills/investment-asset-analysis/calculate_ratios.py` runs ratio calculations.
- `python3 skills/investment-asset-analysis/interpret_ratios.py` interprets results.
- No package manager or virtual environment is defined; use your standard Python environment.

## Coding Style & Naming Conventions
- Python: 4-space indentation, snake_case for files and functions (e.g. `calculate_ratios.py`).
- Markdown: keep headings short, use bullet lists for steps, and include code fences for examples.
- Skill folders should be lower-case, dash-separated, and match the `name` field in `SKILL.md` (e.g. `investment-asset-analysis`).
- Keep `SKILL.md` focused on capability, input/output formats, and example usage.

## Testing Guidelines
- No automated tests are currently configured.
- If you add tests, place them under `skills/<skill-name>/tests/` and name files `test_*.py`.
- Prefer lightweight, deterministic tests that run with `python3 -m pytest` if you introduce pytest.

## Commit & Pull Request Guidelines
- Git history is minimal and does not establish conventions. Use clear, imperative commit messages (e.g. "Add cash flow ratio support").
- PRs should include a short summary of the skill change, links to any relevant specs or issues, and example input/output snippets when behavior changes.

## Agent-Specific Instructions
- Follow the Agent Skills open format: each skill must include a `SKILL.md` with YAML frontmatter.
- Use progressive disclosure: keep `SKILL.md` readable, and put heavy references or templates in supporting files if they are added later.
