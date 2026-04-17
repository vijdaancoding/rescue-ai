.PHONY: all help dev backend frontend agent test test-unit test-api test-service test-voice test-quick test-cov test-cov-html test-debug test-watch clean test-file test-marker test-slow test-ci install-test-deps

# Marker file to keep track of whether the models are downloaded
DOWNLOAD_MARKER = .models_downloaded

# Default command if you just type "make"
all: dev

help:
	@echo "Rescue AI - Makefile Commands"
	@echo "=============================="
	@echo "Development Commands:"
	@echo "  make dev                Run Backend, Frontend, and AI Agent concurrently"
	@echo "  make backend            Start only the FastAPI Backend"
	@echo "  make frontend           Start only the React/Vite Frontend"
	@echo "  make agent              Start only the LiveKit AI Agent"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make install-test-deps  Install testing dependencies"
	@echo "  make test               Run all tests"
	@echo "  make test-unit          Run only unit tests"
	@echo "  make test-api           Run only API endpoint tests"
	@echo "  make test-service       Run only service layer tests"
	@echo "  make test-voice         Run only voice agent tests"
	@echo "  make test-quick         Quick test run (less verbose)"
	@echo "  make test-cov           Run tests with coverage report (terminal)"
	@echo "  make test-cov-html      Run tests with HTML coverage report"
	@echo "  make test-debug         Run tests with detailed output"
	@echo "  make test-watch         Run tests in watch mode"
	@echo "  make clean              Remove test artifacts and cache files"
	@echo "=============================="

# ==========================================
# DEVELOPMENT ENVIRONMENT
# ==========================================

# 1. Start Backend
backend:
	@echo "=== Starting FastAPI Backend ==="
	. .venv/bin/activate && uv run uvicorn app.main:app --reload

# 2. Start Frontend
frontend:
	@echo "=== Starting Frontend ==="
	cd frontend && npm run dev

# 3. Agent File Downloader (Only runs if $(DOWNLOAD_MARKER) doesn't exist)
$(DOWNLOAD_MARKER):
	@echo "=== Downloading AI Agent files (First time only) ==="
	. .venv/bin/activate && python app/voice/agent.py download-files
	@touch $(DOWNLOAD_MARKER)
	@echo "=== Download complete! ==="

# 4. Start AI Agent (Depends on the download marker)
agent: $(DOWNLOAD_MARKER)
	@echo "=== Starting AI Agent ==="
	. .venv/bin/activate && python app/voice/agent.py start

# 5. Run all 3 concurrently
dev:
	@echo "Starting Backend, Frontend, and AI Agent simultaneously..."
	$(MAKE) -j3 backend frontend agent


# ==========================================
# TESTING ENVIRONMENT
# ==========================================

# Install testing dependencies
install-test-deps:
	uv sync --extra test

# Run all tests
test:
	uv run pytest tests/ -v --tb=short

# Run only unit tests
test-unit:
	uv run pytest tests/ -m unit -v --tb=short

# Run only API tests
test-api:
	uv run pytest tests/test_api/ -m api -v --tb=short

# Run only service tests
test-service:
	uv run pytest tests/test_services/ -m service -v --tb=short

# Run only voice tests
test-voice:
	uv run pytest tests/test_voice/ -m voice -v --tb=short

# Quick test run
test-quick:
	uv run pytest tests/ -q

# Run tests with coverage report (terminal output)
test-cov:
	uv run pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=70

# Generate HTML coverage report
test-cov-html:
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=70
	@echo ""
	@echo "Coverage report generated: htmlcov/index.html"
	@echo "Open in browser: open htmlcov/index.html"

# Run tests with detailed output
test-debug:
	uv run pytest tests/ -vv --tb=long --capture=no

# Run tests in watch mode (requires pytest-watch)
test-watch:
	uv run pytest-watch tests/ -- -v --tb=short

# Clean test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .eggs/
	rm -rf build/
	rm -rf dist/
	find . -type d -name __pycache__ -exec rm -r {} + || true
	find . -type f -name "*.pyc" -delete

# Run specific test file
test-file:
	@echo "Usage: make test-file FILE=tests/test_api/test_auth.py"
	@test -n "$(FILE)" || (echo "Please specify FILE variable" && exit 1)
	uv run pytest $(FILE) -v --tb=short

# Run test with specific marker
test-marker:
	@echo "Usage: make test-marker MARKER=api"
	@test -n "$(MARKER)" || (echo "Please specify MARKER variable (unit, api, service, voice)" && exit 1)
	uv run pytest tests/ -m $(MARKER) -v --tb=short

# Run tests and show slowest tests
test-slow:
	uv run pytest tests/ -v --durations=10

# CI/CD pipeline test run
test-ci:
	uv run pytest tests/ \
		--cov=app \
		--cov-report=xml \
		--cov-report=term-missing \
		--cov-fail-under=70 \
		-v \
		--tb=short \
		--junit-xml=test-results.xml