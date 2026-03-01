.PHONY: dev test test-backend test-frontend test-e2e lint build clean

dev:
	docker compose up --build

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && pnpm dev

test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && pnpm test

test-e2e:
	cd frontend && pnpm playwright test

lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check app tests
	cd backend && uv run ruff format --check app tests
	cd backend && uv run mypy app

lint-frontend:
	cd frontend && pnpm lint
	cd frontend && pnpm typecheck

format:
	cd backend && uv run ruff format app tests
	cd backend && uv run ruff check --fix app tests
	cd frontend && pnpm format

build:
	docker compose build

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

install:
	cd backend && uv sync
	cd frontend && pnpm install

setup: install
	cp -n .env.example .env.local 2>/dev/null || true
	@echo "Setup complete. Edit .env.local then run: make dev"
