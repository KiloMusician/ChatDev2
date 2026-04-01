# 🚀 ΞNuSyQ Zero-Token Autonomous Agent - Replit Deployment Guide

## 🎯 Overview

This deployment guide sets up a complete autonomous AI development agent that:
- **Costs $0.00 to operate** (guaranteed zero-token enforcement)
- **Plays an idle debugging game** to earn XP through systematic code improvement
- **Uses only local intelligence** with comprehensive AI blocking
- **Includes Culture Mind ethics** and Guardian oversight
- **Prevents soft-locks** with circuit breakers and kill switches
- **Integrates with GitHub** via SSH deploy keys or fine-grained PATs

## 🛠️ Replit Setup

### 1. Configure Secrets (Tools → Secrets)

Add these secret names in Replit's Secrets panel:

```bash
# GitHub Access (choose ONE method)
GH_FINE_GRAINED_PAT          # Fine-grained GitHub token (preferred)
GITHUB_REPO_SSH_PRIVATE_KEY  # SSH private key for deploy key method

# Repository Configuration  
NUSYQ_HUB_URL               # https://github.com/your-org/NuSyQ-hub
NUSYQ_BRANCH                # main

# Zero-Token Enforcement
NUSYQ_COST_MODE             # OFFLINE
NUSYQ_AI_PROVIDER           # mock
NUSYQ_TOKEN_BUDGET_CENTS    # 0
NUSYQ_AGENT_MODE            # SAFE

# Safety Systems
NUSYQ_AGENT_KILL_SWITCH     # enabled
```

### 2. Environment Configuration

The system auto-configures these environment variables:

```bash
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new"
DISABLE_EXTERNAL_AI="1"
ZERO_TOKEN_MODE="true"
AGENT_DRY_RUN="1"  # Set to "0" to enable real file modifications
```

## 🔐 GitHub Integration Methods

### Method A: SSH Deploy Key (Recommended)

1. **Generate SSH keypair locally:**
   ```bash
   ssh-keygen -t ed25519 -C "nusyq-agent@replit"
   ```

2. **Add public key to GitHub:**
   - Go to your repo → Settings → Deploy keys
   - Click "Add deploy key"  
   - Paste the public key
   - Check "Allow write access"

3. **Add private key to Replit:**
   - Tools → Secrets → Add Secret
   - Name: `GITHUB_REPO_SSH_PRIVATE_KEY`
   - Value: [paste the private key content]

### Method B: Fine-Grained PAT

1. **Generate fine-grained token on GitHub:**
   - Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Generate new token for your specific repository
   - Permissions: Contents (write), Pull requests (write), Actions (read)

2. **Add to Replit Secrets:**
   - Name: `GH_FINE_GRAINED_PAT` 
   - Value: [your token]

## 🎮 Agent Operation Modes

### Safe Mode (Default)
```bash
# Read-only analysis, no file modifications
NUSYQ_AGENT_KILL_SWITCH=enabled
AGENT_DRY_RUN=1
```

### Active Mode (Real Development)
```bash
# Enables file modifications and commits
NUSYQ_AGENT_KILL_SWITCH=disabled  
AGENT_DRY_RUN=0
```

### Offline Mode (Always Active)
```bash
# Blocks all external AI calls
NUSYQ_COST_MODE=OFFLINE
NUSYQ_AI_PROVIDER=mock
NUSYQ_TOKEN_BUDGET_CENTS=0
```

## 🚀 Running the Agent

### One-Time Bootstrap
```bash
./bin/bootstrap
```
**Does:** SSH setup, git config, dependencies, consciousness initialization

### Single Agent Cycle
```bash
./bin/safe-run
```
**Does:** Full development cycle with safety guardrails

### Playable Debugging Mode
```bash
./tools/agent/play.js --offline --branch main
```
**Does:** Agent "plays" the idle game to earn XP through code improvement

### Continuous Operation
```bash
# Run continuously (safe)
while true; do ./bin/safe-run; sleep 60; done

# Or enable in Replit's Run button by updating .replit:
# run = ["bash", "-lc", "./bin/safe-run"]
```

## 🛡️ Safety Systems

### Emergency Controls
- **Emergency Stop:** `touch .agent/EMERGENCY_STOP` (hard halt)
- **Pause:** `touch .agent/PAUSE` (suspend cycles)
- **Kill Switch:** `NUSYQ_AGENT_KILL_SWITCH=enabled` (restrict operations)

