# Makefile for LLM Prompt Engineering Book
# Builds PDF, EPUB, and web versions

.PHONY: all clean pdf epub web labs test install help

# Default target
all: pdf epub web

# Help target
help:
	@echo "LLM Prompt Engineering Book - Build System"
	@echo ""
	@echo "Targets:"
	@echo "  make all      - Build all formats (PDF, EPUB, web)"
	@echo "  make pdf      - Build PDF version"
	@echo "  make epub     - Build EPUB version"
	@echo "  make web      - Build web version (MkDocs)"
	@echo "  make labs     - Test all lab code examples"
	@echo "  make test     - Run all tests"
	@echo "  make install  - Install dependencies"
	@echo "  make clean    - Remove build artifacts"

# Installation
install:
	@echo "Setting up Python virtual environment..."
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt
	@echo "Installation complete. Activate with: source .venv/bin/activate"

# PDF build using Pandoc
pdf: book/*.md book/book.bib
	@echo "Building PDF..."
	@mkdir -p output
	pandoc book/ch*.md \
		--from=markdown+smart \
		--to=pdf \
		--pdf-engine=xelatex \
		--bibliography=book/book.bib \
		--citeproc \
		--csl=ieee.csl \
		--number-sections \
		--toc \
		--toc-depth=3 \
		--metadata-file=book/metadata.yaml \
		--template=templates/book-template.tex \
		--resource-path=.:figures \
		-o output/prompt-engineering-book.pdf
	@echo "PDF created: output/prompt-engineering-book.pdf"

# EPUB build using Pandoc
epub: book/*.md book/book.bib
	@echo "Building EPUB..."
	@mkdir -p output
	pandoc book/ch*.md \
		--from=markdown+smart \
		--to=epub \
		--bibliography=book/book.bib \
		--citeproc \
		--csl=ieee.csl \
		--number-sections \
		--toc \
		--toc-depth=3 \
		--metadata-file=book/metadata.yaml \
		--resource-path=.:figures \
		--epub-cover-image=figures/cover.png \
		-o output/prompt-engineering-book.epub
	@echo "EPUB created: output/prompt-engineering-book.epub"

# Web build using MkDocs
web:
	@echo "Building web version..."
	. .venv/bin/activate && mkdocs build
	@echo "Web version created: site/index.html"

# Serve web version locally
serve:
	@echo "Starting local web server..."
	. .venv/bin/activate && mkdocs serve

# Test lab code examples
labs:
	@echo "Testing lab code examples..."
	. .venv/bin/activate && pytest labs/ -v --tb=short

# Run all tests
test:
	@echo "Running all tests..."
	. .venv/bin/activate && pytest tests/ -v --cov=labs --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# Linting and type checking
lint:
	@echo "Running linters..."
	. .venv/bin/activate && flake8 labs/ tests/
	. .venv/bin/activate && mypy labs/ tests/
	. .venv/bin/activate && black --check labs/ tests/

# Format code
format:
	@echo "Formatting code..."
	. .venv/bin/activate && black labs/ tests/

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf output/ site/ .pytest_cache/ htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete"

# Validate citations and links
validate:
	@echo "Validating citations and links..."
	. .venv/bin/activate && python scripts/validate_citations.py
	. .venv/bin/activate && python scripts/check_links.py

# Generate state checkpoint
checkpoint:
	@echo "Creating state checkpoint..."
	@mkdir -p STATE
	@python scripts/create_checkpoint.py
	@echo "Checkpoint created: STATE/state.json"
