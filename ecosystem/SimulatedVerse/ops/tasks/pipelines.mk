.PHONY: scan fix format lint semgrep comby agent vacuum

scan:
	rg -n "TODO|FIXME|XXX|HACK" || true
	semgrep --config ops/linters/semgrep_rules.yml || true

format:
	black . || true
	ruff check --fix || true
	isort . || true
	prettier -w . || true
	gdformat . || true

lint:
	eslint . --ext .ts,.tsx,.js,.jsx --fix || true
	mypy || true
	bandit -r . || true
	gdlint . || true

semgrep:
	semgrep --config ops/linters/semgrep_rules.yml --fix || true

comby:
	comby -config ops/linters/comby/console_to_logger.toml -d . -in-place || true

fix: format lint semgrep comby

agent:
	. ops/spine/detect_env.sh 2>/dev/null || true; aider --config ops/agents/aider.conf.yml

vacuum:
	python ops/agents/smolagents_recipe.py