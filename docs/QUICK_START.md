# Quick Start Guide

## For Readers

### Option 1: Read Online (Easiest)

Visit the book website:
```
https://astoreyai.github.io/llm-ebook/
```

### Option 2: Download PDF/EPUB

1. Go to [Releases](https://github.com/astoreyai/llm-ebook/releases)
2. Download the latest version:
   - `prompt-engineering-book.pdf` - For printing and offline reading
   - `prompt-engineering-book.epub` - For e-readers (Kindle, Apple Books, etc.)

### Option 3: Build Locally

```bash
# Clone the repository
git clone https://github.com/astoreyai/llm-ebook.git
cd llm-ebook

# Install dependencies (requires pandoc and LaTeX)
make install

# Build all formats
make all

# Outputs:
# - output/prompt-engineering-book.pdf
# - output/prompt-engineering-book.epub
# - site/index.html (open in browser)
```

## For Contributors

### Initial Setup

```bash
# Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/llm-ebook.git
cd llm-ebook

# Install dependencies
make install
source .venv/bin/activate

# Install pre-commit hook (optional)
ln -s ../../hooks/pre-commit .git/hooks/pre-commit
chmod +x hooks/pre-commit
```

### Making Changes

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes to book/*.md or labs/

# Test your changes
make web        # Build and preview website
make labs       # Run lab tests

# Commit with descriptive message
git add .
git commit -m "feat: Add new section on X"

# Push and create pull request
git push origin feature/your-feature-name
```

### Content Guidelines

1. **No decorative emojis** - Use text instead (pre-commit hook will check)
2. **Cite sources** - Add to `book/book.bib` in BibTeX format
3. **Test code** - All lab code must run and have tests
4. **PhD-level writing** - Technical, precise, evidence-based
5. **Security-first** - Integrate OWASP considerations

### Running Quality Checks

```bash
# Check for emojis
grep -r "🎉\|✅\|❌" --include="*.md" book/ labs/

# Validate markdown structure
make validate

# Run tests
make test

# Build locally to verify
make all
```

## For Maintainers

### Creating a Release

```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag (triggers GitHub Actions)
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Build PDF, EPUB, and web versions
2. Create a GitHub Release
3. Attach PDF and EPUB files
4. Deploy to GitHub Pages

### Monitoring

- **Actions**: Check build status at `https://github.com/astoreyai/llm-ebook/actions`
- **Pages**: View deployed site at `https://astoreyai.github.io/llm-ebook/`
- **Releases**: Manage at `https://github.com/astoreyai/llm-ebook/releases`

### Troubleshooting

**Build fails in CI but works locally?**
- Check Python version (CI uses 3.11)
- Check pandoc version (CI uses latest from apt)
- Review workflow logs in Actions tab

**Pages not deploying?**
- Verify Settings → Pages → Source is "GitHub Actions"
- Check workflow permissions are "Read and write"

**Release not created?**
- Ensure tag matches `v*.*.*` format
- Check workflow permissions include `contents: write`

## Directory Structure

```
llm-ebook/
├── .github/workflows/       # CI/CD automation
│   ├── build-and-publish.yml
│   └── quality-check.yml
├── book/                    # Book chapters
│   ├── ch01-foundations.md
│   ├── ch02-affective-prompting.md
│   ├── ...
│   ├── book.bib            # Bibliography
│   └── metadata.yaml       # Book metadata
├── labs/                    # Runnable code examples
│   ├── ch01-foundations/
│   ├── ch02-affective-prompting/
│   └── ...
├── docs/                    # Documentation
│   ├── GITHUB_ACTIONS_SETUP.md
│   └── QUICK_START.md
├── hooks/                   # Git hooks
│   └── pre-commit          # Quality validation
├── output/                  # Build artifacts (gitignored)
├── site/                    # Web build (gitignored)
├── Makefile                # Build automation
├── requirements.txt        # Python dependencies
└── README.md              # Project overview
```

## Make Targets

```bash
make install    # Install Python dependencies
make pdf        # Build PDF
make epub       # Build EPUB
make web        # Build website
make all        # Build all formats
make labs       # Run lab tests
make test       # Run all tests
make clean      # Remove build artifacts
make serve      # Serve website locally (http://localhost:8000)
```

## CI/CD Pipeline

### On Every Push

- Build PDF, EPUB, and web versions
- Run quality checks (no emojis, AI patterns, etc.)
- Test all lab code
- Upload artifacts

### On Main Branch

- Deploy website to GitHub Pages
- Make artifacts available for download

### On Version Tag (`v*.*.*`)

- Create GitHub Release
- Attach PDF and EPUB files
- Deploy to GitHub Pages
- Generate release notes

## Support

- **Issues**: https://github.com/astoreyai/llm-ebook/issues
- **Discussions**: https://github.com/astoreyai/llm-ebook/discussions
- **Documentation**: See `docs/` directory

## License

CC BY-NC-SA 4.0 - Free for educational and non-commercial use.

See [LICENSE](../LICENSE) for full terms.
