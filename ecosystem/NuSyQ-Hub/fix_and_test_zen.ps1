$data = @{
    version = "1.0.0"
    meta = @{}
    rules = @(
        @{
            id = "test_rule"
            triggers = @{}
            suggestions = @(@{ strategy = "test" })
            tags = @()
        }
    )
} | ConvertTo-Json -Depth 10

$data | Out-File -FilePath "zen_engine/codex/zen.json" -Encoding UTF8
Write-Host "✅ Created valid zen.json"

python test_zen_system.py
