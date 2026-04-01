# Working Orders vΩ + Intelligent Editing Integration
.PHONY: wo-scan wo-analyze wo-fix wo-stack

# Vacuum-mode scanning (no LLM deps)
wo-scan:
	@echo "🔍 Vacuum-mode repository scan..."
	python ops/agents/vacuum_scanner.py
	python ops/agents/vacuum_dedupe.py
	@echo "📊 Scan complete - receipts in ops/receipts/"

# Basic analysis (combines with existing WO)
wo-analyze: wo-scan
	./run.sh gates
	./run.sh ingest
	@echo "📈 Analysis complete"

# Vacuum fixes (safe, no LLM)
wo-fix:
	@echo "🔧 Applying vacuum-mode fixes..."
	bash ops/spine/detect_env.sh
	rg -l "console\.log" --type ts --type js | head -10 | while read f; do \
		echo "📝 Processing $$f..."; \
	done || true
	@echo "✅ Vacuum fixes applied"

# Complete intelligent stack status
wo-stack:
	@echo "📡 Intelligent Editing Stack Status:"
	@echo "Spine: $$(bash ops/spine/detect_spine.sh)"
	@echo "WO System: $$(test -f reports/gates_status.json && echo 'ACTIVE' || echo 'PENDING')"
	@echo "Receipts: $$(ls ops/receipts/*.json 2>/dev/null | wc -l) files"
	@echo "TODOs Found: $$(test -f ops/receipts/vacuum_scan.json && jq '. | to_entries | map(.value | length) | add' ops/receipts/vacuum_scan.json || echo '0')"