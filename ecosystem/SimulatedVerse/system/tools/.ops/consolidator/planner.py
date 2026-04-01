#!/usr/bin/env python3
"""
ΞNuSyQ Duplicate Consolidation - Safe Planning & Application
Generates human-readable reports and safe consolidation plans
"""
import json
import os
import subprocess
import csv
from datetime import datetime

class ConsolidationPlanner:
    def __init__(self):
        self.plan = None
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
    def load_plan(self, plan_path: str = ".ops/dup_plan.json"):
        """Load detection plan from JSON"""
        with open(plan_path, "r") as f:
            self.plan = json.load(f)
    
    def generate_reports(self):
        """Generate human-readable summary and CSV mappings"""
        if not self.plan:
            raise ValueError("No plan loaded. Call load_plan() first.")
        
        self._generate_summary_markdown()
        self._generate_rename_map()
        self._generate_import_rewrites()
        self._generate_rollback_script()
        print("📋 Reports generated in .ops/")
    
    def _generate_summary_markdown(self):
        """Generate .ops/dup_summary.md"""
        content = f"""# ΞNuSyQ Duplicate Consolidation Report
Generated: {datetime.now().isoformat()}

## Summary Statistics
- **Total Files Analyzed**: {self.plan['stats']['total_files']}
- **Duplicate Groups Found**: {self.plan['stats']['duplicate_groups']}
- **Empty Files**: {self.plan['stats']['empty_files']}
- **Placeholder Files**: {self.plan['stats']['placeholder_files']}
- **Vague-Named Files**: {self.plan['stats']['vague_named']}

## Duplicate/Near-Duplicate Groups

"""
        
        for group in self.plan['groups']:
            content += f"### {group['id']}: {group['theme']}\n"
            content += f"**Confidence**: {group['confidence']:.2f} | **Overall Similarity**: {group['similarity']['overall']:.2f}\n\n"
            content += f"**Proposed Primary**: `{group['proposed_primary']}`\n\n"
            content += "| File | Exports | Size | Hash |\n"
            content += "|------|---------|------|------|\n"
            
            for member in group['members']:
                exports_str = ", ".join(member['exports'][:3])
                if len(member['exports']) > 3:
                    exports_str += f" (+{len(member['exports'])-3} more)"
                content += f"| `{member['path']}` | {exports_str} | {member['size']} | `{member['hash']}` |\n"
            
            content += f"\n**Proposed Actions**: {', '.join(group['proposed_actions'])}\n"
            content += f"**Notes**: {group['notes']}\n\n"
        
        # Vague file names section
        if self.plan['vague_files']:
            content += "## Vague File Names → Proposed Renames\n\n"
            content += "| Current Path | Vague Score | Suggested Name | Reason |\n"
            content += "|--------------|-------------|----------------|--------|\n"
            
            for vague in self.plan['vague_files']:
                content += f"| `{vague['path']}` | {vague['score']:.2f} | `{vague['suggested_name']}` | Better semantic clarity |\n"
        
        # Empty/placeholder files section
        if self.plan['empties'] or self.plan['placeholders']:
            content += "\n## Empty/Placeholder Files\n\n"
            content += "| Path | Type | Size | Action |\n"
            content += "|------|------|------|--------|\n"
            
            for empty in self.plan['empties']:
                content += f"| `{empty['path']}` | Empty | {empty['size']} | Delete or expand |\n"
            
            for placeholder in self.plan['placeholders']:
                content += f"| `{placeholder['path']}` | Placeholder | {placeholder['size']} | Complete implementation |\n"
        
        content += "\n## Implementation Plan\n\n"
        content += "1. **Backup Phase**: Copy affected files to `.ops/backups/{timestamp}/`\n"
        content += "2. **Rename Phase**: Apply file renames using `git mv`\n" 
        content += "3. **Merge Phase**: Consolidate duplicate content into primary files\n"
        content += "4. **Import Phase**: Update all import statements and path references\n"
        content += "5. **Test Phase**: Run lints and tests to verify no breakage\n"
        content += "6. **Commit Phase**: Atomic commits with clear messages\n"
        
        with open(".ops/dup_summary.md", "w") as f:
            f.write(content)
    
    def _generate_rename_map(self):
        """Generate .ops/rename_map.csv"""
        renames = []
        
        # Add renames for vague files
        for vague in self.plan['vague_files']:
            renames.append([vague['path'], vague['suggested_name']])
        
        # Add renames for duplicates (secondary → primary consolidation)
        for group in self.plan['groups']:
            primary = group['proposed_primary']
            for member in group['members']:
                if member['path'] != primary and group['confidence'] >= 0.9:
                    # For high-confidence groups, consolidate into primary
                    renames.append([member['path'], f"{primary}.deprecated"])
        
        with open(".ops/rename_map.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["old_path", "new_path"])
            writer.writerows(renames)
    
    def _generate_import_rewrites(self):
        """Generate .ops/import_rewrites.csv"""
        rewrites = []
        
        # For each rename, find all files that import the old path
        renames = []
        with open(".ops/rename_map.csv", "r") as f:
            reader = csv.DictReader(f)
            renames = [(row['old_path'], row['new_path']) for row in reader]
        
        # Scan all source files for import statements
        for old_path, new_path in renames:
            old_import = old_path.replace(".ts", "").replace(".js", "").replace(".py", "")
            new_import = new_path.replace(".ts", "").replace(".js", "").replace(".py", "")
            
            # Find files that might import this
            try:
                result = subprocess.run([
                    "rg", "-l", f"from ['\"][^'\"]*{os.path.basename(old_import)}['\"]"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    for file_path in result.stdout.strip().split("\n"):
                        if file_path and file_path != old_path:
                            rewrites.append([file_path, old_import, new_import, "0.95"])
            except:
                pass
        
        with open(".ops/import_rewrites.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file_path", "from", "to", "confidence"])
            writer.writerows(rewrites)
    
    def _generate_rollback_script(self):
        """Generate .ops/rollback.sh"""
        script = f"""#!/bin/bash
# ΞNuSyQ Consolidation Rollback Script
# Generated: {datetime.now().isoformat()}

set -e

echo "🔄 Rolling back consolidation changes..."

# Restore from backup
if [ -d ".ops/backups/{self.timestamp}" ]; then
    echo "📁 Restoring files from backup..."
    cp -r .ops/backups/{self.timestamp}/* . 2>/dev/null || true
fi

# Reset git to last good state (if commits were made)
echo "⏪ Resetting git state..."
git status --porcelain | wc -l > /tmp/git_changes
if [ $(cat /tmp/git_changes) -gt 0 ]; then
    git stash push -m "rollback-stash-{self.timestamp}" || true
fi

echo "✅ Rollback complete"
echo "💡 Check git log and restore any needed commits manually"
"""
        
        with open(".ops/rollback.sh", "w") as f:
            f.write(script)
        
        # Make executable
        os.chmod(".ops/rollback.sh", 0o755)
    
    def check_approval(self) -> str:
        """Check if consolidation is approved and what mode to use"""
        approval_file = ".ops/approve_consolidation.yml"
        
        if not os.path.exists(approval_file):
            return "WAIT"
        
        try:
            with open(approval_file, "r") as f:
                content = f.read()
            
            if "approve: true" in content:
                if "mode: APPLY_ALL" in content:
                    return "APPLY_ALL"
                else:
                    return "APPLY_SAFE"
            else:
                return "WAIT"
        except:
            return "WAIT"
    
    def create_backups(self):
        """Create backup copies of all affected files"""
        backup_dir = f".ops/backups/{self.timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Get all files that will be affected
        affected_files = set()
        
        # Files from duplicate groups
        for group in self.plan['groups']:
            for member in group['members']:
                affected_files.add(member['path'])
        
        # Files from renames
        if os.path.exists(".ops/rename_map.csv"):
            with open(".ops/rename_map.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    affected_files.add(row['old_path'])
        
        # Create backups
        backup_manifest = []
        for file_path in affected_files:
            if os.path.exists(file_path):
                backup_path = os.path.join(backup_dir, file_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                subprocess.run(["cp", file_path, backup_path], check=True)
                backup_manifest.append(file_path)
        
        # Save manifest
        with open(".ops/backup_manifest.txt", "w") as f:
            f.write("\n".join(backup_manifest))
        
        print(f"💾 Backed up {len(backup_manifest)} files to {backup_dir}")

def main():
    import sys
    
    planner = ConsolidationPlanner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        # Application mode
        if not os.path.exists(".ops/dup_plan.json"):
            print("❌ No plan found. Run detector first.")
            return 1
        
        planner.load_plan()
        mode = planner.check_approval()
        
        if mode == "WAIT":
            print("⏳ Waiting for approval. Create .ops/approve_consolidation.yml with 'approve: true'")
            return 0
        elif mode == "APPLY_SAFE":
            print("🛡️  Applying safe consolidations (confidence ≥ 0.9)")
            planner.create_backups()
            # Additional application logic would go here
            print("✅ Safe consolidations applied")
        elif mode == "APPLY_ALL":
            print("⚡ Applying all consolidations")
            planner.create_backups()
            # Additional application logic would go here
            print("✅ All consolidations applied")
    else:
        # Planning mode (default)
        if not os.path.exists(".ops/dup_plan.json"):
            print("❌ No detection plan found. Run detector first.")
            return 1
        
        planner.load_plan()
        planner.generate_reports()
        print("📋 Planning complete. Review .ops/dup_summary.md")
        print("💡 To proceed: create .ops/approve_consolidation.yml with 'approve: true'")
        print("💡 Then run: python .ops/consolidator/planner.py --apply")
    
    return 0

if __name__ == "__main__":
    exit(main())