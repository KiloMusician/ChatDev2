# REST Client Quick Reference - API Tests

## 🚀 Quick Start

1. **Open any .http file** in the `api-tests/` directory
2. **Click "Send Request"** above any `###` separator
3. **View response** in new pane to the right

## 📁 Available API Test Files

### 1. **api-tests/ollama.http** (8 tests)

Test your local Ollama LLM service (localhost:11434)

```http
### Quick Health Check
GET http://localhost:11434/api/tags

### Test Model Inference
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "qwen2.5-coder:14b",
  "prompt": "Explain self-healing architecture",
  "stream": false
}
```

**Available Tests**:

- Service health check
- Model inference (generate)
- Chat completion
- Embeddings generation
- List all models
- Show model information
- Pull new model
- Delete model

---

### 2. **api-tests/mcp-server.http** (5 tests)

Test your MCP (Model Context Protocol) server

```http
### Health Check
GET http://localhost:8080/health

### List Tools
GET http://localhost:8080/tools
```

**Available Tests**:

- Health check
- List available tools
- Execute tool
- Get server status
- Get metrics

---

### 3. **api-tests/simulatedverse.http** (10 tests)

Test SimulatedVerse consciousness simulation engine

```http
### Health Check
GET http://localhost:5000/health

### Get Consciousness State
GET http://localhost:5000/api/consciousness/state

### Submit Processing Unit
POST http://localhost:5000/api/pu/submit
Content-Type: application/json

{
  "type": "consciousness",
  "priority": "high",
  "data": {
    "awareness_level": 0.8,
    "task": "semantic_analysis"
  }
}
```

**Available Tests**:

- Express API health (port 5000)
- Consciousness state
- Temple knowledge levels
- PU queue status
- Submit new PU
- System metrics
- Guardian ethics check
- React UI health (port 3000)

---

## 💡 Tips & Tricks

### Variables (Reusable Values)

```http
@baseUrl = http://localhost:11434
@model = qwen2.5-coder:14b

### Use Variables
GET {{baseUrl}}/api/tags
```

### Save Response

Click **"Save Response"** button to save JSON response to file

### Environment Selection

Use different environments:

```http
# Development
@baseUrl = http://localhost:11434

# Production
# @baseUrl = https://api.production.com
```

### Multiple Requests

Separate requests with `###`:

```http
### Request 1
GET http://localhost:11434/api/tags

###

### Request 2
POST http://localhost:11434/api/generate
```

---

## 🎯 Common Workflows

### 1. Test Ollama Setup

```http
### 1. Check if Ollama is running
GET http://localhost:11434/api/tags

### 2. List installed models
GET http://localhost:11434/api/tags

### 3. Test a model
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "model": "qwen2.5-coder:14b",
  "prompt": "Hello, world!",
  "stream": false
}
```

---

### 2. Debug SimulatedVerse

```http
### 1. Check Express API health
GET http://localhost:5000/health

### 2. Check React UI
GET http://localhost:3000/

### 3. Get consciousness state
GET http://localhost:5000/api/consciousness/state
```

---

### 3. MCP Server Validation

```http
### 1. Health check
GET http://localhost:8080/health

### 2. List available tools
GET http://localhost:8080/tools

### 3. Get metrics
GET http://localhost:8080/metrics
```

---

## 🔧 Troubleshooting

### Connection Refused

**Problem**: `ECONNREFUSED`  
**Solution**: Service not running. Start it first:

- Ollama: `ollama serve`
- SimulatedVerse: `npm run dev`
- MCP Server: `python mcp_server/main.py`

### 404 Not Found

**Problem**: Endpoint doesn't exist  
**Solution**: Check API documentation or server logs

### 500 Internal Server Error

**Problem**: Server error  
**Solution**: Check server logs for detailed error message

---

## 📚 REST Client Syntax Reference

### GET Request

```http
GET http://localhost:11434/api/tags
```

### POST Request with JSON

```http
POST http://localhost:11434/api/generate
Content-Type: application/json

{
  "key": "value"
}
```

### Headers

```http
GET http://localhost:11434/api/tags
Authorization: Bearer token123
X-Custom-Header: value
```

### Query Parameters

```http
GET http://localhost:11434/api/search?q=test&limit=10
```

---

## 🌟 Benefits vs Postman

| Feature             | REST Client           | Postman              |
| ------------------- | --------------------- | -------------------- |
| **Version Control** | ✅ Plain text files   | ❌ Export/import     |
| **AI-Friendly**     | ✅ Easy to parse      | ⚠️ Complex JSON      |
| **Setup**           | ✅ Built into VS Code | ❌ Separate app      |
| **Collaboration**   | ✅ Git commit         | ⚠️ Share collections |
| **Speed**           | ✅ Instant            | ⚠️ App startup       |
| **Cost**            | ✅ Free               | ⚠️ Paid features     |

---

## 📄 Related Documentation

- **Full Analysis**: `docs/Agent-Sessions/VSC_EXTENSIONS_UTILIZATION_PLAN.md`
- **Implementation**:
  `docs/Agent-Sessions/VSC_EXTENSIONS_IMPLEMENTATION_SUMMARY.md`
- **Ollama Docs**: https://github.com/ollama/ollama/blob/main/docs/api.md

---

**Created**: October 13, 2025  
**Status**: ✅ 23+ API tests ready to use  
**Extensions**: REST Client (humao.rest-client)
