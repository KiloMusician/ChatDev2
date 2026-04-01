# Projects Directory

**Purpose:** Sandbox for building games, tools, and applications using the NuSyQ development ecosystem.

## Directory Structure

- `active/` - Projects currently being developed
- `archived/` - Completed or paused projects
- `experiments/` - Throwaway prototypes (not tracked by git)
- `_templates/` - Project starter templates

## Usage

### Creating a New Project

1. Choose a template from `_templates/` or start from scratch
2. Create directory in `active/<project-name>/`
3. Initialize your project (npm init, godot project, etc.)
4. Start building!

### What Gets Tracked

✅ **Tracked** (committed to git):
- Source code
- Configuration files (package.json, requirements.txt, etc.)
- Documentation
- Small assets (<5MB)
- Build scripts

❌ **Ignored** (not committed):
- Dependencies (node_modules, venv, .godot, etc.)
- Build artifacts (dist, build, exe files, etc.)
- Environment files (.env, secrets)
- Logs and temporary files
- Large binary assets (>5MB)

### When to Archive

Move projects to `archived/` when:
- Project is completed and deployed
- Project is paused indefinitely
- You want to keep the source but not actively develop

### When to Use Experiments

Use `experiments/` for:
- Quick prototypes (<1 hour)
- Testing ideas you'll likely discard
- Learning experiments
- Anything you don't want in git history

## Examples

```bash
# Create a new Godot game
cp -r _templates/godot-game active/my-tower-defense
cd active/my-tower-defense
godot --editor

# Create a new web app
cp -r _templates/web-app active/my-synthesizer
cd active/my-synthesizer
npm install
npm run dev

# Quick prototype (not tracked)
mkdir experiments/ai-voice-test
cd experiments/ai-voice-test
# ... hack away, will never be committed ...
```

## Philosophy

This directory embodies the Culture Ship principle:

> "Our repository is for healing/developing/evolving/learning/cultivating/stewarding 'like the culture ship...', and building awesome games and programs!"

- **Healing:** Learn from experiments, improve skills
- **Developing:** Build actual deliverables
- **Evolving:** Try new patterns, iterate designs
- **Learning:** Prototype ideas, test hypotheses
- **Cultivating:** Grow a portfolio of projects
- **Stewarding:** Maintain and refine completed work

The system (NuSyQ-Hub, ChatDev, SimulatedVerse, orchestration, AI agents) is the **gardener**.

The Projects/ directory is the **garden**.

Let the system help you build amazing things!
