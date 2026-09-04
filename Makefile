.PHONY: install test lint typecheck clean

install:
	pip install -e ".[dev]"

test:
	pytest --cov=holdem --cov-report=term-missing

lint:
	ruff check src tests
	ruff format --check src tests

typecheck:
	mypy

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.egg-info" -exec rm -rf {} +
