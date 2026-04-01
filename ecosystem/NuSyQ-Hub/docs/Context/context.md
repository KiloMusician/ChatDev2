# GitHub Copilot Context & Collaboration Guide
# This file helps Copilot understand the KILO-FOOLISH project better

## 🎯 Project Overview for AI Assistance

### **Core Mission**
KILO-FOOLISH is an experimental AI-assisted development framework that combines:
- **ΞNuSyQ₁ Quantum Architecture**: Multi-dimensional system design
- **AI Copilot Integration**: You (GitHub Copilot) + Ollama + OpenAI coordination  
- **Self-Healing Systems**: Automated error detection and resolution
- **Idler Game Development**: Complex incremental game mechanics

### **Current Development Phase**
- ✅ **Phase 1**: Environment Setup (90% complete)
- 🔄 **Phase 2**: Core Infrastructure (in progress)
- 📋 **Phase 3**: AI Integration (planning)
- 🚀 **Phase 4**: Feature Development (future)

## 🧠 How to Best Assist This Project

### **Code Generation Preferences**
- **Language Priority**: PowerShell > Python > JavaScript
- **Style**: Modular, well-documented, enterprise-grade
- **Architecture**: Prefer functions over scripts, clear separation of concerns
- **Error Handling**: Comprehensive try-catch with logging
- **Documentation**: Inline comments + README updates

### **Common Tasks You'll Help With**
1. **PowerShell Scripts**: Environment setup, diagnostics, automation
2. **Python Modules**: AI integration, data processing, game logic  
3. **Configuration Files**: JSON, YAML, INI for various tools
4. **Documentation**: Markdown files, code comments, API docs
5. **Integration Code**: API wrappers, service connectors

### **Project-Specific Patterns**
```powershell
# Logging pattern we use everywhere
Write-SetupLog "Message here" "LEVEL"  # LEVEL: INFO, SUCCESS, WARNING, ERROR

# Configuration loading pattern
try {
    . ".\config\project.ps1"
    $ProjectName = Get-ProjectName
}
catch {
    $ProjectName = "KILO-FOOLISH"  # Always have fallback
}

# Error handling pattern
try {
    # Main operation
    Write-SetupLog "Operation completed ✓" "SUCCESS"
}
catch {
    Write-SetupLog "Operation failed: $_" "ERROR"
    return $false
}
```

## 🔍 Key Files & Their Purposes

### **Core Infrastructure**
- `setup.ps1` - Main environment setup script (your primary focus)
- `config/project.ps1` - Project constants and configuration
- `config/secrets.ps1` - API keys and sensitive data (never commit)
- `src/diagnostics/ErrorDetector.ps1` - Self-healing system
- `src/ai/RoadmapAssistant.ps1` - AI coordination and guidance

### **File Naming Conventions**
- PowerShell: `PascalCase.ps1`
- Python: `snake_case.py`
- Config: `lowercase.extension`
- Documentation: `UPPERCASE.md` for important files

### **Directory Structure Logic**
```
src/           # All source code
├── ai/        # AI integration modules  
├── diagnostics/ # Self-healing and error detection
├── game/      # Idler game development
└── utils/     # Shared utilities

config/        # All configuration files
tests/         # Automated tests
docs/          # Documentation
data/          # Application data
logs/          # Log files
```

## 🤖 AI Integration Context

### **Multi-AI Coordination Strategy**
- **GitHub Copilot (You)**: Real-time code generation and debugging
- **Ollama**: Local AI processing, privacy-focused tasks
- **OpenAI**: Complex reasoning, high-level planning
- **QuantumArchitect**: Future meta-coordination layer

### **When to Suggest Each AI**
- **Immediate coding help**: You (Copilot)
- **Local experimentation**: Ollama  
- **Complex architecture decisions**: OpenAI
- **System optimization**: Diagnostic tools + AI analysis

## 🎮 Idler Game Development Context

### **Game Concept**
- **Genre**: Incremental/idle game with AI optimization
- **Tiers**: Survival → Expansion → Mastery
- **Mechanics**: Resource management, automation, AI-driven difficulty
- **Integration**: Uses the same AI framework as the development tools

### **Technical Approach**
- **Backend**: Python for game logic
- **Frontend**: TBD (web-based likely)
- **AI**: Real-time optimization of game balance
- **Data**: SQLite for development, PostgreSQL for production

