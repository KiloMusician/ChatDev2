---
applyTo: '.github/instructions/*'
priority: CRITICAL
---

# 📚 Context Registry

This registry maps the key documentation and configuration files in the `.github` directory to their purposes and locations.

- 🧠 `.github/instructions/`: Instructional memory core for project context and development guidelines. Files:
  - `COPILOT_INSTRUCTIONS_CONFIG.instructions.md`
  - `GITHUB_INSTRUCTIONS_CONTEXT.md`
  - `intelligence-discovery.md`
  - `repository-context.md`

- 🕸️ `.github/prompts/`: AI prompt templates and interaction patterns. Files:
  - `GITHUB_PROMPTS_CONTEXT.md`
  - `interaction-templates.md`

- 🚦 `.github/workflows/`: CI/CD and automation workflows. Files:
  - `ci.yml`
  - `security-scan.yml`
  - `labeler.yml`

- ⚙️ Root configuration:
  - `copilot.yaml`: Copilot repository configuration for advanced AI collaboration.
  - `dependabot.yml`: Scheduled dependency updates.
  - `CODEOWNERS`: Repository code ownership rules.

_For more details on usage and integration, refer to each file directly._
