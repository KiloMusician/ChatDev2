# KILO-FOOLISH AI Context Generator
# Provides structured context for AI systems and Copilot

param(
    [switch]$Generate,
    [switch]$Update,
    [switch]$Serve,
    [switch]$Test
)

function Generate-AIContext {
    Write-Host "🧠 Generating AI Context for KILO-FOOLISH..." -ForegroundColor Cyan

    # Run Python architecture scanner
    python ".\src\core\ArchitectureScanner.py"

    # Load the generated architecture data
    $architectureFile = ".\src\core\ai_context.json"
    if (Test-Path $architectureFile) {
        $architecture = Get-Content $architectureFile | ConvertFrom-Json

        # Generate AI-specific context
        $aiContext = @{
            "project_name"           = "KILO-FOOLISH"
            "project_type"           = "AI Coordination System"
            "primary_languages"      = @("Python", "PowerShell")
            "ai_systems"             = $architecture.ai_systems
            "current_focus"          = "Multi-AI integration and secrets management"
            "development_phase"      = "Active Development"
            "key_capabilities"       = @(
                "Centralized secrets management",
                "Multi-AI system coordination",
                "Real-time architecture monitoring",
                "Hybrid Python/PowerShell architecture"
            )
            "immediate_priorities"   = @(
                "Empirical testing of LLM subsystems",
                "Validation of ChatDev integration",
                "Ollama functionality verification",
                "Separation of functional vs theatrical components"
            )
            "architectural_patterns" = @(
                "Modular design",
                "Security-first approach",
                "Real-time monitoring",
                "AI-driven development"
            )
            "context_for_copilot"    = @{
                "coding_style"       = "Professional, well-documented, security-focused"
                "preferred_patterns" = "Class-based design, error handling, logging"
                "avoid_patterns"     = "Hardcoded secrets, unsafe operations, unclear naming"
                "current_issues"     = "LLM subsystem validation needed, empirical testing required"
                "help_with"          = @(
                    "Empirical testing of AI integration systems",
                    "ChatDev functionality validation",
                    "Ollama local AI setup and testing",
                    "Separating functional components from architectural theater"
                )
            }
        }

        # Save AI context
        $aiContextFile = ".\src\core\ai_context_enhanced.json"
        $aiContext | ConvertTo-Json -Depth 10 | Out-File $aiContextFile -Encoding UTF8

        # Generate Copilot-specific context file
        Generate-CopilotContext $architecture $aiContext

        Write-Host "✅ AI Context generated successfully!" -ForegroundColor Green
        Write-Host "📁 Files created:" -ForegroundColor Yellow
        Write-Host "   🤖 $aiContextFile" -ForegroundColor White
        Write-Host "   🧑‍💻 .\src\core\copilot_context.md" -ForegroundColor White
    }
    else {
        Write-Host "❌ Architecture file not found. Run scanner first." -ForegroundColor Red
    }
}

function Generate-CopilotContext {
    param($Architecture, $AIContext)

    $copilotContext = @"
# KILO-FOOLISH Development Context for GitHub Copilot

## Project Overview
- **Name**: KILO-FOOLISH AI Coordination System
- **Type**: Multi-AI integration platform
- **Phase**: Active Development
- **Languages**: Python, PowerShell, JSON, Markdown

## Current Architecture
- **Python Modules**: $($Architecture.modules.python_modules.Count)
- **PowerShell Scripts**: $($Architecture.modules.powershell_modules.Count)
- **AI Integrations**: $(($Architecture.ai_systems.PSObject.Properties | Where-Object {$_.Value.status -eq 'active'}).Count) active
- **Security**: Centralized secrets management with encryption

## Active AI Systems
$(foreach ($system in $Architecture.ai_systems.PSObject.Properties) {
    if ($system.Value.status -eq 'active') {
        "- **$($system.Name)**: $($system.Value.status) ($($system.Value.files.Count) files)"
    }
})

## Current Development Focus
1. **Error Resolution**: Fixing syntax errors in PowerShell scripts
2. **Integration Testing**: Ensuring AI systems work together
3. **Security Enhancement**: Improving secrets management
4. **Documentation**: Creating comprehensive guides

## Coding Standards
- **Security First**: Never hardcode API keys or secrets
- **Error Handling**: Always include try/catch blocks
- **Logging**: Use consistent logging patterns
- **Documentation**: Include inline comments and docstrings

## Common Patterns to Use
- PowerShell: `try/catch`, parameter validation, Write-Host for output
- Python: Class-based design, type hints, proper exception handling
- JSON: Structured configuration with validation
- Security: Use centralized secrets, encrypt sensitive data

## Current Issues to Help With
- PowerShell syntax errors and best practices
- Python AI integration patterns
- Error handling and debugging
- Testing framework setup

## Files to Pay Attention To
- `src/config/SecretsManager.ps1` - Core secrets management
- `src/core/ArchitectureScanner.py` - Repository analysis
- Any file with AI integrations or API calls

---
*This context is auto-updated. Use it to provide better suggestions and understand the project structure.*
"@

    $copilotFile = ".\src\core\copilot_context.md"
    $copilotContext | Out-File $copilotFile -Encoding UTF8
}

