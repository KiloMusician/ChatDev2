@echo off
echo 🔬 EMPIRICAL LLM SUBSYSTEM TESTING
echo =================================================
echo Question: Are our LLM subsystems functional (gas) or just theater (snake oil)?
echo.

echo 1️⃣ Testing Ollama...
ollama --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Ollama is installed
    echo 📋 Available models:
    ollama list
) else (
    echo ❌ Ollama not found or not running
)

echo.
echo 2️⃣ Testing Python...
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python is available
) else (
    echo ❌ Python not found
)

echo.
echo 3️⃣ Testing ChatDev directory...
if exist "c:\Users\malik\Desktop\ChatDev_CORE\ChatDev-main" (
    echo ✅ ChatDev directory exists
    if exist "c:\Users\malik\Desktop\ChatDev_CORE\ChatDev-main\run.py" (
        echo ✅ ChatDev run.py exists
    ) else (
        echo ❌ ChatDev run.py missing
    )
) else (
    echo ❌ ChatDev directory not found
)

echo.
echo 4️⃣ Testing our integration files...
if exist "src\integration\chatdev_llm_adapter.py" (
    echo ✅ ChatDev LLM adapter exists
) else (
    echo ❌ ChatDev LLM adapter missing
)

if exist "src\ai\ollama_chatdev_integrator.py" (
    echo ✅ Ollama-ChatDev integrator exists
) else (
    echo ❌ Ollama-ChatDev integrator missing
)

echo.
echo 🧐 VERDICT: Check output above to determine GAS vs SNAKE OIL ratio
pause
