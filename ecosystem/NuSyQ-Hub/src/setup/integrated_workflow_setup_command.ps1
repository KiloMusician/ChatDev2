Write-Host "🚀 KILO-FOOLISH Advanced Systems Setup" -ForegroundColor Cyan

# Create all new directories
$newDirectories = @(
    "src\libraries",
    "src\dictionaries\groups",
    "src\rosetta_stone",
    "src\tagging_systems",
    "src\analysis",
    "src\interfaces",
    "data\jobs",
    "data\libraries",
    "data\dictionaries",
    "data\cache",
    "tests\unit",
    "tests\integration",
    "tests\fixtures",
    "docs\api",
    "docs\guides",
    "docs\architecture"
)

foreach ($dir in $newDirectories) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    }
    else {
        Write-Host "⏭️  Skipped (already exists): $dir" -ForegroundColor Yellow
    }
}


# Create configuration file only if it does not exist
$configPath = "config\integration_settings.json"
if (-not (Test-Path $configPath)) {
    @"
{
    "job_tracker": {
        "enabled": true,
        "auto_tag": true,
        "rosetta_integration": true,
        "data_path": "data/jobs"
    },
    "rosetta_stone": {
        "auto_translate": true,
        "confidence_threshold": 0.6,
        "unknown_word_tracking": true
    },
    "tagging_systems": {
        "omni_tag": {"enabled": true, "weight": 1.0},
        "mega_tag": {"enabled": true, "weight": 1.2},
        "nusyq_tag": {"enabled": true, "weight": 1.5},
        "rsev_tag": {"enabled": true, "weight": 1.0}
    },
    "music_analysis": {
        "enabled": true,
        "harmonic_analysis": true,
        "pattern_matching": true
    }
}
"@ | Out-File $configPath -Encoding UTF8
    Write-Host "✅ Created config: $configPath" -ForegroundColor Green
}
else {
    Write-Host "⏭️  Skipped (already exists): $configPath" -ForegroundColor Yellow
}

Write-Host "🎯 Advanced systems configured!" -ForegroundColor Green
Write-Host "📊 Ready for Job Tracking, Rosetta Stone, and Advanced Tagging!" -ForegroundColor Yellow
