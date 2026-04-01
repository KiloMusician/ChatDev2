#!/usr/bin/env python3
"""
CULTIVATION CYCLE 0 – DIAGNOSTIC SCAN
The Garden's First Breath

Scans the entire ecosystem for:
- File inventory
- Service health
- Repository structure
- Critical gaps
- Alignment metrics
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def run_cmd(cmd):
    """Run a shell command and capture output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return ""

def main():
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                        CULTIVATION CYCLE 0 – SCAN                          ║")
    print("║                    The Garden's First Diagnostic Walk                       ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    scan_log = {
        'timestamp': datetime.now().isoformat(),
        'cycle': 0,
        'phase': 'SCAN',
        'repository_root': os.getcwd(),
        'services': {
            'running': [],
            'stopped': [],
        },
        'gaps': {
            'p0_critical': [],
            'p1_important': [],
            'p2_nice_to_have': []
        },
        'metrics': {
            'total_files': 0,
            'python_files': 0,
            'yaml_files': 0,
            'markdown_files': 0
        }
    }
    
    # ========================================================
    # 1. FILE INVENTORY
    # ========================================================
    print("📊 FILE INVENTORY SCAN")
    print()
    
    root = Path('.')
    file_count = {'.py': 0, '.yaml': 0, '.yml': 0, '.md': 0, 'other': 0}
    
    for fpath in root.rglob('*'):
        if '.git' in str(fpath) or '__pycache__' in str(fpath) or '.venv' in str(fpath):
            continue
        if fpath.is_file():
            if fpath.suffix == '.py':
                file_count['.py'] += 1
            elif fpath.suffix in ['.yaml', '.yml']:
                file_count['.yaml'] += 1
            elif fpath.suffix == '.md':
                file_count['.md'] += 1
            else:
                file_count['other'] += 1
    
    print(f"  Python files:      {file_count['.py']:5}")
    print(f"  Config files:      {file_count['.yaml']:5}")
    print(f"  Documentation:     {file_count['.md']:5}")
    print(f"  Other files:       {file_count['other']:5}")
    print(f"  TOTAL:             {sum(file_count.values()):5}")
    print()
    
    # ========================================================
    # 2. SERVICE STATUS
    # ========================================================
    print("🔧 SERVICE STATUS")
    print()
    
    services = [
        ('Dev-Mentor backend', 'terminal-depths-backend', 7337),
        ('Ollama', 'terminal-depths-ollama', 11434),
        ('RimWorld', 'terminal-depths-rimworld', 9000),
        ('NuSyQ Bridge', 'nusyq-bridge', 9876),
        ('ChatDev', 'chatdev-orchestrator', 7338),
        ('MCP Server', 'mcp-server', 8765),
    ]
    
    for name, container, port in services:
        try:
            result = run_cmd(f"docker ps --filter name={container} --format '{{{{.Status}}}}'")
            if result and 'Up' in result:
                print(f"  ✓ {name:25} (:{port})")
                scan_log['services']['running'].append(name)
            else:
                print(f"  ✗ {name:25} (stopped)")
                scan_log['services']['stopped'].append(name)
        except:
            print(f"  ? {name:25} (unknown)")
    
    print()
    
    # ========================================================
    # 3. CRITICAL GAPS (P0)
    # ========================================================
    print("⚠️  CRITICAL GAPS (P0)")
    print()
    
    critical_checks = {
        'Gordon SQLite schema fixed': Path('state/gordon_memory.db').exists(),
        'Docker Compose up': len(scan_log['services']['running']) > 0,
        'Serena working': run_cmd("curl -s http://localhost:7337/api/serena/align 2>/dev/null | grep -q ok && echo yes") == "yes",
        'Backend API responding': run_cmd("curl -s http://localhost:7337 2>/dev/null | wc -c") != "0",
    }
    
    for check, status in critical_checks.items():
        if status:
            print(f"  ✓ {check}")
        else:
            print(f"  ✗ {check}")
            scan_log['gaps']['p0_critical'].append(check)
    
    print()
    
    # ========================================================
    # 4. MISSING FEATURES (P1)
    # ========================================================
    print("📝 MISSING FEATURES (P1)")
    print()
    
    missing_features = [
        ('Cultivation command', Path('scripts/cultivation.py').exists()),
        ('Health dashboard', Path('app/dashboard.py').exists()),
        ('ARG system complete', Path('knowledge/arcs/arcs.yaml').exists()),
        ('Challenge pool generated', Path('tasks/challenges.json').exists()),
        ('Lore fully indexed', Path('knowledge/lore').exists()),
    ]
    
    for feature, exists in missing_features:
        if exists:
            print(f"  ✓ {feature}")
        else:
            print(f"  ⊙ {feature} (incomplete)")
            scan_log['gaps']['p1_important'].append(feature)
    
    print()
    
    # ========================================================
    # 5. NICE-TO-HAVE (P2)
    # ========================================================
    print("🌟 NICE-TO-HAVE FEATURES (P2)")
    print()
    
    nice_to_have = [
        'GraphQL API',
        'Real-time WebSocket updates',
        'Agent performance metrics dashboard',
        'Automated benchmark suite',
        'CI/CD pipeline for repositories',
    ]
    
    for feature in nice_to_have:
        print(f"  ⊙ {feature}")
        scan_log['gaps']['p2_nice_to_have'].append(feature)
    
    print()
    
    # ========================================================
    # 6. SAVE SCAN LOG
    # ========================================================
    print("💾 SAVING SCAN LOG")
    print()
    
    state_path = Path('state')
    state_path.mkdir(exist_ok=True)
    
    log_file = state_path / 'cultivation_log.json'
    with open(log_file, 'w') as f:
        json.dump(scan_log, f, indent=2)
    
    print(f"  ✓ Saved to {log_file}")
    print()
    
    # ========================================================
    # 7. SUMMARY & RECOMMENDATIONS
    # ========================================================
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                        SCAN COMPLETE – GARDEN MAP                         ║")
    print("╠════════════════════════════════════════════════════════════════════════════╣")
    print(f"║ Total files:           {sum(file_count.values()):40} ║")
    print(f"║ Services running:      {len(scan_log['services']['running']):40} ║")
    print(f"║ Critical gaps:         {len(scan_log['gaps']['p0_critical']):40} ║")
    print(f"║ Important features:    {len(scan_log['gaps']['p1_important']):40} ║")
    print("║                                                                            ║")
    print("║ NEXT STEPS:                                                              ║")
    print("║  1. Fix critical gaps (SQLite, Gordon)                                    ║")
    print("║  2. Implement P1 features (Health dashboard, ARG completion)              ║")
    print("║  3. Run agent swarm on task queue                                         ║")
    print("║  4. Begin continuous cultivation cycles                                   ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    main()
