.PHONY: help install test setup clean run venv

help:
	@echo "Available commands:"
	@echo "  venv       - Create virtual environment"
	@echo "  install    - Install Python dependencies (requires venv)"
	@echo "  test       - Run setup tests"
	@echo "  setup      - Full setup (create venv + install + test)"
	@echo "  run        - Run the pipeline"
	@echo "  clean      - Remove Python cache files and venv"

venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

install:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make venv' first."; exit 1; fi
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt

test:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make setup' first."; exit 1; fi
	venv/bin/python test_setup.py

setup:
	./setup.sh

run:
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make setup' first."; exit 1; fi
	venv/bin/python main.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf venv