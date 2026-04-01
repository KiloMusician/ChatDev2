#!/usr/bin/env python3
"""
CoreLink Foundation - Sophisticated Dependency Management System
Infrastructure-First Python Package Management for Replit Environment
"""

import importlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


@dataclass
class PackageInfo:
    name: str
    version: str
    required_version: Optional[str] = None
    installed: bool = False
    compatible: bool = True
    source: str = "unknown"

class DependencyManager:
    """Sophisticated dependency management for Replit environment"""
    
    # Official package list from project overview
    REPLIT_AVAILABLE_PACKAGES = {
        'beautifulsoup4': '4.12+',
        'colorama': '0.4+',
        'easydict': '1.10+', 
        'faiss-cpu': '1.7+',
        'fastapi': '0.104+',
        'flask': '3.0+',
        'gdtoolkit': '4.2+',
        'joblib': '1.3+',
        'langchain': '0.1+',
        'markdown': '3.5+',
        'numpy': '1.24+',
        'openai': '1.3+',
        'pandas': '2.0+',
        'pydantic': '2.5+',
        'python-osc': '1.8+',
        'pyyaml': '6.0+',
        'requests': '2.31+',
        'rich': '13.6+',
        'scikit-learn': '1.3+',
        'tenacity': '8.2+',
        'textual': '0.41+',
        'tiktoken': '0.5+',
        'typing-extensions': '4.8+',
        'uvicorn': '0.24+',
        'wcwidth': '0.2+'
    }
    
    def __init__(self):
        self.package_cache: Dict[str, PackageInfo] = {}
        self.missing_packages: Set[str] = set()
        self.conflicted_packages: Set[str] = set()
        
    def scan_installed_packages(self) -> Dict[str, PackageInfo]:
        """Scan all installed packages and return detailed info"""
        print("🔍 Scanning installed packages...")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--format=json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                installed = json.loads(result.stdout)
                for pkg in installed:
                    name = pkg['name'].lower().replace('_', '-')
                    self.package_cache[name] = PackageInfo(
                        name=name,
                        version=pkg['version'],
                        installed=True,
                        source="pip"
                    )
            else:
                print(f"⚠️ pip list failed: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Error scanning packages: {e}")
            
        return self.package_cache
    
    def validate_import(self, package_name: str) -> bool:
        """Test if a package can actually be imported"""
        import_name = package_name.replace('-', '_')
        
        # Handle special cases
        import_mapping = {
            'beautifulsoup4': 'bs4',
            'pyyaml': 'yaml', 
            'python-osc': 'pythonosc',
            'scikit-learn': 'sklearn',
            'typing-extensions': 'typing_extensions'
        }
        
        test_name = import_mapping.get(package_name, import_name)
        
        try:
            importlib.import_module(test_name)
            return True
        except ImportError:
            return False
    
    def check_package_status(self, package_name: str) -> PackageInfo:
        """Get comprehensive status of a single package"""
        if package_name in self.package_cache:
            pkg_info = self.package_cache[package_name]
        else:
            pkg_info = PackageInfo(
                name=package_name,
                version="unknown",
                installed=False
            )
        
        # Test if package is actually importable
        pkg_info.compatible = self.validate_import(package_name)
        
        # Check if it's in Replit's official list
        if package_name in self.REPLIT_AVAILABLE_PACKAGES:
            pkg_info.required_version = self.REPLIT_AVAILABLE_PACKAGES[package_name]
            pkg_info.source = "replit-official"
        
        return pkg_info
    
    def validate_all_dependencies(self) -> Dict[str, Any]:
        """Validate all required packages and return status report"""
        print("🔧 Validating all dependencies...")

        self.scan_installed_packages()
        summary: Dict[str, int] = {"available": 0, "missing": 0, "broken": 0}
        packages: Dict[str, Dict[str, Any]] = {}
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_required": len(self.REPLIT_AVAILABLE_PACKAGES),
            "packages": packages,
            "summary": summary,
        }

        for pkg_name in self.REPLIT_AVAILABLE_PACKAGES:
            status = self.check_package_status(pkg_name)

            if status.installed and status.compatible:
                summary["available"] += 1
                status_text = "✅ AVAILABLE"
            elif status.installed and not status.compatible:
                summary["broken"] += 1
                status_text = "❌ BROKEN"
                self.conflicted_packages.add(pkg_name)
            else:
                summary["missing"] += 1
                status_text = "⚠️ MISSING"
                self.missing_packages.add(pkg_name)

            packages[pkg_name] = {
                "version": status.version,
                "status": status_text,
                "importable": status.compatible,
                "source": status.source,
            }
            
            print(f"{status_text} {pkg_name} ({status.version})")
        
        return report
    
    def generate_install_commands(self) -> List[str]:
        """Generate commands to fix missing/broken packages"""
        commands = []
        
        if self.missing_packages:
            commands.append(f"# Install missing packages ({len(self.missing_packages)} found)")
            for pkg in sorted(self.missing_packages):
                commands.append(f"# Missing: {pkg}")
        
        if self.conflicted_packages:
            commands.append(f"# Fix broken packages ({len(self.conflicted_packages)} found)")
            for pkg in sorted(self.conflicted_packages):
                commands.append(f"# Broken: {pkg}")
        
        if not self.missing_packages and not self.conflicted_packages:
            commands.append("# ✅ All packages are properly installed and working!")
        
        return commands
    
    def export_dependency_report(self, filename: str = "dependency_report.json"):
        """Export comprehensive dependency report"""
        report = self.validate_all_dependencies()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Dependency report exported to {filename}")
        return report

def main():
    """Main dependency management interface"""
    print("🚀 CoreLink Foundation - Dependency Manager")
    print("=" * 50)
    
    manager = DependencyManager()
    report = manager.export_dependency_report()
    
    print("\n📋 Summary:")
    print(f"✅ Available: {report['summary']['available']}")
    print(f"⚠️ Missing: {report['summary']['missing']}")
    print(f"❌ Broken: {report['summary']['broken']}")
    
    if report['summary']['missing'] > 0 or report['summary']['broken'] > 0:
        print("\n🔧 Recommended Actions:")
        commands = manager.generate_install_commands()
        for cmd in commands:
            print(cmd)
    
    return report

if __name__ == "__main__":
    main()