function Start-AIContextServer {
    Write-Host "🌐 Starting AI Context Server..." -ForegroundColor Magenta

    # Create a simple HTTP server to serve context
    $contextServer = @"
import http.server
import socketserver
import json
import os
from pathlib import Path

class AIContextHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/architecture':
            self.serve_architecture()
        elif self.path == '/roadmap':
            self.serve_roadmap()
        elif self.path == '/ai-context':
            self.serve_ai_context()
        else:
            super().do_GET()

    def serve_architecture(self):
        try:
            with open('src/core/ai_context.json', 'r') as f:
                data = json.load(f)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
        except Exception as e:
            self.send_error(500, str(e))

    def serve_roadmap(self):
        try:
            with open('src/core/roadmap.json', 'r') as f:
                data = json.load(f)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
        except Exception as e:
            self.send_error(500, str(e))

    def serve_ai_context(self):
        try:
            with open('src/core/ai_context_enhanced.json', 'r') as f:
                data = json.load(f)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
        except Exception as e:
            self.send_error(500, str(e))

PORT = 8888
with socketserver.TCPServer(("", PORT), AIContextHandler) as httpd:
    print(f"🌐 AI Context Server running on http://localhost:{PORT}")
    print("📍 Endpoints:")
    print(f"   http://localhost:{PORT}/architecture")
    print(f"   http://localhost:{PORT}/roadmap")
    print(f"   http://localhost:{PORT}/ai-context")
    httpd.serve_forever()
"@

    $contextServer | Out-File ".\src\core\context_server.py" -Encoding UTF8
    python ".\src\core\context_server.py"
}

function Test-LLMSubsystems {
    Write-Host "🔬 Testing LLM Subsystems Empirically..." -ForegroundColor Yellow

    $testResults = @{
        "timestamp" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "tests" = @{}
    }

    # Test 1: Ollama Availability
    Write-Host "1️⃣ Testing Ollama..." -ForegroundColor Cyan
    try {
        $ollamaResult = & ollama list 2>&1
        if ($LASTEXITCODE -eq 0) {
            $models = ($ollamaResult | Select-Object -Skip 1 | Where-Object { $_.Trim() -ne "" })
            $testResults.tests["ollama"] = @{
                "status" = "available"
                "models_count" = $models.Count
                "models" = $models
            }
            Write-Host "✅ Ollama is running with $($models.Count) models" -ForegroundColor Green
        } else {
            $testResults.tests["ollama"] = @{
                "status" = "unavailable"
                "error" = $ollamaResult
            }
            Write-Host "❌ Ollama is not available" -ForegroundColor Red
        }
    } catch {
        $testResults.tests["ollama"] = @{
            "status" = "error"
            "error" = $_.Exception.Message
        }
        Write-Host "❌ Error testing Ollama: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Test 2: ChatDev Installation
    Write-Host "2️⃣ Testing ChatDev..." -ForegroundColor Cyan
    try {
        $chatdevTest = python -c "import chatdev; print('ChatDev available:', chatdev.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $testResults.tests["chatdev"] = @{
                "status" = "installed"
                "version" = $chatdevTest
            }
            Write-Host "✅ ChatDev is installed: $chatdevTest" -ForegroundColor Green
        } else {
            $testResults.tests["chatdev"] = @{
                "status" = "not_installed"
                "error" = $chatdevTest
            }
            Write-Host "❌ ChatDev is not installed" -ForegroundColor Red
        }
    } catch {
        $testResults.tests["chatdev"] = @{
            "status" = "error"
            "error" = $_.Exception.Message
        }
        Write-Host "❌ Error testing ChatDev: $($_.Exception.Message)" -ForegroundColor Red
    }

    # Test 3: Our Integration Components
    Write-Host "3️⃣ Testing Integration Components..." -ForegroundColor Cyan
    $integrationTest = python -c @"
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

