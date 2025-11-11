# GitHub Actions Setup Guide

## Overview

This repository includes automated CI/CD workflows that:

1. **Build** PDF, EPUB, and web versions on every push
2. **Test** all lab code automatically
3. **Deploy** web version to GitHub Pages
4. **Create** releases with downloadable files when you tag a version
5. **Validate** content quality (no emojis, AI patterns, broken links)

## Prerequisites

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under "Build and deployment":
   - **Source**: GitHub Actions
   - This will allow the workflow to deploy automatically

### 2. Configure Repository Permissions

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions":
   - Select **Read and write permissions**
   - Check **Allow GitHub Actions to create and approve pull requests**
3. Click **Save**

## Workflows

### 1. Build and Publish (`build-and-publish.yml`)

**Triggers**:
- Push to `main` branch
- Push to any `claude/**` branch
- Push tags matching `v*.*.*` (e.g., `v1.0.0`)
- Manual trigger via GitHub UI

**What it does**:
- Installs pandoc and LaTeX dependencies
- Builds PDF, EPUB, and web versions
- Uploads artifacts for download
- Deploys web version to GitHub Pages (on main or tags)
- Creates GitHub Release with PDF/EPUB (on tags only)

**Artifacts available**:
- `book-pdf`: PDF version of the book
- `book-epub`: EPUB version for e-readers
- `book-web`: Static website files
- `test-results`: Lab test results

### 2. Quality Checks (`quality-check.yml`)

**Triggers**:
- Pull requests to `main`
- Push to `claude/**` branches

**What it does**:
- Checks for decorative emojis
- Validates markdown structure
- Detects AI language patterns
- Checks for TODO/STUB markers
- Validates bibliography format
- Runs code linting (flake8, black, isort)
- Validates internal links

## Usage

### Daily Development

Just commit and push normally:

```bash
git add .
git commit -m "feat: Add new content"
git push
```

The workflows will run automatically. Check the **Actions** tab to see progress.

### Creating a Release

When ready to publish a new version:

```bash
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will:
1. Build PDF, EPUB, and web versions
2. Create a GitHub Release with description
3. Attach PDF and EPUB files to the release
4. Deploy web version to GitHub Pages

### Manual Build

You can manually trigger builds from the GitHub UI:

1. Go to **Actions** tab
2. Select **Build and Publish Book** workflow
3. Click **Run workflow**
4. Choose branch and click **Run workflow**

## GitHub Pages URL

After the first successful deployment, your book will be available at:

```
https://<username>.github.io/<repository-name>/
```

For this repository:
```
https://astoreyai.github.io/llm-ebook/
```

## Monitoring Builds

### Check Build Status

1. Go to the **Actions** tab in your repository
2. Click on a workflow run to see details
3. Expand each job to see logs

### Download Artifacts

1. Go to a completed workflow run
2. Scroll to the **Artifacts** section
3. Click to download:
   - `book-pdf` - PDF version
   - `book-epub` - EPUB version
   - `book-web` - Website files

### View Releases

Published releases are available at:
```
https://github.com/astoreyai/llm-ebook/releases
```

## Troubleshooting

### Build Fails: "Permission denied"

**Solution**: Enable write permissions
1. Settings → Actions → General
2. Workflow permissions → Read and write permissions
3. Save

### Pages Deploy Fails: "Pages not enabled"

**Solution**: Enable GitHub Pages
1. Settings → Pages
2. Source → GitHub Actions
3. Save

### PDF Build Fails: "xelatex not found"

This shouldn't happen in GitHub Actions (dependencies are installed automatically), but if it does:
- Check the workflow log
- Verify `texlive-xetex` is in the install step

### Release Not Created on Tag

**Solution**: Ensure tag matches pattern
- Tags must match `v*.*.*` format
- Examples: `v1.0.0`, `v2.1.3`, `v1.0.0-beta`
- Not: `version-1.0`, `release-1`

## Customization

### Change Deployment Branch

Edit `.github/workflows/build-and-publish.yml`:

```yaml
on:
  push:
    branches:
      - main  # Change to your preferred branch
```

### Skip Quality Checks

Add to commit message:
```bash
git commit -m "docs: Update README [skip ci]"
```

### Modify Release Notes

Edit the `body:` section in the `create-release` job:

```yaml
- name: Create Release
  uses: softprops/action-gh-release@v2
  with:
    body: |
      Your custom release notes here
```

## Cost and Limits

- **GitHub Actions minutes**: Free tier includes 2,000 minutes/month for public repos
- **Artifact storage**: 500 MB free
- **GitHub Pages**: 100 GB bandwidth/month, 1 GB storage

Typical build uses:
- ~15-20 minutes per full build (PDF + EPUB + Web)
- ~50 MB artifact storage per build (cleaned after 30 days)

## Security

### Secrets

This workflow doesn't require secrets (all operations use GitHub's built-in `GITHUB_TOKEN`).

### Permissions

The workflow has minimal permissions:
- `contents: write` - To create releases
- `pages: write` - To deploy to GitHub Pages
- `id-token: write` - For GitHub Pages authentication

### Dependabot

Enable Dependabot to keep workflow dependencies updated:

1. Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Best Practices

### Branch Protection

Protect your `main` branch:
1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - Require pull request reviews
   - Require status checks to pass
   - Require branches to be up to date

### Version Numbering

Follow semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Minor update (new features)
- `v1.0.1` - Patch (bug fixes)
- `v2.0.0-beta.1` - Pre-release

### Release Cadence

Suggested schedule:
- **Main branch**: Deploy on every merge (continuous deployment)
- **Tagged releases**: Monthly or when significant features are ready
- **Hotfix releases**: As needed for critical issues

## Integration with Local Development

Your local build process (`make all`) is identical to CI:

```bash
# Local build
make install && make all

# CI build (same commands in workflow)
make pdf
make epub
make web
```

This ensures consistency between local and production builds.

## Next Steps

1. **Enable GitHub Pages**: Settings → Pages → Source: GitHub Actions
2. **Push to main**: `git push origin main`
3. **Check Actions tab**: Verify build succeeds
4. **Create first release**: `git tag v1.0.0 && git push origin v1.0.0`
5. **Share the book**: Send people to your GitHub Pages URL!

## Support

- **GitHub Actions Docs**: https://docs.github.com/actions
- **GitHub Pages Docs**: https://docs.github.com/pages
- **Book Issues**: https://github.com/astoreyai/llm-ebook/issues
