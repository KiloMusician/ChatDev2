#!/usr/bin/env bash
# Preview import changes that would result from renames

set -e

if [ ! -f ".ops/import_rewrites.csv" ]; then
    echo "❌ No import rewrites found. Run planner first."
    exit 1
fi

echo "🔍 Previewing import changes..."
echo "================================"

while IFS=, read -r file from to confidence; do
    # Skip header row
    if [ "$file" = "file_path" ]; then continue; fi
    
    echo "📁 File: $file"
    echo "🔄 Rewrite: $from → $to (confidence: $confidence)"
    
    # Show current import lines
    if [ -f "$file" ]; then
        echo "📝 Current imports:"
        rg -n --color=always --hidden "$from" "$file" 2>/dev/null || echo "   (no matches found)"
    else
        echo "⚠️  File not found: $file"
    fi
    
    echo "─────────────────────────────────"
done < .ops/import_rewrites.csv

echo "✅ Preview complete"