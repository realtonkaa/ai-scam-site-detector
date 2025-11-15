.PHONY: install test lint run clean help

help:
	@echo "AI Scam Site Detector - Makefile targets"
	@echo ""
	@echo "  install   Install dependencies"
	@echo "  test      Run all tests"
	@echo "  lint      Run code linting"
	@echo "  run       Run CLI (requires URL= argument)"
	@echo "  app       Launch Streamlit web interface"
	@echo "  clean     Remove cache and build artifacts"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v --tb=short

test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	python -m flake8 src/ tests/ --max-line-length=100 --ignore=E501,W503

run:
	python -m src.cli $(URL)

app:
	streamlit run app/app.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/ *.egg-info/