## 📋 Common Copilot Prompts That Work Well

### **For PowerShell Development**
- "Create a PowerShell function that [specific task] with error logging"
- "Add error handling and logging to this PowerShell script"
- "Generate a PowerShell module for [functionality] following our patterns"

### **For Python Development**  
- "Create a Python class for [purpose] with type hints and docstrings"
- "Add AI integration to this Python module using OpenAI API"
- "Generate unit tests for this Python function"

### **For Configuration**
- "Create a JSON config file for [purpose] with validation"
- "Generate a requirements.txt with these packages and version constraints"
- "Create VS Code settings for this project type"

## 🔧 Development Workflow Context

### **Current Setup Process**
1. Run `setup.ps1` (installs tools, creates structure)
2. Configure `config/secrets.ps1` (API keys)
3. Run diagnostics (`ErrorDetector.ps1`)
4. Launch AI assistant (`RoadmapAssistant.ps1`)
5. Begin feature development

### **Testing Strategy**
- **Unit Tests**: pytest for Python, Pester for PowerShell
- **Integration Tests**: API connectivity, file operations
- **Self-Tests**: Diagnostic scripts validate environment

### **Deployment Strategy**
- **Development**: Local with virtual environments
- **Staging**: Docker containers
- **Production**: Cloud deployment (TBD)

## 🚨 Critical Considerations

### **Security Requirements**
- Never hardcode API keys in any file
- Always use `config/secrets.ps1` for sensitive data
- Validate all external inputs
- Log security events separately

### **Performance Priorities**
1. Startup time (environment setup)
2. AI response time (API calls)
3. Memory usage (large datasets)
4. Network efficiency (API rate limits)

### **Error Recovery Patterns**
- Always provide fallback options
- Log detailed error information
- Attempt automatic fixes when safe
- Guide user to manual solutions when needed

## 💡 Suggestions for Better Collaboration

### **When I Ask for Code**
- Include comprehensive error handling
- Add logging statements using our patterns
- Follow our naming conventions
- Include relevant comments
- Consider integration with existing modules

### **When I Ask for Architecture**
- Think modular and extensible
- Consider the AI coordination strategy
- Plan for self-healing capabilities
- Include configuration flexibility
- Design for both development and production

### **When I Ask for Documentation**
- Use our established markdown patterns
- Include code examples
- Reference existing files and patterns
- Consider multiple skill levels
- Update this context file if needed

## 🎯 Current Priorities (Update as Needed)

### **Immediate (This Week)**
- [ ] Complete setup.ps1 functionality
- [ ] Create all missing config files
- [ ] Test diagnostic system thoroughly
- [ ] Validate AI assistant integration

### **Short-term (Next Month)**  
- [ ] Implement core AI coordination
- [ ] Begin Idler game prototype
- [ ] Set up automated testing
- [ ] Create comprehensive documentation

### **Long-term (Future)**
- [ ] Full ΞNuSyQ₁ implementation
- [ ] Multi-agent AI ecosystem
- [ ] Production deployment
- [ ] Community/open-source release


---

## 🔄 Workflow Integration

### **Infrastructure Integration Status**
- **Chatdev Launcher**: ❌ Not Available
- **Testing Chamber**: ❌ Not Available
- **Quantum Automator**: ❌ Not Available
- **Ollama Integrator**: ❌ Not Available
- **Kilo Secrets**: ❌ Not Available

### **Workflow Capabilities**
Archive system integration

### **Subprocess Management**
Archive process management


### Subprocess Integration Guide

**Standard Archive Integration:**
```python
# Import relevant modules
from archive.archive_coordinator import ArchiveCoordinator

# Initialize coordinator
coordinator = ArchiveCoordinator()

# Execute archive operations
coordinator.execute_operations(parameters)
```


### **Rube Goldbergian Integration**
This directory integrates seamlessly with the modular KILO-FOOLISH workflow:
1. **ChatDev Integration**: Automated development task orchestration
2. **Ollama Bridge**: Local AI model integration with API fallback
3. **Testing Chamber**: Isolated development and testing environments
4. **Quantum Workflows**: Advanced workflow automation and optimization
5. **Consciousness Sync**: Repository awareness and memory integration

---

**Last Updated**: 2025-01-08
**Next Review**: When major architectural changes occur

*This file should be updated regularly to help Copilot provide increasingly better assistance as the project evolves.*
