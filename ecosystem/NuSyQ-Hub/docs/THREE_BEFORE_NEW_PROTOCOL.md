# Three Before New Protocol

**Purpose:** Stop duplicate tooling in a brownfield ecosystem by forcing
reuse/extension before new creation.

## Rule (must follow before adding any script/tool/module)

1. **Discover**: Find **three** existing implementations that could be extended,
   combined, or modernized for the capability you need.
2. **Assess**: For each candidate, note why it works or why it falls short.
3. **Justify**: If none fit, document the rationale and planned scope.
4. **Record**: Log the decision in the quest system (e.g., `quest_log.jsonl`)
   with links to the three candidates.
5. **Proceed**: Only then create new code.

## Exemptions (still document briefly)

- Critical security fixes with no safe workaround.
- Truly novel capabilities (state why they are novel and why existing tools
  cannot be adapted).

## How to comply (fast path)

- Run the discovery helper:
  `python scripts/find_existing_tool.py --capability "<capability>"`
- Review the suggested candidates and pick an extension/combination path.
- If you must go net-new, include the three references and justification in your
  quest/update.

## Approval signal

- Quests/PRs that add new tools must include a "Three Before New" note: three
  candidates + justification. Missing notes = reject.

## Pre-commit hook (optional but recommended)

- Link `.git/hooks/pre-commit` to `python scripts/three_before_new_audit.py`.
- Blocking by default; set `TBN_WARN_ONLY=1` or pass `--warn-only` to emit
  warnings instead of failing.
- Heuristic scope: new files in `scripts/`, `src/tools/`, `src/utils/`,
  `src/diagnostics/`, `src/healing/` with common script/config extensions.

## Hygiene checklist (copy/paste)

- [ ] Ran tool discovery for the capability
- [ ] Listed three candidates with paths
- [ ] Stated why each is insufficient (or how to extend)
- [ ] Logged decision in quest system
- [ ] Proceeded only after the above
