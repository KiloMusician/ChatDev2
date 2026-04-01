# Anti-Softlock Protocol for Claude Code Sessions

## The Problem
Getting stuck waiting for task outputs or checking status when I should be making concrete progress.

## The Solution: Always Be Doing

### Rule 1: Never Wait Without Action
- ❌ BAD: Check output → Wait → Check again
- ✅ GOOD: Check output → Take action immediately → Move to next task

### Rule 2: Parallel > Sequential
- ❌ BAD: Fix one file → Commit → Fix next file → Commit
- ✅ GOOD: Fix all related files → Single comprehensive commit

### Rule 3: Concrete Actions First
- ❌ BAD: Create summary.md about what I'll do
- ✅ GOOD: Do the actual work → Optionally document after

### Rule 4: Time Budget Per Action
If I'm spending more than 30 seconds without making a code change or running a command, I'm stuck.

## Anti-Softlock Checklist

Before each response, ask:
1. ✅ Am I making a concrete code change or running a useful command?
2. ✅ If checking status, do I have an immediate next action planned?
3. ✅ If waiting for output, can I do something else in parallel?
4. ✅ If documenting, is the actual work already done?

## Emergency Recovery

If stuck for >1 minute:
1. Stop whatever I'm doing
2. Pick the simplest concrete action from the todo list
3. Execute it immediately
4. Update todo list
5. Move to next item

## Examples

### ❌ Softlock Pattern (What I Was Doing)
```
1. Run test
2. Check output
3. Analyze results
4. Think about what to do next
5. Check another output
6. Wait...
7. User notices I'm stuck
```

### ✅ Keep Moving Pattern (What I Should Do)
```
1. Run test
2. See 18 errors
3. Immediately: Read first error file
4. Fix error
5. Move to next error
6. Fix error
7. Commit batch
8. Run test again
9. Report results
```

## Commitment

I will bias toward **doing** over **analyzing** and **action** over **waiting**.

Every 60 seconds of session time should include at least one:
- File edit
- Command execution
- Commit
- Concrete result delivered to user

---
Created: 2025-12-22
Purpose: Prevent future softlock incidents
