# 🎮 Hacking Game End-to-End Test Guide

This guide tests the complete hacking loop: `nmap` → `connect` → `exploit` → `patch` → `traces`

## Prerequisites

```bash
# 1. Activate venv and start the API server
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
.\.venv\Scripts\Activate.ps1
python -m src.api.main  # or: uvicorn src.api.main:app --reload
```

Server should be running on `http://localhost:8000`

---

## 🔄 Test Sequence (Complete Loop - ~2 mins)

### Step 1: Smart Search for Hacking Help

**Query:** Ask fl1ght.exe what to do

```bash
curl -X GET "http://localhost:8000/api/fl1ght?q=hack"
```

**Expected Response:**
```json
{
  "query": "hack",
  "total_results": 5,
  "categories": {
    "hacking": 5,
    "commands": 0,
    ...
  },
  "results": [
    {
      "type": "hacking",
      "operation": "nmap",
      "endpoint": "POST /api/hack/nmap",
      "description": "Enumerate ports and vulnerabilities on a component",
      "relevance": 1.0
    },
    ...
  ],
  "suggestions": [
    "🎮 New to hacking? Start: POST /api/hack/nmap on 'python' component.",
    "Hacking: POST /api/hack/nmap (operation: nmap)"
  ]
}
```

---

### Step 2: Scan a Component (nmap)

**Action:** Discover ports and services on the 'python' component

```bash
curl -X POST "http://localhost:8000/api/hack/nmap" \
  -H "Content-Type: application/json" \
  -d '{"component_name": "python"}'
```

**Expected Response:**
```json
{
  "component": "python",
  "ip_address": "192.168.5.101",
  "ports": [
    {
      "port": 22,
      "service": "SSH",
      "open": true,
      "vulnerable": true,
      "exploit_type": "ssh_crack"
    },
    {
      "port": 443,
      "service": "HTTPS",
      "open": true,
      "vulnerable": true,
      "exploit_type": "ssl_bypass"
    }
  ],
  "services": ["SSH", "HTTPS", "RPC"],
  "vulnerabilities": ["outdated_openssh", "weak_ssl_config"],
  "open_exploits": ["ssh_crack", "ssl_bypass"],
  "security_level": 3,
  "trace_risk": 0.6,
  "timestamp": "2026-02-04T18:30:45.123Z"
}
```

---

### Step 3: Connect to a Component

**Action:** Establish an access session to 'python' on port 22 (SSH)

```bash
curl -X POST "http://localhost:8000/api/hack/connect" \
  -H "Content-Type: application/json" \
  -d '{"component_name": "python"}'
```

**Expected Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6",
    "component_name": "python",
    "access_level": 1,
    "created_at": "2026-02-04T18:30:50.123Z",
    "last_seen": "2026-02-04T18:30:50.123Z"
  }
}
```

**Save the session_id for later use**

---

### Step 4: Execute an Exploit (Privilege Escalation)

**Action:** Execute SSH crack to gain higher privileges

```bash
curl -X POST "http://localhost:8000/api/hack/exploit" \
  -H "Content-Type: application/json" \
  -d '{
    "component_name": "python",
    "exploit_type": "SSH_CRACK",
    "xp_reward": 50
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "component": "python",
  "access_level": 2,
  "xp_gained": 50,
  "trace_triggered": true
}
```

---

### Step 5: Check Active Traces (Alarm System)

**Action:** Monitor active trace timers (you triggered an alarm!)

```bash
curl -X GET "http://localhost:8000/api/hack/traces"
```

**Expected Response:**
```json
{
  "active_traces": 1,
  "traces": {
    "python": {
      "status": "TRACING",
      "countdown": 45
    }
  },
  "timestamp": "2026-02-04T18:30:55.123Z"
}
```

**⚠️ Note:** Trace is now active! Countdown is 45 seconds. You must patch before lockdown (0).

---

### Step 6: Patch the Component (Harden Defense)

**Action:** Remove vulnerabilities before trace completes

```bash
curl -X POST "http://localhost:8000/api/hack/patch" \
  -H "Content-Type: application/json" \
  -d '{"component_name": "python"}'
```

**Expected Response:**
```json
{
  "success": true,
  "component": "python",
  "message": "Patched"
}
```

---

### Step 7: Verify Patch (Check Traces Cleared)

```bash
curl -X GET "http://localhost:8000/api/hack/traces"
```

**Expected Response:**
```json
{
  "active_traces": 0,
  "traces": {},
  "timestamp": "2026-02-04T18:30:58.123Z"
}
```

✅ **Success!** Trace cleared.

---

## 🧪 Individual Endpoint Tests

### Test nmap on Different Components

```bash
# Test on ollama component
curl -X POST "http://localhost:8000/api/hack/nmap" \
  -H "Content-Type: application/json" \
  -d '{"component_name": "ollama"}'

