# Ollama Direct Commands Reference

## 🚀 Quick Start Commands

### **Service Management**
```bash
# CHECK FIRST: Is Ollama already running?
ollama ps

# If you get the error "listen tcp 127.0.0.1:11434: bind: Only one usage..."
# This means Ollama is ALREADY RUNNING - skip to model commands below!

# ONLY run this if ollama ps shows "connection refused"
ollama serve
```

### **Model Management**
```bash
# List available models (works if service is running)
ollama list

# Pull recommended models for KILO-FOOLISH
ollama pull phi:2.7b
ollama pull mistral:7b-instruct
ollama pull codellama:7b-instruct
ollama pull llama2:7b-chat

# Remove model (replace with actual model name)
ollama rm phi:2.7b
```

## 💬 Direct Chat Commands (READY TO USE NOW!)

### **Basic Chat Sessions**
```bash
# Start chat with specific model
ollama run phi:2.7b
ollama run mistral:7b-instruct
ollama run codellama:7b-instruct
ollama run llama2:7b-chat

# Exit chat: type /bye or /exit
```

### **One-Shot Commands**
```bash
# Quick question without entering chat
ollama run phi:2.7b "Explain this code error: YOUR_ERROR_HERE"
ollama run codellama:7b-instruct "Write a Python function to DESCRIBE_TASK"
ollama run mistral:7b-instruct "Analyze this system architecture: PASTE_DESCRIPTION"
```

## 🔧 KILO-FOOLISH Specific Commands

### **System Prompts for Our Project**
```bash
# PowerShell assistance
ollama run codellama:7b-instruct --system "You are a PowerShell expert working on the KILO-FOOLISH project. Follow our logging patterns using Write-SetupLog. Use comprehensive error handling with try-catch blocks."

# Python development
ollama run phi:2.7b --system "You are a Python developer working on the KILO-FOOLISH ΞNuSyQ₁ framework. Include type hints, docstrings, and comprehensive error handling."

# AI integration help
ollama run mistral:7b-instruct --system "You are an AI integration specialist for the KILO-FOOLISH project. Help with Ollama, OpenAI, and multi-AI coordination strategies."
```

### **Common Task Commands**
```bash
# Code review
ollama run codellama:7b-instruct "Review this PowerShell script for KILO-FOOLISH compliance: PASTE_SCRIPT_HERE"

# Documentation help
ollama run phi:2.7b "Create documentation for this Python module following KILO-FOOLISH patterns: PASTE_CODE_HERE"

# Architecture questions
ollama run mistral:7b-instruct "How should I structure this feature in the ΞNuSyQ₁ architecture: DESCRIBE_FEATURE"
```

## 🌐 API Integration Commands

### **PowerShell Integration**
```powershell
# Function to query Ollama from PowerShell
function Invoke-OllamaQuery {
    param(
        [string]$Model = "phi:2.7b",
        [string]$Prompt,
        [string]$SystemPrompt = ""
    )
    
    try {
        $body = @{
            model = $Model
            prompt = $Prompt
            stream = $false
        }
        
        if ($SystemPrompt) {
            $body.system = $SystemPrompt
        }
        
        $jsonBody = $body | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body $jsonBody -ContentType "application/json"
        
        Write-Host "✓ Ollama query completed successfully" -ForegroundColor Green
        return $response.response
    }
    catch {
        Write-Host "✗ Ollama query failed: $_" -ForegroundColor Red
        return $null
    }
}

# Usage examples
$result = Invoke-OllamaQuery -Model "codellama:7b-instruct" -Prompt "Write a PowerShell function with error handling"
$result = Invoke-OllamaQuery -Model "phi:2.7b" -Prompt "Explain this error" -SystemPrompt "You are a debugging expert"
```

### **Python Integration**
```python
import requests
import json

def query_ollama(model: str, prompt: str, system_prompt: str = "") -> str:
    """Query Ollama API following KILO-FOOLISH patterns."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        result = response.json()
        print(f"✓ Ollama query completed successfully")
        return result.get("response", "")
        
    except Exception as e:
        print(f"✗ Ollama query failed: {e}")
        return ""

# Usage examples
result = query_ollama("codellama:7b-instruct", "Write a Python class for AI coordination")
result = query_ollama("phi:2.7b", "Debug this error", "You are a Python debugging expert")
```

