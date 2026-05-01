---
applyTo: "src/**/*.py,tests/**/*.py"
description: "Use when editing or reviewing Python code and tests in this repository. Standardizes pytest usage, fixture patterns, and focused validation behavior for cycle-report changes."
---
Follow these repository testing conventions when making or validating Python changes:

- Use `pytest` for automated validation. Prefer the narrowest possible command first, usually a single test file or a specific test selected with `-k`.
- Keep tests in `tests/` and follow the existing `test_*.py` naming pattern.
- Reuse the repository's existing testing style: direct assertions, lightweight fake classes, and small local fixtures before adding new abstractions.
- Prefer deterministic fixture data and explicit assertions over snapshots.
- When adding coverage for a bug, write the regression test before widening to related happy-path cases.
- When a change touches CLI behavior, follow the existing pattern of calling `main([...])` or `build_parser()` directly in tests instead of shelling out unless subprocess behavior is the thing under test.
- When a change touches runner or analysis behavior, inspect nearby tests first and extend the local fake/fixture pattern instead of introducing mocks from a new framework.
- After the first substantive edit, run one focused validation action immediately. Widen to broader `pytest` runs only after the local check passes or if a broader failure is needed to explain impact.
- Do not replace narrowly failing tests with broader smoke tests. Preserve defect-localizing assertions whenever possible.
- If you uncover a product defect while acting in a QA-only role, stop at the failing test and report the defect clearly instead of silently patching production code.

Useful validation examples for this repo:

- `pytest tests/test_runner.py`
- `pytest tests/test_cli.py -k generate_scenarios`
- `pytest tests/test_analysis.py tests/test_reporting.py`