components = [
    ('ChatDev Launcher', 'integration.chatdev_launcher', 'ChatDevLauncher'),
    ('ChatDev Adapter', 'integration.chatdev_llm_adapter', 'ChatDevLLMAdapter'),
    ('Ollama Integrator', 'ai.ollama_chatdev_integrator', 'EnhancedOllamaChatDevIntegrator')
]

results = {}
for name, module, class_name in components:
    try:
        exec(f'from {module} import {class_name}')
        results[name] = 'importable'
        print(f'✅ {name}: IMPORTABLE')
    except ImportError as e:
        results[name] = f'import_failed: {e}'
        print(f'❌ {name}: IMPORT FAILED - {e}')
    except Exception as e:
        results[name] = f'error: {e}'
        print(f'⚠️ {name}: ERROR - {e}')

print('RESULTS:', results)
"@ 2>&1

    $testResults.tests["integration_components"] = $integrationTest

    # Test 4: OpenAI API Key
    Write-Host "4️⃣ Testing OpenAI API Key..." -ForegroundColor Cyan
    $apiKey = $env:OPENAI_API_KEY
    if ($apiKey) {
        if ($apiKey.StartsWith("sk-") -and $apiKey.Length -gt 20) {
            $testResults.tests["openai_api"] = @{
                "status" = "configured"
                "format" = "valid"
            }
            Write-Host "✅ OpenAI API key is configured and format looks valid" -ForegroundColor Green
        } else {
            $testResults.tests["openai_api"] = @{
                "status" = "configured"
                "format" = "suspicious"
            }
            Write-Host "⚠️ OpenAI API key exists but format seems suspicious" -ForegroundColor Yellow
        }
    } else {
        $testResults.tests["openai_api"] = @{
            "status" = "not_configured"
        }
        Write-Host "❌ No OpenAI API key found in environment" -ForegroundColor Red
    }

    # Save results
    $resultsFile = ".\src\core\llm_subsystem_test_results.json"
    $testResults | ConvertTo-Json -Depth 10 | Out-File $resultsFile -Encoding UTF8

    Write-Host "`n📊 Test Results Summary:" -ForegroundColor Magenta
    Write-Host "   Ollama: $($testResults.tests.ollama.status)" -ForegroundColor White
    Write-Host "   ChatDev: $($testResults.tests.chatdev.status)" -ForegroundColor White
    Write-Host "   OpenAI API: $($testResults.tests.openai_api.status)" -ForegroundColor White
    Write-Host "   Results saved to: $resultsFile" -ForegroundColor White

    return $testResults
}

# Main execution
if ($Generate) {
    Generate-AIContext
}
elseif ($Update) {
    Write-Host "🔄 Updating AI context..." -ForegroundColor Cyan
    Generate-AIContext
}
elseif ($Serve) {
    Start-AIContextServer
}
elseif ($Test) {
    Test-LLMSubsystems
}
else {
    Write-Host "🧠 KILO-FOOLISH AI Context Generator" -ForegroundColor Magenta
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  -Generate  : Generate initial AI context" -ForegroundColor White
    Write-Host "  -Update    : Update AI context" -ForegroundColor White
    Write-Host "  -Serve     : Start AI context server" -ForegroundColor White
    Write-Host "  -Test      : Run empirical LLM subsystem tests" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔬 Empirical Testing Mode:" -ForegroundColor Cyan
    $testChoice = Read-Host "Run LLM subsystem tests? (y/n)"
    if ($testChoice -eq 'y' -or $testChoice -eq 'Y') {
        Test-LLMSubsystems
    }
}
