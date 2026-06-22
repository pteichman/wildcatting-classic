test:
	uv run python -m unittest discover -s test

check:
	uv run ruff check wildcatting test
	uv run mypy wildcatting test
	uv run vulture wildcatting test vulture/allowlist.py

fmt:
	uv run ruff format wildcatting test
	uv run ruff check --fix wildcatting test

.PHONY: test check fmt
