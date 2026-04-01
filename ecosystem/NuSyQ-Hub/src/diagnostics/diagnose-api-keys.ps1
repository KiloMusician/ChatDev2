# KILO-FOOLISH API Key Error Diagnostic

Write-Host "🔍 KILO-FOOLISH API Key Error Diagnostic" -ForegroundColor Red
Write-Host "=" * 50 -ForegroundColor Red

# Check if secrets manager exists and is accessible
Write-Host "`n1. 🔑 Checking Secrets Manager..." -ForegroundColor Yellow
$secretsManager = ".\src\config\SecretsManager.ps1"
if (Test-Path $secretsManager) {
    Write-Host "   ✅ SecretsManager.ps1 found" -ForegroundColor Green

    try {
        # Test if we can load it without errors
        $testLoad = powershell -Command "& '$secretsManager' -Status" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Secrets Manager loads successfully" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ Secrets Manager has syntax errors:" -ForegroundColor Red
            Write-Host "   $testLoad" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "   ❌ Error loading Secrets Manager: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "   ❌ SecretsManager.ps1 not found" -ForegroundColor Red
}

# Check VS Code settings for exposed API keys
Write-Host "`n2. 🔍 Checking VS Code Settings..." -ForegroundColor Yellow
$vscodeSettings = "$env:APPDATA\Code\User\settings.json"
if (Test-Path $vscodeSettings) {
    try {
        $content = Get-Content $vscodeSettings -Raw

        # Look for API key patterns
        $apiKeyPatterns = @(
            'sk-[a-zA-Z0-9]{48,}',
            'sk-proj-[a-zA-Z0-9_-]{48,}',
            '"apiKey":\s*"[^"]*"',
            '"gptKey":\s*"[^"]*"'
        )

        $foundKeys = @()
        foreach ($pattern in $apiKeyPatterns) {
            $matches = [regex]::Matches($content, $pattern)
            foreach ($match in $matches) {
                $foundKeys += $match.Value
            }
        }

        if ($foundKeys.Count -gt 0) {
            Write-Host "   ⚠️ Found $($foundKeys.Count) potential API keys in VS Code settings:" -ForegroundColor Yellow
            foreach ($key in $foundKeys) {
                if ($key.Length -gt 20) {
                    Write-Host "     🔑 $($key.Substring(0, 15))..." -ForegroundColor Red
                }
                else {
                    Write-Host "     🔑 $key" -ForegroundColor Red
                }
            }
            Write-Host "   🚨 SECURITY RISK: API keys exposed in VS Code settings!" -ForegroundColor Red
        }
        else {
            Write-Host "   ✅ No exposed API keys found in VS Code settings" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "   ❌ Error reading VS Code settings: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "   ⚠️ VS Code settings file not found" -ForegroundColor Yellow
}

# Check for API key errors in recent VS Code logs
Write-Host "`n3. 📋 Checking Recent Errors..." -ForegroundColor Yellow
$logDirs = @(
    "$env:APPDATA\Code\logs",
    "$env:APPDATA\Code\User\workspaceStorage"
)

foreach ($logDir in $logDirs) {
    if (Test-Path $logDir) {
        $recentLogs = Get-ChildItem $logDir -Recurse -Filter "*.log" |
        Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-2) } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 3

        foreach ($log in $recentLogs) {
            try {
                $logContent = Get-Content $log.FullName -Tail 50 -ErrorAction SilentlyContinue
                $apiErrors = $logContent | Select-String -Pattern "api.*key|401|unauthorized|authentication" -CaseSensitive:$false

                if ($apiErrors) {
                    Write-Host "   🔍 Found API-related errors in $($log.Name):" -ForegroundColor Red
                    foreach ($error in $apiErrors | Select-Object -First 3) {
                        Write-Host "     ⚠️ $($error.Line)" -ForegroundColor Yellow
                    }
                }
            }
            catch {
                # Skip logs that can't be read
            }
        }
    }
}

# Test current API keys
Write-Host "`n4. 🧪 Testing API Keys..." -ForegroundColor Yellow
if (Test-Path ".\src\config\secrets.ps1") {
    try {
        . ".\src\config\secrets.ps1"

        # Test OpenAI key
        $openaiKey = Get-KILOSecret "OpenAI" "ApiKey"
        if ($openaiKey -and $openaiKey.StartsWith("sk-")) {
            Write-Host "   🔑 OpenAI API Key: $($openaiKey.Substring(0, 7))... ✅" -ForegroundColor Green

            # Test if key is valid (quick test)
            try {
                $headers = @{
                    'Authorization' = "Bearer $openaiKey"
                    'Content-Type'  = 'application/json'
                }
                $response = Invoke-RestMethod -Uri "https://api.openai.com/v1/models" -Headers $headers -Method GET -TimeoutSec 10
                Write-Host "   ✅ OpenAI API Key is valid and working" -ForegroundColor Green
            }
            catch {
                Write-Host "   ❌ OpenAI API Key failed test: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "   ❌ OpenAI API Key not found or invalid format" -ForegroundColor Red
        }

        # Test CodeSmell key
        $codeSmellKey = Get-KILOSecret "CodeSmellGPT" "ApiKey"
        if ($codeSmellKey -and $codeSmellKey.StartsWith("sk-")) {
            Write-Host "   🔑 CodeSmell API Key: $($codeSmellKey.Substring(0, 7))... ✅" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ CodeSmell API Key not found or invalid format" -ForegroundColor Red
        }

    }
    catch {
        Write-Host "   ❌ Error testing API keys: $_" -ForegroundColor Red
    }
}
else {
    Write-Host "   ❌ secrets.ps1 file not found" -ForegroundColor Red
}

Write-Host "`n🎯 IMMEDIATE FIXES:" -ForegroundColor Magenta
Write-Host "=" * 30 -ForegroundColor Magenta
