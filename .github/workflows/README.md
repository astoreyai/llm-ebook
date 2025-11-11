# GitHub Actions Workflows

This directory contains automated CI/CD workflows for building and publishing the book.

## Workflows

### 1. Build and Publish (`build-and-publish.yml`)

**Purpose**: Automated book building and publishing

**Triggers**:
- Push to `main` branch
- Push to `claude/**` branches
- Version tags (`v*.*.*`)
- Manual workflow dispatch

**Jobs**:

1. **build** - Builds all book formats
   - Installs pandoc, LaTeX, Python dependencies
   - Builds PDF, EPUB, and web versions
   - Uploads artifacts (PDF, EPUB, Web)
   - Prepares for GitHub Pages deployment

2. **deploy-pages** - Deploys to GitHub Pages
   - Only runs on `main` or version tags
   - Deploys static website
   - Available at `https://astoreyai.github.io/llm-ebook/`

3. **create-release** - Creates GitHub Releases
   - Only runs on version tags
   - Attaches PDF and EPUB files
   - Generates release notes
   - Available at `/releases`

4. **test-labs** - Tests lab code
   - Runs pytest on all labs
   - Uploads test results
   - Continues on failure (non-blocking)

**Artifacts**:
- `book-pdf` - PDF version
- `book-epub` - EPUB version
- `book-web` - Website files
- `test-results` - Lab test results

**Build Time**: ~15-20 minutes

### 2. Quality Checks (`quality-check.yml`)

**Purpose**: Content and code quality validation

**Triggers**:
- Pull requests to `main`
- Push to `claude/**` branches

**Jobs**:

1. **content-quality** - Validates content
   - ✓ No decorative emojis
   - ✓ No AI language patterns
   - ✓ Valid markdown structure
   - ✓ No TODO/STUB markers
   - ✓ Bibliography exists

2. **code-quality** - Validates code
   - Runs flake8 (syntax errors)
   - Checks black formatting
   - Validates import sorting
   - All non-blocking (warnings only)

3. **link-validation** - Validates links
   - Checks internal chapter links
   - Verifies referenced files exist
   - Non-blocking

**Build Time**: ~5 minutes

## Usage Examples

### Daily Development

```bash
# Normal commit/push
git add .
git commit -m "feat: Add new content"
git push

# Workflows run automatically
# Check status at: https://github.com/astoreyai/llm-ebook/actions
```

### Creating a Release

```bash
# Tag and push
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Creates release at: https://github.com/astoreyai/llm-ebook/releases/tag/v1.0.0
# Deploys to: https://astoreyai.github.io/llm-ebook/
```

### Manual Trigger

1. Go to **Actions** tab
2. Select **Build and Publish Book**
3. Click **Run workflow**
4. Choose branch
5. Click **Run workflow** button

### Skip CI

Add `[skip ci]` to commit message:

```bash
git commit -m "docs: Update README [skip ci]"
```

## Workflow Status Badges

Add to README.md:

```markdown
![Build Status](https://github.com/astoreyai/llm-ebook/actions/workflows/build-and-publish.yml/badge.svg)
![Quality](https://github.com/astoreyai/llm-ebook/actions/workflows/quality-check.yml/badge.svg)
```

## Debugging

### View Logs

1. Go to **Actions** tab
2. Click on a workflow run
3. Click on a job to see details
4. Expand steps to see logs

### Common Issues

**Permission Denied**:
- Settings → Actions → General
- Workflow permissions → Read and write
- Save

**Pages Deploy Fails**:
- Settings → Pages
- Source → GitHub Actions
- Save

**Build Timeout**:
- Default timeout: 60 minutes
- Usually completes in 15-20 minutes
- Check for hanging processes in logs

### Download Artifacts

1. Go to completed workflow run
2. Scroll to **Artifacts** section
3. Click artifact name to download

Artifacts expire after 30 days.

## Customization

### Change Pandoc Options

Edit `build-and-publish.yml`:

```yaml
- name: Build PDF
  run: |
    pandoc book/ch*.md \
      --pdf-engine=xelatex \
      # Add your custom options here
      -o output/book.pdf
```

### Add Custom Checks

Edit `quality-check.yml`:

```yaml
- name: Your Custom Check
  run: |
    # Your validation script
```

### Modify Release Notes

Edit the `create-release` job body:

```yaml
body: |
  ## Your Custom Release Notes
  Version ${{ steps.version.outputs.VERSION }}

  Your custom content here
```

## Dependencies

### System Packages

Installed in workflow:
- `pandoc` - Document converter
- `texlive-xetex` - LaTeX engine
- `texlive-fonts-recommended` - Fonts
- `texlive-fonts-extra` - Additional fonts
- `texlive-latex-extra` - LaTeX packages
- `lmodern` - Latin Modern fonts

### Python Packages

From `requirements.txt`:
- `mkdocs` + `mkdocs-material` - Website
- `pytest` - Testing
- `numpy`, `scipy` - Statistical tests
- `openai`, `anthropic` - LLM APIs
- 40+ additional packages

### GitHub Actions

- `actions/checkout@v4` - Checkout code
- `actions/setup-python@v5` - Setup Python
- `actions/upload-artifact@v4` - Upload artifacts
- `actions/upload-pages-artifact@v3` - Upload for Pages
- `actions/deploy-pages@v4` - Deploy to Pages
- `softprops/action-gh-release@v2` - Create releases

## Cost and Limits

**Free Tier (Public Repository)**:
- 2,000 Actions minutes/month
- 500 MB artifact storage
- 100 GB Pages bandwidth/month

**Typical Usage**:
- ~15-20 minutes per full build
- ~50 MB artifacts per build
- ~15 MB Pages site

**Estimated Monthly Cost**: $0 (within free tier)

## Security

### Permissions

Workflows use minimal required permissions:
- `contents: write` - Create releases
- `pages: write` - Deploy Pages
- `id-token: write` - Pages authentication

### Secrets

No secrets required. Uses built-in `GITHUB_TOKEN`.

### Dependabot

Keep actions updated:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Monitoring

### Email Notifications

GitHub sends emails on:
- Workflow failures
- First failure after success

Configure: Settings → Notifications

### Status Checks

Require in branch protection:
- `build / Build Book (PDF, EPUB, Web)`
- `content-quality / Content Quality Validation`

Settings → Branches → Branch protection rules

## Support

- **GitHub Actions Docs**: https://docs.github.com/actions
- **Workflow Syntax**: https://docs.github.com/actions/reference/workflow-syntax-for-github-actions
- **Issues**: https://github.com/astoreyai/llm-ebook/issues
