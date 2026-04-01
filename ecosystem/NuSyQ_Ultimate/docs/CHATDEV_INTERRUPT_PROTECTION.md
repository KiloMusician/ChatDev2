# ChatDev Interrupt Protection System

## Problem Solved
ChatDev multi-agent tasks can take 15-60+ minutes to complete. Previously, ANY interruption (accidental keypress, VS Code action, system event) would kill the process and lose ALL progress.

## Protection Features Implemented

### 1. Double-Confirmation Interrupt Protection
When you accidentally press `Ctrl+C`:
- **First interrupt**: Shows warning and 5-second grace period
- **Second interrupt** (within 5s): Actually stops the process
- **No second interrupt**: Resumes waiting for ChatDev completion

This prevents accidental interruptions while still allowing intentional stops.

### 2. Background Mode (`--background`)
For truly long-running tasks, run in detached background mode:

```powershell
# Run in background - process continues even if terminal closes
python nusyq_chatdev.py --task "Your complex task" --background

# Monitor progress in real-time
Get-Content -Wait chatdev_background_*.log
```

**Benefits:**
- Process runs independently of terminal
- Survives terminal closure
- Safe from accidental interrupts
- Logs all output to timestamped file
- Can close VS Code entirely while ChatDev works

### 3. Clear Warning Messages
Users now see:
```
[*] ChatDev running... (output streaming above)
[*] This may take several minutes for complex tasks
[⚠️] IMPORTANT: Do NOT interrupt! ChatDev agents are coordinating...
[⚠️] Interruption will lose all progress. Let the agents finish!
```

## Usage Examples

### Normal Mode (With Protection)
```powershell
cd C:\Users\keath\NuSyQ

python nusyq_chatdev.py --task "Fix all bare except clauses" \
  --symbolic --consensus --models "qwen2.5-coder:7b,starcoder2:7b"

# If you accidentally press Ctrl+C:
# [!!!!] INTERRUPT DETECTED - DO YOU REALLY WANT TO STOP?
# [!!!!] ChatDev agents are still working. This will lose ALL progress!
# [!!!!] Press Ctrl+C again within 5 seconds to force stop, or wait to continue...

# Just wait 5 seconds and it resumes!
```

### Background Mode (Maximum Protection)
```powershell
cd C:\Users\keath\NuSyQ

# Start in background
python nusyq_chatdev.py --task "Implement complex feature" --background

# Output:
# [⚙️] BACKGROUND MODE ENABLED
# [⚙️] Process will run detached from this terminal
# [⚙️] Output logging to: C:\Users\keath\NuSyQ\chatdev_background_20251015_143022.log
# [OK] Background process started with PID: 12345

# Monitor progress (keep this terminal open or open new one)
Get-Content -Wait chatdev_background_20251015_143022.log

# Or just check it periodically
cat chatdev_background_20251015_143022.log

# Close VS Code, grab coffee, come back later!
```

### For Consensus Runs (Multiple Models)
```powershell
# These can take 30-60 minutes! Use background mode
python nusyq_chatdev.py \
  --task "Complex refactoring task" \
  --consensus \
  --models "qwen2.5-coder:7b,starcoder2:7b,codellama:7b" \
  --symbolic \
  --track-drift \
  --background

# Go do something else - check log file when you return
```

## Technical Implementation Details

### Interrupt Handler (Lines 493-537 in nusyq_chatdev.py)
```python
try:
    exit_code = process.wait()
except KeyboardInterrupt:
    # Show warning
    print("[!!!!] INTERRUPT DETECTED - DO YOU REALLY WANT TO STOP?")

    # Setup double-confirmation handler
    stop_confirmed = [False]
    def confirm_handler(signum, frame):
        stop_confirmed[0] = True
        raise KeyboardInterrupt("User confirmed stop")

    old_handler = signal.signal(signal.SIGINT, confirm_handler)

    # 5-second grace period
    time.sleep(5)
    # If no second Ctrl+C, resume waiting
    exit_code = process.wait()
```

### Background Mode (Lines 478-524 in nusyq_chatdev.py)
```python
if background:
    log_file = Path(f"chatdev_background_{timestamp}.log")

    if sys.platform == 'win32':
        # Windows: use DETACHED_PROCESS flag
        process = subprocess.Popen(
            cmd, ...,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # Linux/Mac: use start_new_session
        process = subprocess.Popen(
            cmd, ...,
            start_new_session=True
        )

    return True  # Don't wait for completion
```

## Best Practices

1. **For quick tasks (<5 min)**: Use normal mode
2. **For medium tasks (5-15 min)**: Use normal mode, be careful not to interrupt
3. **For long tasks (>15 min)**: Use `--background` mode
4. **For multi-model consensus**: ALWAYS use `--background` mode

## Monitoring Background Tasks

### PowerShell
```powershell
# Monitor live output
Get-Content -Wait chatdev_background_*.log

# Check if process is still running
Get-Process -Id 12345  # Use PID from startup message

# Kill if needed (rare)
Stop-Process -Id 12345
```

### Linux/Mac
```bash
# Monitor live output
tail -f chatdev_background_*.log

# Check if running
ps aux | grep chatdev

# Kill if needed
kill 12345
```

## Recovery from Interruptions

If you DID interrupt a task:
1. Check `C:\Users\keath\NuSyQ\ChatDev\WareHouse\` for partial work
2. Review any generated code/files
3. Re-run with refined task description
4. Use `--background` mode this time!

## Integration with Ecosystem

This protection system integrates with:
- **ΞNuSyQ Symbolic Tracking**: Tracks full session lifecycle
- **Temporal Drift Tracking**: Monitors multi-hour consensus runs
- **Multi-Model Consensus**: Essential for 30-60 min runs
- **Quest System**: Long-running quests benefit from background mode

## Future Enhancements

Potential additions:
- [ ] Resume capability from checkpoint
- [ ] Progress estimation and ETA display
- [ ] Web UI for monitoring background tasks
- [ ] Email/notification on completion
- [ ] Auto-background mode for tasks >15 min estimated duration

---

**Implementation Date**: October 15, 2025
**Files Modified**: `nusyq_chatdev.py`
**Testing**: Pending validation with live ChatDev run
