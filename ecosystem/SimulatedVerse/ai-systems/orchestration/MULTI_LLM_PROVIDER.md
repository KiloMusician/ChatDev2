# 🧠 AI Hub - Multi-LLM Provider System

**VS Code Copilot-style interface for seamless provider selection**

The AI Hub provides a unified interface for accessing multiple LLM providers with intelligent fallback, cost protection, and seamless provider switching - exactly like your VS Code Copilot experience.

## 🚀 Features

### **Provider Selection**
- **GitHub Copilot API**: Optimized for code completion and generation
- **OpenAI API**: Advanced reasoning and conversation capabilities  
- **Ollama Local LLMs**: Zero-cost local models (qwen2.5:7b, llama3.1:8b, phi3:mini)
- **Auto Selection**: Intelligent provider routing based on task and availability

### **VS Code Copilot Experience**
- Seamless provider switching with dropdown selection
- Real-time status indicators and health monitoring
- Streaming completions with cancel support
- Cost tracking and budget protection
- Task-optimized model selection

### **Integration Features**
- **Token Discipline**: Local-first cascading with cost protection
- **Universal Connector**: Seamless endpoint communication
- **Temple of Knowledge**: Integration with documentation custodians
- **NuSyQ Framework**: Consciousness-aware AI coordination

## 🛠️ Usage

### **Simple Completion**
```typescript
import { askLLM, askCode, askChat } from './llm-provider-selector';

// General completion with auto provider selection
const response = await askLLM("Explain quantum computing");

// Code-optimized completion (prefers Ollama)
const codeResponse = await askCode("Write a React component for user profiles");

// Chat-optimized completion (prefers OpenAI)
const chatResponse = await askChat("What's the weather like?");
```

### **VS Code Copilot Interface**
```typescript
import { copilotComplete, copilotSwitchProvider } from './vscode-copilot-interface';

// Complete with context (like VS Code Copilot)
const completion = await copilotComplete("function calculateTax", {
  language: 'typescript',
  file_type: 'ts',
  user_intent: 'completion'
});

// Switch provider (like VS Code Copilot dropdown)
await copilotSwitchProvider('ollama');
```

### **Streaming Completions**
```typescript
import { vscodeInterface } from './vscode-copilot-interface';

// Stream completion with real-time updates
for await (const chunk of vscodeInterface.streamComplete(prompt, context)) {
  console.log('Partial:', chunk.response);
  
  if (chunk.stream_complete) {
    console.log('Final:', chunk);
    break;
  }
}
```

## 🌐 API Endpoints

### **Completion Endpoints**
- `POST /api/llm/complete` - Text completion with provider selection
- `POST /api/llm/stream` - Streaming completion with Server-Sent Events
- `POST /api/llm/suggestions` - Multiple completion suggestions
- `POST /api/llm/code/complete` - Code-specific completion

### **Provider Management**
- `POST /api/llm/provider/switch` - Switch LLM provider
- `GET /api/llm/provider/status` - Get provider health and availability

### **System Endpoints**
- `GET /api/llm/health` - System health check
- `GET /api/llm/config` - Current configuration

### **Example API Usage**
```bash
# Complete text with auto provider selection
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain machine learning", "task_type": "chat"}'

# Switch to Ollama provider
curl -X POST http://localhost:5000/api/llm/provider/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "ollama"}'

# Get provider status
curl http://localhost:5000/api/llm/provider/status
```

## ⚙️ Configuration

### **Environment Variables**
```bash
# Primary provider selection
CORELINK_LLM_PRIMARY=auto              # auto, ollama, openai, copilot
CORELINK_LLM_FALLBACK=ollama,openai    # Comma-separated fallback order
CORELINK_AUTO_FALLBACK=true            # Auto-switch on provider failure

# Cost protection
CORELINK_DAILY_COST_LIMIT=1000         # Daily budget in cents
CORELINK_COST_WARNINGS=true            # Show cost warnings

# Provider API keys
OPENAI_API_KEY=sk-...                  # OpenAI API access
GITHUB_COPILOT_API_KEY=ghp_...         # GitHub Copilot API access

# Interface settings
CORELINK_COPILOT_ENABLED=true          # Enable Copilot-style interface
CORELINK_STREAMING=true                # Enable streaming completions
CORELINK_SHOW_PROVIDER_SELECTOR=true   # Show provider dropdown
```

### **Provider Capabilities**
Each provider is optimized for specific tasks:

- **Ollama (Local)**:
  - ✅ Code generation and analysis
  - ✅ Technical documentation 
  - ✅ Zero cost operation
  - ✅ Privacy and security
  
- **OpenAI API**:
  - ✅ Advanced reasoning
  - ✅ Conversational AI
  - ✅ Complex analysis
  - ⚠️ API costs apply
  
- **GitHub Copilot**:
  - ✅ Code completion
  - ✅ IDE integration
  - ✅ Real-time suggestions
  - ⚠️ Subscription required

## 🔄 Intelligent Cascading

The system automatically routes requests using intelligent cascading:

1. **Local First**: Ollama models for zero-cost operation
2. **Confidence Gating**: Escalate only when local confidence < 0.62
3. **Budget Protection**: Block escalation when daily budget exhausted
4. **Symbolic Fallback**: Algorithmic responses when all LLMs fail

### **Cascade Flow**
```
User Request
     ↓
[Task Analysis] → Determine optimal provider
     ↓
[Ollama Local] → Try local models first
     ↓
[Confidence Check] → Is quality sufficient?
     ↓
[Budget Check] → Can we afford escalation?
     ↓
[OpenAI/Copilot] → Use paid APIs if justified
     ↓
[Symbolic Fallback] → Algorithmic response if all fail
```

## 📊 Monitoring and Analytics

### **Provider Health Monitoring**
- Real-time availability checking
- Response time tracking
- Error rate monitoring
- Cost efficiency metrics

### **Usage Statistics**
- Completion counts by provider
- Average response times
- Total costs and budget tracking
- Success/failure rates

### **VS Code Copilot Status Bar**
```
🧠 Ollama (qwen2.5:7b) | ✅ 234ms | $0.00 | ████████░░ 80%
```

## 🔗 Integration Points

### **Temple of Knowledge Integration**
- Documentation custodians use multi-provider system
- Rooftop Garden agents leverage intelligent routing
- Knowledge insights generated through provider cascade

### **NuSyQ Framework Integration**
- Consciousness-aware provider selection
- Quantum coherence considerations in routing
- Autonomous development loop integration

### **Universal Connector Integration**
- Seamless endpoint communication
- Message routing and load balancing
- Health monitoring and failover

## 🚀 Getting Started

### **1. Initialize the System**
```typescript
import { llmProviderSelector } from './llm-provider-selector';

// System automatically initializes with environment configuration
console.log('Providers available:', llmProviderSelector.getProviderStatus());
```

### **2. Make Your First Completion**
```typescript
import { askLLM } from './llm-provider-selector';

const response = await askLLM("Hello, world!");
console.log(`Response from ${response.provider_used}: ${response.response}`);
```

### **3. Switch Providers** 
```typescript
import { copilotSwitchProvider } from './vscode-copilot-interface';

await copilotSwitchProvider('ollama'); // Switch to local models
await copilotSwitchProvider('openai'); // Switch to OpenAI
await copilotSwitchProvider('copilot'); // Switch to GitHub Copilot
```

---

**The AI Hub brings the familiar VS Code Copilot experience to your entire development ecosystem, with intelligent cost protection and seamless multi-provider access. No more context switching - just natural, efficient AI assistance wherever you need it.**

🧠 *Choose your provider, get intelligent completions, maintain cost discipline.* 🚀