## 🎯 Project-Specific Workflows

### **Daily Development Startup**
```bash
# 1. Check if Ollama is running (most likely it is!)
ollama ps

# 2. If you see models listed, you're ready to go!
# If you get connection errors, then start the service:
# ollama serve

# 3. Verify models are available
ollama list

# 4. Test connection
ollama run phi:2.7b "Hello, ready to work on KILO-FOOLISH!"
```

### **Code Generation Workflow**
```bash
# 1. For PowerShell scripts
ollama run codellama:7b-instruct --system "You are a PowerShell expert for KILO-FOOLISH. Use Write-SetupLog for logging, comprehensive error handling, and follow our naming conventions."

# 2. For Python modules
ollama run phi:2.7b --system "You are a Python developer for KILO-FOOLISH ΞNuSyQ₁. Include type hints, docstrings, and integrate with our AI coordination framework."

# 3. For documentation
ollama run mistral:7b-instruct --system "You are a technical writer for KILO-FOOLISH. Create clear, comprehensive documentation with code examples."
```

### **Troubleshooting Commands**
```bash
# Test if Ollama API is responding
curl http://localhost:11434/api/tags

# Check what models are loaded
ollama ps

# If service isn't responding, restart it:
# 1. Find and close any terminal running "ollama serve"
# 2. Run: ollama serve
# 3. Test: ollama ps
```

## 📊 Model Recommendations

### **For Different Tasks**
```bash
# Code generation and debugging
ollama run codellama:7b-instruct

# General questions and explanations  
ollama run phi:2.7b

# Complex reasoning and architecture
ollama run mistral:7b-instruct

# Conversational assistance
ollama run llama2:7b-chat
```

### **Performance Tips**
```bash
# Use smaller models for quick tasks
ollama run phi:2.7b "Quick question..."

# Use larger models for complex tasks
ollama run mistral:7b-instruct "Complex architecture decision..."

# Keep models loaded by running them once
ollama run phi:2.7b "warmup"
```

## 🔗 Integration with Existing Systems

### **With setup.ps1**
```powershell
# Add to setup.ps1 for AI assistance
$aiHelp = Invoke-OllamaQuery -Model "phi:2.7b" -Prompt "What should I do next in the KILO-FOOLISH setup?"
Write-SetupLog "AI Suggestion: $aiHelp" "INFO"
```

### **With diagnostic systems**
```powershell
# Get AI help for errors
$errorAnalysis = Invoke-OllamaQuery -Model "codellama:7b-instruct" -Prompt "Analyze this error: $errorMessage"
Write-SetupLog "AI Error Analysis: $errorAnalysis" "INFO"
```

## 🎮 Game Development Commands

### **For Idler Game Development**
```bash
# Game mechanics help
ollama run phi:2.7b --system "You are a game developer working on an incremental idle game with AI optimization. Focus on resource management and automation systems."

# AI-driven difficulty
ollama run mistral:7b-instruct --system "You are an AI specialist for game balance. Help design systems that adapt difficulty based on player behavior."
```

## 🚨 Common Error Solutions

### **"bind: Only one usage of each socket address" Error**
```bash
# This means Ollama is ALREADY RUNNING - good!
# Skip ollama serve and go straight to:
ollama ps

# You should see something like:
# NAME    ID    SIZE    PROCESSOR    UNTIL
# (shows loaded models)
```

### **Connection Refused Error**
```bash
# Service not running, start it:
ollama serve

# Then test:
ollama ps
```

### **Model Not Found Error**
```bash
# Pull the model first:
ollama pull phi:2.7b

# Then try again:
ollama run phi:2.7b "test"
```

---

**Last Updated**: 2025-01-08  
**Compatible with**: KILO-FOOLISH workspace structure  
**Prerequisites**: Ollama installed (service may already be running)

*This file focuses on direct interaction commands and handles the common "port already in use" scenario.*
