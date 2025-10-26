# Simple developer targets (Kilo Code CLI not required)
.PHONY: lint test build dev tui

lint:
	ruff check .

test:
	pytest -v

build: lint test
	@echo "✅ Build complete (lint + tests)"

dev:
	bash scripts/dev.sh

tui:
	python -m tui.app
