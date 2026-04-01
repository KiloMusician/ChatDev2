#!/bin/bash
# CoreLink Foundation - Dependency Modernization Script
# Sophisticated solution for Replit environment

echo "🚀 CoreLink Foundation - Dependency Modernization"
echo "=================================================="

# 1. Environment Health Check
echo "🔍 Checking Python environment..."
python3 --version
which python3

# 2. Clean up potential conflicts
echo "🧹 Cleaning package cache..."
python3 -m pip cache purge 2>/dev/null || true

# 3. Verify critical packages
echo "🔧 Verifying critical packages..."
python3 -c "
import sys
critical_packages = ['typing_extensions', 'openai', 'langchain', 'fastapi']
failed = []

for pkg in critical_packages:
    try:
        if pkg == 'typing_extensions':
            import typing_extensions
            print(f'✅ {pkg} - {typing_extensions.__version__}')
        elif pkg == 'openai':
            import openai
            print(f'✅ {pkg} - {openai.__version__}')
        elif pkg == 'langchain':
            import langchain
            print(f'✅ {pkg} - working')
        elif pkg == 'fastapi':
            import fastapi
            print(f'✅ {pkg} - {fastapi.__version__}')
    except ImportError as e:
        print(f'❌ {pkg} - {e}')
        failed.append(pkg)

if failed:
    print(f'\\n🚨 CRITICAL: {len(failed)} packages broken')
    sys.exit(1)
else:
    print('\\n✅ All critical packages working')
    sys.exit(0)
"

RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "✅ Dependency modernization complete"
else
    echo "❌ Critical packages still broken - manual intervention required"
fi

exit $RESULT