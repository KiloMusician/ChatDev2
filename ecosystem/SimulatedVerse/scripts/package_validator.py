#!/usr/bin/env python3
"""
Package Validation and Conflict Detection System
Prevents duplicate installations and validates package integrity
"""

import importlib
import subprocess
import sys
from typing import Any, Dict, List, Tuple


class PackageValidator:
    """Advanced package validation and conflict detection"""
    
    # Critical imports that must work for system functionality
    CRITICAL_PACKAGES = {
        'typing_extensions': 'typing_extensions',
        'fastapi': 'fastapi', 
        'openai': 'openai',
        'langchain': 'langchain',
        'numpy': 'numpy',
        'pandas': 'pandas'
    }
    
    def __init__(self):
        self.validation_results = {}
        self.conflicts = []
        self.missing_critical = []
    
    def test_import(self, package_name: str, import_name: str) -> Tuple[bool, str]:
        """Test if a package can be imported and return version info"""
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'unknown')
            return True, version
        except ImportError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def validate_critical_packages(self) -> Dict[str, dict]:
        """Validate all critical packages that system depends on"""
        print("🔍 Validating critical packages...")
        
        for pkg_name, import_name in self.CRITICAL_PACKAGES.items():
            success, info = self.test_import(pkg_name, import_name)
            
            self.validation_results[pkg_name] = {
                'importable': success,
                'version_or_error': info,
                'critical': True
            }
            
            if not success:
                self.missing_critical.append(pkg_name)
                print(f"❌ CRITICAL: {pkg_name} - {info}")
            else:
                print(f"✅ {pkg_name} v{info}")
        
        return self.validation_results
    
    def check_for_duplicates(self) -> List[str]:
        """Check for duplicate or conflicting package installations"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--format=freeze'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                packages = result.stdout.strip().split('\n')
                seen = set()
                duplicates = []
                
                for line in packages:
                    if '==' in line:
                        name = line.split('==')[0].lower()
                        if name in seen:
                            duplicates.append(name)
                        seen.add(name)
                
                return duplicates
            
        except Exception as e:
            print(f"⚠️ Error checking duplicates: {e}")
        
        return []
    
    def fix_critical_issues(self) -> List[str]:
        """Generate commands to fix critical package issues"""
        commands = []
        
        if self.missing_critical:
            commands.append("# CRITICAL PACKAGES MISSING - SYSTEM WILL NOT FUNCTION")
            for pkg in self.missing_critical:
                if pkg == 'typing_extensions':
                    commands.append("# typing_extensions is required for ChatDev and OpenAI")
                commands.append(f"# NEED: {pkg}")
        
        duplicates = self.check_for_duplicates()
        if duplicates:
            commands.append("# DUPLICATE PACKAGES DETECTED")
            for dup in duplicates:
                commands.append(f"# DUPLICATE: {dup}")
        
        return commands
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print("🚀 Running Full Package Validation")
        print("=" * 40)
        
        # Validate critical packages
        critical_results = self.validate_critical_packages()
        
        # Check for conflicts
        duplicates = self.check_for_duplicates()
        
        # Generate report
        report = {
            'critical_packages': critical_results,
            'missing_critical': self.missing_critical,
            'duplicates': duplicates,
            'system_functional': len(self.missing_critical) == 0,
            'needs_attention': len(self.missing_critical) > 0 or len(duplicates) > 0
        }
        
        print("\n📊 Validation Summary:")
        print(f"Critical packages: {len(critical_results)} tested")
        print(f"Missing critical: {len(self.missing_critical)}")
        print(f"Duplicates found: {len(duplicates)}")
        print(f"System functional: {report['system_functional']}")
        
        if report['needs_attention']:
            print("\n🔧 Issues found - running diagnostics:")
            fix_commands = self.fix_critical_issues()
            for cmd in fix_commands:
                print(cmd)
        
        return report

def main():
    validator = PackageValidator()
    return validator.run_full_validation()

if __name__ == "__main__":
    main()
