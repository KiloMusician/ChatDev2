# 🛠️ NuSyQ-Hub Workflows & Agent Guidance

## Overview
This document provides guidance for developers, agents, and AI assistants working in the NuSyQ-Hub repository. It outlines best practices, integration points, and workflow automation for seamless collaboration between Copilot, ChatDev, Ollama, and other systems.

---

## 🤖 Agent & Copilot Guidance
- **Preserve and Enhance:** Always enhance existing files and documentation. Never overwrite or delete without review.
- **Check for Existing Context:** Before generating new context or documentation, check for existing files (e.g., `CONTEXT.md`, `*_CONTEXT.md`, `INTEGRATION_SYSTEMS_CONTEXT.md`).
- **Merge, Don’t Duplicate:** If new information is needed, merge it into the most detailed existing file.
- **Log Backend Selection:** When running LLM tasks, always log whether Ollama or OpenAI is used, and when fallback occurs.
- **Use Enhanced Launcher:** Prefer `enhanced_agent_launcher.py` for all orchestration, testing, and integration tasks.
- **Health Checks:** Use the `health` action to verify system readiness before major workflows.

---

## 🧩 Integration Points
- **Ollama:** Primary LLM backend for ChatDev and agent workflows.
- **OpenAI:** Fallback LLM backend, only used if Ollama is unavailable.
- **ChatDev:** Multi-agent collaboration, always routed through Ollama first.
- **Copilot:** Real-time code assistance, integrated via bridge modules.
- **Bridge System:** Enables seamless context and workflow sharing between Copilot and ChatDev.

---

## 🚦 Workflow Automation
- **Testing:** Use `python src/scripts/enhanced_agent_launcher.py test <files>` for integration tests.
- **Review/Enhance:** Use `review` and `enhance` actions for collaborative code improvement.
- **System Health:** Run `python src/scripts/enhanced_agent_launcher.py health` before major changes.
- **Context Generation:** Update or merge context files as part of every major PR.

---

## 📚 Documentation Best Practices
- **Directory Context:** Every major directory should have a `CONTEXT.md` or similar file.
- **Integration Context:** Use `INTEGRATION_SYSTEMS_CONTEXT.md` for detailed integration documentation.
- **Snapshots:** Reference `.snapshots/` for architecture and historical context.
- **.github Directory:** Use this directory for workflow, contribution, and agent guidance docs.

---

## 📝 Contribution & Agent Notes
- **File Preservation Mandate:** Always prefer enhancement over replacement or deletion.
- **Agent Mode:** When running in agent mode, always check for existing documentation and context before making changes.
- **Human Review:** Major changes to integration, context, or workflow files should be reviewed by a human maintainer.

---

*This document is auto-generated and should be updated as workflows and integrations evolve.*
