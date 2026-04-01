Code style and E501 policy

This project uses Black, Ruff, and MyPy for formatting, linting, and typing.

Line length and E501 policy

- Canonical line length: 100 characters.
- E501 (line-too-long) is treated conservatively: manual, behavior-preserving
  edits are preferred for high-impact files rather than bulk auto-fixes.
- Temporary per-file `# noqa: E501` is allowed when necessary, but please
  document the rationale in a comment.

Local checks

- Use the included helper to capture Ruff E501 output reliably on Windows:

```bash
python scripts/capture_ruff_e501.py
python scripts/parse_ruff_e501.py
```

This produces `ruff_e501.txt` (UTF-8) and `ruff_e501_summary.json` (ranked
offender list).

Pre-commit hooks and CI

- Pre-commit is configured in `.pre-commit-config.yaml`; ruff is intentionally
  configured without `--fix` to avoid automatic edits at commit time.
- There is also a legacy `.githooks/pre-commit-impl.py` script used by some
  developer workflows; that script ignores E501 to enable staged manual fixes.
- CI workflows run ruff checks (machine-readable) and no longer run `--fix` in
  PR validation; an artifact with E501 summary is uploaded for triage.

Recommended workflow

1. Run `python scripts/capture_ruff_e501.py` to capture E501s in UTF-8.
2. Run `python scripts/parse_ruff_e501.py` to generate `ruff_e501_summary.json`.
3. Triage top offenders and apply conservative edits in small batches.
4. Re-run the capture+parse cycle and push a new PR with focused edits.

Contact

- If unsure about a line-length change, ask on the PR or open a "style" quest in
  the repository's quest system.
