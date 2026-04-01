$ollamaPath = "$env:USERPROFILE\.ollama\models"
$lmstudioPath = "$env:USERPROFILE\.lmstudio\models"
Write-Host "Ollama models path: $ollamaPath"
Write-Host "LM Studio models path: $lmstudioPath"
if (Test-Path $ollamaPath) { Write-Host "Ollama models dir exists" } else { Write-Host "Ollama models dir not found" }
if (Test-Path $lmstudioPath) { Write-Host "LM Studio models dir exists" } else { Write-Host "LM Studio models dir not found" }
