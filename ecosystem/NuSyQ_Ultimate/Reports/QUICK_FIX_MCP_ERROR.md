# 🔧 Quick Fix: Chrome DevTools MCP Error

## The Error
```
Invalid URL
Process exited with code 1
Server exited before responding to `initialize` request
```

## Quick Fix (30 seconds)

### Step 1: Open VS Code User Settings
- Press: `Ctrl + Shift + P`
- Type: "Preferences: Open User Settings (JSON)"
- Press Enter

### Step 2: Find MCP Configuration
Search for one of these:
- `"mcp.servers"`
- `"chromedevtools"`
- `"chrome-devtools-mcp"`

### Step 3: Fix It

**Option A: Disable (if not needed)**
```json
// Comment out or delete this section:
// "mcp.servers": {
//   "chromedevtools/chrome-devtools-mcp": { ... }
// }
```

**Option B: Fix (if needed)**
```json
"mcp.servers": {
  "chromedevtools/chrome-devtools-mcp": {
    "command": "npx",
    "args": [
      "chrome-devtools-mcp@latest",
      "--isolated",
      "--headless"
    ]
  }
}
```

### Step 4: Save & Reload
- Save the file (Ctrl+S)
- Reload VS Code window: `Ctrl+Shift+P` → "Developer: Reload Window"

---

## Why This Happened
The MCP server is configured but missing required browser connection arguments.

## Impact
**NONE** - This is a VS Code setting issue, not a NuSyQ problem.
- NuSyQ works fine ✅
- Boss Rush continues ✅
- All systems operational ✅

---

**Status:** Informational Only
**Priority:** Low (can be ignored)
**Time to Fix:** 30 seconds
