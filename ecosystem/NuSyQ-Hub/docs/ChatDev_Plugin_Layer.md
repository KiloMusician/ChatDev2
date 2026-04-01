# ChatDev Plugin Layer (Symbiotic Integration)

The NuSyQ ecosystem treats ChatDev as a runtime/dependency layer rather than a hardwired submodule inside every workflow. This document describes how ChatDev can plug into NuSyQ (and vice versa) in a flexible, bi-directional manner.

## Goals

1. **Symbiotic integration** — our package can detect and consume a standalone ChatDev installation, and ChatDev-based projects can import our orchestration layers without bundling NuSyQ directly.  
2. **Selective activation** — the warehouse modules live in `ChatDev/WareHouse`; they should only be a focus when agents are consciously building against them.  
3. **Transparent onboarding** — provide users with CLI helpers to detect chatdev roots and configure environment variables before runtime.

## Plugin Concepts

1. **Environment discovery**
   * `CHATDEV_ROOT` (or `NuSyQ/ChatDev`) is treated like another optional dependency.  
   * NuSyQ can adjust `PYTHONPATH`/`sys.path` to load ChatDev helpers only when needed.  
2. **Plugin interface**
   * Create lightweight adapters that expose NuSyQ services (e.g., diagnostics, quests) to ChatDev modules.  
   * Provide `nusyq_plugin.py` style hooks that ChatDev consumers can import if they want orchestration without copying the whole repo.
3. **Two-way capability**
   * If a user already has ChatDev as part of their process, they can `pip install` or `git clone` NuSyQ and call helper scripts (see below).  
   * If our package is the core product, it can ensure the ChatDev dependency is installed (via instructions or automation) before exposing the "warehouse" experiences.

## CLI Helper Usage

We added `scripts/chatdev_plugin_helper.py` to inspect the environment:

```bash
python scripts/chatdev_plugin_helper.py --status
```

This script:

* Detects visible ChatDev roots (env vars, common repo paths).  
* Prints guidance about setting `CHATDEV_ROOT`/`SIMULATEDVERSE_ROOT`.  
* Lists warehouse projects that can be enabled via the new Auditor `--warehouse-projects` flag.

## Documented Flows

| Workflow | Description |
| --- | --- |
| **NuSyQ first** | Install NuSyQ, run `chatdev_plugin_helper`, then optionally `pip install -r requirements.txt` inside the detected ChatDev repo before you `python scripts/start_nusyq.py`. |
| **ChatDev first** | If a user already works inside ChatDev, they can import NuSyQ components by setting `CHATDEV_ROOT`, adding `NuSyQ-Hub/src` to `PYTHONPATH`, and invoking `nuSync` utilities from within their agent scripts. |

## Next Steps

* Extend `scripts/chatdev_plugin_helper.py` to optionally bootstrap dependency downloads (future work).  
* When we build a user-facing app/extension, expose these plugin hooks directly inside the UI so automations can choose “NuSyQ + ChatDev” vs “NuSyQ Core Only.”  
