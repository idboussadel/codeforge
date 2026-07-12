.DEFAULT_GOAL := help

PNPM := pnpm
API_DIR := apps/api
VENV := $(API_DIR)/venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help dev setup install install-js install-api api web build lint typecheck check-env

help: ## Show available commands
	@echo "CodeForge"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: install ## First-time setup (install deps + create .env)
	@test -f .env || cp .env.example .env
	@echo ""
	@echo "Setup complete. Add your keys to .env, then run:"
	@echo "  make dev"

install: install-js install-api ## Install all dependencies

install-js: ## Install Node deps (pnpm)
	$(PNPM) install

install-api: $(VENV)/bin/uvicorn ## Create Python venv + install API deps
$(VENV)/bin/uvicorn: $(API_DIR)/requirements.txt
	@test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install -q -r $(API_DIR)/requirements.txt
	@touch $(VENV)/bin/uvicorn

dev: check-env install-js ## Run web (:3000) + api (:8000)
	$(PNPM) dev

api: check-env ## Run API only (:8000)
	$(PNPM) dev:api

web: check-env install-js ## Run web only (:3000)
	$(PNPM) dev:web

build: check-env ## Build all apps
	$(PNPM) build

lint: ## Lint all apps
	$(PNPM) lint

typecheck: ## Typecheck all apps
	$(PNPM) typecheck

check-env:
	@test -f .env || (echo "Missing .env — run: make setup" && exit 1)