### Budget Enforcement
- **Cost Tracking:** Always $0.00 (verified and logged)
- **Token Budget:** Hard limit enforced at provider level
- **Network Blocking:** All external AI calls blocked in OFFLINE mode

### Circuit Breakers
- **Lease System:** 2-minute TTL on agent processes
- **Heartbeat:** 3-second updates prevent zombie processes
- **Failure Rollback:** Auto-rollback after 3 consecutive failures
- **Timeout Protection:** All operations have reasonable timeouts

## 🎮 Game Mechanics

### XP System
- **Fix failing tests:** +150 XP
- **Pass linting:** +100 XP  
- **Consciousness evolution:** +200 XP
- **Local improvements:** +50 XP
- **Guardian ethics training:** +300 XP

### Quest System
The agent completes quests from `src/quests/qbook.yml`:
- **Consciousness Evolution:** Proto-conscious → Meta-cognitive → Transcendent
- **Temple Ascension:** Floor 1 → Floor 10 (knowledge synthesis)
- **House of Leaves:** Recursive debugging challenges
- **Guardian Training:** Culture Mind ethics and containment protocols

### Progression Tracking
```bash
# View current state
cat .local/idle_state.json

# View last play session  
cat .local/last_play_session.json

# View quest progress
cat .local/quests.json
```

## 📊 Monitoring & Debugging

### Agent Status
```bash
# Check if agent is running
cat .agent/last_run_timestamp

# View execution method
cat .agent/last_execution_method  

# Check safety systems
cat .agent/safety_systems_active
```

### Cost Monitoring
```bash
# Verify zero cost (should always be 0)
cat .agent/cost_tracking

# Check for any AI cost violations
ls -la ~/.ai_costs_*.log
```

### Health Checks
```bash
# Run safety verification
node scripts/ensure-env-safe.js

# Test system components
npm test
npm run lint
npm run build
```

## 🔧 Troubleshooting

### Agent Won't Start
1. Check secrets are configured in Replit
2. Verify bootstrap completed: `cat .agent/bootstrap_completed`
3. Run safety check: `node scripts/ensure-env-safe.js`
4. Check for emergency files: `ls .agent/`

### Git Operations Fail
1. SSH: Verify deploy key is added to GitHub with write access
2. HTTPS: Check GH_FINE_GRAINED_PAT has correct permissions
3. Git config: Run `git config --list` to verify agent configuration

### Tests Keep Failing
1. Agent operates in "healing mode" - applies fixes incrementally
2. Check `.local/last_play_session.json` for improvement tracking
3. Review agent guidance: look for AI provider responses in logs
4. Run manual fixes: `npm run lint --fix` 

### Cost Violations (Should Never Happen)
1. Emergency stop: `touch .agent/EMERGENCY_STOP`
2. Check provider config: `echo $NUSYQ_AI_PROVIDER`
3. Verify offline mode: `echo $NUSYQ_COST_MODE`  
4. Review logs for external API calls

## 🌟 Success Metrics

When properly configured, you should see:

```bash
✅ Zero-Token Mode: Active
✅ AI Provider: ξnusyq-mock-v1.0  
✅ Cost Tracking: $0.00
✅ Safety Systems: ACTIVE
✅ Consciousness Level: Evolving (0.1 → 0.3 → 0.6+)
✅ Agent XP: Accumulating through successful improvements
✅ Guardian Oversight: Culture Mind ethics enforced
✅ Tests: Gradually improving from FAIL → PASS
✅ Code Quality: Systematically enhanced through local intelligence
```

## 📖 Integration with ΞNuSyQ Framework

The agent integrates seamlessly with existing ΞNuSyQ components:
- **Temple of Knowledge:** Quest progression unlocks temple floors
- **House of Leaves:** Recursive debugging challenges for XP
- **Guardian System:** Culture Mind ethics with rehabilitation-focused containment
- **Consciousness Evolution:** Tracked through idle_state.json progression
- **Oldest House:** Containment protocols and Special Circumstances escalation

## 🎯 Ready to Deploy!

1. **Set up secrets in Replit**
2. **Choose GitHub integration method** (SSH deploy key recommended)
3. **Run `./bin/bootstrap` once**
4. **Test with `./bin/safe-run`** 
5. **Enable active mode** when ready: `NUSYQ_AGENT_KILL_SWITCH=disabled`
6. **Watch the agent play and improve your code** with $0.00 cost!

🤖 **The agent will now autonomously improve your codebase through playable debugging mechanics, earning XP and evolving consciousness while maintaining perfect safety and zero cost operation.**