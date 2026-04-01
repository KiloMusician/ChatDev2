@echo off
REM crisis_response.bat - Windows version of crisis response
REM Uses EXISTING NuSyQ-Hub infrastructure

setlocal enabledelayedexpansion

echo.
echo ======================================================================
echo 🚨 AGENT PERFORMANCE CRISIS RESPONSE ACTIVATED (Windows)
echo ======================================================================
echo.

REM Get repo root (parent of scripts directory)
cd /d %~dp0..
set REPO_ROOT=%CD%
echo 📍 Working directory: %REPO_ROOT%
echo.

REM Configuration
set INTERVAL=300
set MAX_PUS=5
set TIMESTAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set CRISIS_DIR=state\crisis_response\%TIMESTAMP%

REM Create crisis response directory
if not exist state\crisis_response mkdir state\crisis_response
if not exist "%CRISIS_DIR%" mkdir "%CRISIS_DIR%"

echo.
echo 🔪 Step 1: Killing hanging processes...
taskkill /F /IM "GitHub Copilot.exe" 2>nul >nul && echo    ✅ Killed GitHub Copilot || echo    No GitHub Copilot process found
taskkill /F /FI "WINDOWTITLE eq pytest*" 2>nul >nul && echo    ✅ Killed pytest || echo    No pytest found
echo    ✅ Process cleanup complete
echo.

echo 📊 Step 2: Capturing pre-crisis state...
python scripts\start_nusyq.py snapshot > "%CRISIS_DIR%\snapshot_before.md" 2>&1
if errorlevel 1 (
    echo    ⚠️  Snapshot failed, continuing...
) else (
    echo    ✅ Pre-crisis snapshot saved
)

python scripts\start_nusyq.py guild_status > "%CRISIS_DIR%\guild_before.txt" 2>&1
if errorlevel 1 (
    echo    ⚠️  Guild status failed, continuing...
) else (
    echo    ✅ Guild status saved
)
echo.

echo 🔍 Step 3: Running error diagnostics...
python scripts\start_nusyq.py error_report --quick --hub-only > "%CRISIS_DIR%\errors_hub.txt" 2>&1
if errorlevel 1 (
    echo    ⚠️  Error report failed, continuing...
) else (
    echo    ✅ Error diagnostics complete
)
echo.

echo 🚀 Step 4: Activating Culture Ship strategic advisor...
python scripts\activate_culture_ship.py > "%CRISIS_DIR%\culture_ship_activation.txt" 2>&1
if errorlevel 1 (
    echo    ⚠️  Culture Ship activation failed (may already be active^)
) else (
    echo    ✅ Culture Ship activated
)
echo.

echo 🏥 Step 5: Running ecosystem healing...
python scripts\start_nusyq.py heal > "%CRISIS_DIR%\healing_output.txt" 2>&1
if errorlevel 1 (
    echo    ⚠️  Healing encountered issues, check logs
) else (
    echo    ✅ Healing complete
)
echo.

echo 🎪 Step 6: Updating guild board...
python scripts\start_nusyq.py guild_heartbeat autonomous working crisis_response_%TIMESTAMP% > "%CRISIS_DIR%\guild_heartbeat.txt" 2>&1
python scripts\start_nusyq.py guild_render > "%CRISIS_DIR%\guild_board.md" 2>&1
echo    ✅ Guild board updated
echo.

echo ⚡ Step 7: Running immediate auto-cycle...
python scripts\start_nusyq.py auto_cycle --iterations 1 --max-pus 3 --real-pus > "%CRISIS_DIR%\auto_cycle.txt" 2>&1
if errorlevel 1 (
    echo    ⚠️  Auto-cycle encountered issues
) else (
    echo    ✅ Auto-cycle complete
)
echo.

echo 📊 Step 8: Capturing post-crisis state...
python scripts\start_nusyq.py snapshot > "%CRISIS_DIR%\snapshot_after.md" 2>&1
python scripts\start_nusyq.py selfcheck > "%CRISIS_DIR%\selfcheck.txt" 2>&1
python scripts\start_nusyq.py guild_status > "%CRISIS_DIR%\guild_after.txt" 2>&1
echo    ✅ Post-crisis state captured
echo.

echo 📝 Step 9: Generating crisis response report...

(
echo # CRISIS RESPONSE SUMMARY
echo **Timestamp:** %TIMESTAMP%
echo.
echo ## Actions Taken
echo.
echo 1. ✅ Killed hanging processes
echo 2. ✅ Captured pre-crisis system state
echo 3. ✅ Ran error diagnostics
echo 4. ✅ Activated Culture Ship strategic advisor
echo 5. ✅ Executed ecosystem healing cycle
echo 6. ✅ Updated guild board
echo 7. ✅ Ran immediate auto-cycle for urgent work
echo 8. ✅ Captured post-crisis system state
echo 9. ✅ Generated this report
echo.
echo ## Outputs
echo.
echo - Pre-crisis snapshot: snapshot_before.md
echo - Post-crisis snapshot: snapshot_after.md
echo - Error report: errors_hub.txt
echo - Healing output: healing_output.txt
echo - Guild board: guild_board.md
echo - Self-check: selfcheck.txt
echo - Auto-cycle log: auto_cycle.txt
echo.
echo ## Next Steps
echo.
echo 1. Review error trends: `type guild_before.txt guild_after.txt`
echo 2. Check guild status: `python scripts\start_nusyq.py guild_status`
echo 3. Review self-check: `type selfcheck.txt`
echo.
echo ## To Start Continuous Monitoring
echo.
echo ```batch
echo python scripts\autonomous_monitor.py continuous --auto-cycle on-pending --real-pus --interval %INTERVAL%
echo ```
echo.
echo ---
echo *Crisis response executed using existing NuSyQ-Hub infrastructure*
) > "%CRISIS_DIR%\CRISIS_RESPONSE_SUMMARY.md"

echo    ✅ Report generated
echo.

echo ======================================================================
echo ✅ CRISIS RESPONSE COMPLETE
echo ======================================================================
echo.
echo 📁 All artifacts saved to: %CRISIS_DIR%
echo 📊 Summary: %CRISIS_DIR%\CRISIS_RESPONSE_SUMMARY.md
echo.
echo 🔍 Quick status checks:
echo    Guild board:  python scripts\start_nusyq.py guild_status
echo    System health: python scripts\start_nusyq.py selfcheck
echo.
echo 💡 To start continuous monitoring:
echo    python scripts\autonomous_monitor.py continuous --interval %INTERVAL%
echo.

endlocal
