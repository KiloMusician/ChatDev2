#!/usr/bin/env python3
"""
Automated Dependency Health Check
Runs on startup to ensure system integrity
"""

import sys

from dependency_manager import DependencyManager
from package_validator import PackageValidator


def health_check():
    """Quick health check for critical systems"""
    print("🏥 Running automated dependency health check...")
    
    validator = PackageValidator()
    validator.validate_critical_packages()
    
    # Check if system is functional
    if validator.missing_critical:
        print("❌ CRITICAL SYSTEM FAILURE")
        print("The following packages are broken and will prevent system operation:")
        for pkg in validator.missing_critical:
            print(f"   - {pkg}")
        print("\nChatDev, OpenAI, and LangChain integrations WILL FAIL")
        return False
    else:
        print("✅ All critical packages functional")
        print("System ready for ChatDev and AI operations")
        return True

def modernization_report():
    """Generate modernization recommendations"""
    manager = DependencyManager()
    report = manager.validate_all_dependencies()
    
    recommendations = []
    
    if report['summary']['broken'] > 0:
        recommendations.append(f"Fix {report['summary']['broken']} broken packages")
    
    if report['summary']['available'] >= 20:
        recommendations.append("Consider dependency consolidation")
    
    recommendations.append("Set up automated dependency monitoring")
    recommendations.append("Implement package conflict detection")
    
    return recommendations

if __name__ == "__main__":
    # Health check
    system_healthy = health_check()
    
    # Modernization recommendations
    print("\n🔧 Modernization Recommendations:")
    recommendations = modernization_report()
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    # Exit with appropriate code
    sys.exit(0 if system_healthy else 1)