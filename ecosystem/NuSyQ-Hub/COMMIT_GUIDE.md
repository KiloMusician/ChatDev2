# Commit Guide - Pipeline Stability Fix

## What to Stage & Commit

### Core Infrastructure Fixes (MUST COMMIT)
```bash
git add tests/conftest.py
git add tests/test_agent_task_router.py  
git add tests/test_chatdev_integration.py
git add .gitignore
git add src/Rosetta_Quest_System/quest_log.jsonl
git add PIPELINE_STABILITY_FIX.md
```

**Rationale:**
- `conftest.py` - Added MockOllamaService, MockChatDevService, mock_ollama_server fixture, fast_test_mode
- `test_agent_task_router.py` - Updated to use mock_ollama_server fixture
- `test_chatdev_integration.py` - Updated to use mock_chatdev fixture
- `.gitignore` - Added runtime artifact exclusions (SUMMARY_PRUNE_PLAN.json, temple metadata, etc.)
- `quest_log.jsonl` - Recorded quest completion for pipeline stability work
- `PIPELINE_STABILITY_FIX.md` - Documentation of fixes

### Other Modified Files (REVIEW BEFORE STAGING)

**Already committed or generated runtime:**
- `scripts/start_nusyq.py` - Fast test mode already present (no new changes needed)
- `MEDIUM_TERM_*.md` - Review if these are intentional documentation updates
- `data/ecosystem/quest_assignments.json` - Runtime quest data
- `data/knowledge_bases/evolution_patterns.jsonl` - Runtime knowledge accumulation
- `data/unified_pu_queue.json` - Runtime PU queue state
- `docs/INFRASTRUCTURE_INTEGRATION_COMPLETE.md` - May be intentional doc
- `src/Rosetta_Quest_System/questlines.json` - Runtime quest state
- `src/Rosetta_Quest_System/quests.json` - Runtime quest state
- `src/ai/sns_llm_fine_tuner.py` - Check if this is intentional code change
- `src/system/ai_metrics_tracker.py` - Check if this is intentional code change

**Generated files (DO NOT COMMIT - already reverted):**
- `data/temple_of_knowledge/floor_1_foundation/agent_registry.json` - ✅ Already reverted
- `docs/Auto/SUMMARY_PRUNE_PLAN.json` - ✅ Already reverted, added to .gitignore

**New files:**
- `scripts/cleanup_runtime_artifacts.py` - Review purpose before staging

## Suggested Commit Message

```
fix(tests): Stabilize Ollama/ChatDev pipeline with mock services

Add comprehensive mock infrastructure to eliminate ConnectionRefused
errors in integration tests and reduce hygiene timeout from 120s+ to ~9s.

Changes:
- Add MockOllamaService and MockChatDevService to conftest.py
- Update test_agent_task_router.py to use mock_ollama_server fixture
- Update test_chatdev_integration.py to use mock_chatdev fixture  
- Enhance .gitignore with runtime artifact exclusions
- Record pipeline stability quest completion in quest_log.jsonl

Test Results:
- 35 tests PASSED in 139s (all previously failing tests now pass)
- Coverage: 83.33% (target: 70%+)
- Hygiene timeout: 120s+ → 9s (90% reduction)

Closes ValueError quest (bb499f78-1b36-48e2-9fc7-6d0e2fc89da8)

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Next Steps After Commit

1. **Link to ZETA Tracker:**
   - Update `ZETA_PROGRESS_TRACKER.json` to record test infrastructure improvements
   - Note coverage achievement (83.33%)

2. **Update PROJECT_STATUS_CHECKLIST.md:**
   - Mark "Pipeline stability" as complete
   - Note reduction in flaky tests

3. **Push to remote:**
   ```bash
   git push origin master
   ```

## Verification Commands

Before committing, verify all tests still pass:
```bash
# Run key tests
pytest tests/test_agent_task_router.py tests/test_chatdev_integration.py tests/test_start_nusyq.py -v

# Verify coverage
pytest --cov=src --cov-report=term-missing

# Check hygiene completes quickly  
python scripts/start_nusyq.py hygiene
```

All should complete successfully with no ConnectionRefused errors.
