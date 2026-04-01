#!/usr/bin/env bash
# Content duplicate scanner using file hashes

set -e
mkdir -p .ops

echo "🔍 Scanning for content duplicates..."

# Get all source files and compute hashes
if command -v fd >/dev/null 2>&1; then
    fd -t f -e ts -e tsx -e js -e jsx -e py -e gd -e md | xargs -I{} sh -c 'sha256sum "{}"' > .ops/hashes.txt
else
    find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.gd" -o -name "*.md" \) \
        ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./dist/*" \
        -exec sha256sum {} \; > .ops/hashes.txt
fi

# Find duplicate hashes
sort .ops/hashes.txt | uniq -d -w 64 > .ops/exact_duplicates.txt

dup_count=$(wc -l < .ops/exact_duplicates.txt)
echo "📊 Found $dup_count exact content duplicates"

if [ $dup_count -gt 0 ]; then
    echo "🔍 Exact duplicates found:"
    cat .ops/exact_duplicates.txt
fi

echo "📁 Full hash list saved to .ops/hashes.txt"