# Test on postgres component
curl -X POST "http://localhost:8000/api/hack/nmap" \
  -H "Content-Type: application/json" \
  -d '{"component_name": "postgres"}'
```

### Test Different Exploit Types

```bash
# SQL injection
curl -X POST "http://localhost:8000/api/hack/exploit" \
  -H "Content-Type: application/json" \
  -d '{
    "component_name": "postgres",
    "exploit_type": "SQL_INJECT",
    "xp_reward": 75
  }'

# SSL bypass
curl -X POST "http://localhost:8000/api/hack/exploit" \
  -H "Content-Type: application/json" \
  -d '{
    "component_name": "python",
    "exploit_type": "SSL_BYPASS",
    "xp_reward": 60
  }'
```

### Test fl1ght.exe Smart Search Variations

```bash
# Search for scanning
curl -X GET "http://localhost:8000/api/fl1ght?q=scan"

# Search for exploits
curl -X GET "http://localhost:8000/api/fl1ght?q=exploit"

# Search for defense
curl -X GET "http://localhost:8000/api/fl1ght?q=patch"

# Search for access
curl -X GET "http://localhost:8000/api/fl1ght?q=connect"

# Search for alarms
curl -X GET "http://localhost:8000/api/fl1ght?q=trace"

# Default help (empty query)
curl -X GET "http://localhost:8000/api/fl1ght?q=hack"
```

### Test Context-Aware Suggestions

```bash
# First scan (should suggest "start with nmap")
curl -X GET "http://localhost:8000/api/fl1ght?q=hack"

# After scan (should suggest "connect next")
# [run nmap first]
curl -X GET "http://localhost:8000/api/fl1ght?q=next"

# After connect/exploit (should alert trace)
# [run exploit first to trigger trace]
curl -X GET "http://localhost:8000/api/fl1ght?q=alarm"

# During active trace (should show countdown)
curl -X GET "http://localhost:8000/api/fl1ght?q=trace"
```

---

## 📊 Success Criteria

### ✅ All Tests Pass When:

- [x] fl1ght returns hacking suggestions in "hacking" category
- [x] nmap returns ports and vulnerabilities
- [x] connect creates a session with session_id
- [x] exploit succeeds and triggers trace
- [x] traces endpoint shows active countdown
- [x] patch clears traces
- [x] fl1ght context-aware suggestions appear based on game state
- [x] Different exploit types work (SSH_CRACK, SQL_INJECT, SSL_BYPASS, etc.)
- [x] Different components can be scanned (python, ollama, postgres, etc.)

### 📈 Performance Targets

- nmap response: < 200ms
- exploit response: < 150ms
- patch response: < 100ms
- traces response: < 50ms
- fl1ght response: < 300ms

---

## 🐛 Troubleshooting

### "Hacking controller not available"

**Cause:** src/games/hacking_mechanics.py not imported correctly

**Fix:**
```bash
# Check import works
python -c "from src.games.hacking_mechanics import get_hacking_controller; print(get_hacking_controller())"
```

### 404 on /api/hack/ endpoints

**Cause:** Router not mounted or endpoints not defined

**Fix:**
```bash
# Check if hacking router is included in main app
grep -r "hack" src/api/main.py
```

### Session not persisting

**Cause:** In-memory HACK_SESSIONS dict resets on server restart

**Note:** This is expected for prototype. Persistence will be added in Phase 2.

---

## 🎯 Next Steps After Testing

1. **Test passes?** Move to Testing Chamber deployment
2. **Issues found?** Log to quest system with error details
3. **Performance good?** Ready for Phase 2 (Smart Search integration)
4. **User feedback needed?** Run playtest with agents

---

## 📝 Test Report Template

Copy this after running tests:

```
Hacking Game Test Report - [DATE]
==================================

fl1ght.exe Smart Search: ✅ PASS / ❌ FAIL
nmap Scanning: ✅ PASS / ❌ FAIL
Connect/Sessions: ✅ PASS / ❌ FAIL
Exploit Execution: ✅ PASS / ❌ FAIL
Trace Monitoring: ✅ PASS / ❌ FAIL
Patching Defense: ✅ PASS / ❌ FAIL
Context Suggestions: ✅ PASS / ❌ FAIL

Average Response Time: ___ ms
Errors Encountered: ___
Notes: ___
```

---

**Happy Hacking! 🎮 Test away and report results.**
