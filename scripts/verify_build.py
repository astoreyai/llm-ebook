#!/usr/bin/env python3
"""
Build System Verification Script
Tests what components of the build system can be verified in the current environment.
"""

import sys
import subprocess
import os
from pathlib import Path


def check_command(cmd):
    """Check if a command is available."""
    try:
        subprocess.run([cmd, '--version'], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False


def verify_files_exist():
    """Verify all required source files exist."""
    print("=" * 70)
    print("FILE VERIFICATION")
    print("=" * 70)

    required_files = [
        'Makefile',
        'mkdocs.yml',
        'requirements.txt',
        'book/metadata.yaml',
        'book/book.bib',
        'book/ch01-foundations.md',
        'book/ch02-affective-prompting.md',
        'book/ch03-context-engineering.md',
    ]

    all_exist = True
    for file in required_files:
        exists = Path(file).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False

    return all_exist


def verify_labs():
    """Verify lab files."""
    print("\n" + "=" * 70)
    print("LAB VERIFICATION")
    print("=" * 70)

    lab_dirs = [
        'labs/ch01-foundations',
        'labs/ch02-affective-prompting',
        'labs/ch03-context-engineering'
    ]

    total_labs = 0
    for lab_dir in lab_dirs:
        if Path(lab_dir).exists():
            py_files = list(Path(lab_dir).glob('*.py'))
            print(f"  ✓ {lab_dir}: {len(py_files)} Python files")
            total_labs += len(py_files)
        else:
            print(f"  ✗ {lab_dir}: Not found")

    return total_labs


def verify_diagrams():
    """Verify SVG diagrams exist."""
    print("\n" + "=" * 70)
    print("DIAGRAM VERIFICATION")
    print("=" * 70)

    diagrams = [
        'figures/rag-pipeline.svg',
        'figures/raptor-tree.svg',
        'figures/position-effects.svg',
        'figures/cot-comparison.svg'
    ]

    all_exist = True
    for diagram in diagrams:
        exists = Path(diagram).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {diagram}")
        if not exists:
            all_exist = False

    return all_exist


def check_build_dependencies():
    """Check which build tools are available."""
    print("\n" + "=" * 70)
    print("BUILD DEPENDENCIES")
    print("=" * 70)

    dependencies = {
        'Python': 'python3',
        'Pandoc': 'pandoc',
        'XeLaTeX': 'xelatex',
        'Make': 'make'
    }

    available = {}
    for name, cmd in dependencies.items():
        is_available = check_command(cmd)
        status = "✓ Available" if is_available else "✗ Not available"
        print(f"  {status:20} {name}")
        available[name] = is_available

    return available


def test_python_imports():
    """Test if required Python packages can be imported."""
    print("\n" + "=" * 70)
    print("PYTHON PACKAGE VERIFICATION")
    print("=" * 70)

    packages = [
        'numpy',
        'scipy',
        # 'mkdocs',
        # 'pytest',
    ]

    available_count = 0
    for package in packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
            available_count += 1
        except ImportError:
            print(f"  ✗ {package} (not installed)")

    return available_count, len(packages)


def generate_build_report():
    """Generate comprehensive build verification report."""
    print("\n" + "=" * 70)
    print("BUILD VERIFICATION REPORT")
    print("=" * 70)

    files_ok = verify_files_exist()
    total_labs = verify_labs()
    diagrams_ok = verify_diagrams()
    build_deps = check_build_dependencies()
    pkg_available, pkg_total = test_python_imports()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"\n✓ Source Files: {'All present' if files_ok else 'Some missing'}")
    print(f"✓ Labs: {total_labs} Python files found")
    print(f"✓ Diagrams: {'All generated' if diagrams_ok else 'Some missing'}")
    print(f"✓ Python Packages: {pkg_available}/{pkg_total} available")

    print("\n" + "=" * 70)
    print("BUILD CAPABILITIES")
    print("=" * 70)

    if build_deps.get('Pandoc') and build_deps.get('XeLaTeX'):
        print("  ✓ Can build PDF (pandoc + XeLaTeX available)")
        print("  ✓ Can build EPUB (pandoc available)")
    else:
        print("  ✗ Cannot build PDF (pandoc or XeLaTeX missing)")
        print("  ✗ Cannot build EPUB (pandoc missing)")
        print("\n  To enable PDF/EPUB builds:")
        print("    Ubuntu/Debian: sudo apt-get install pandoc texlive-xetex")
        print("    macOS: brew install pandoc && brew install --cask mactex")

    if build_deps.get('Python'):
        print("  ✓ Can test labs (python3 available)")
    else:
        print("  ✗ Cannot test labs (python3 missing)")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)

    print("\n1. Install missing dependencies:")
    if not build_deps.get('Pandoc'):
        print("   - Install pandoc for PDF/EPUB generation")
    if not build_deps.get('XeLaTeX'):
        print("   - Install texlive-xetex for PDF generation")
    if pkg_available < pkg_total:
        print("   - Run: pip install -r requirements.txt")

    print("\n2. Test available builds:")
    if build_deps.get('Python'):
        print("   - Run labs: python3 labs/ch01-foundations/cot_vs_direct.py")
    if build_deps.get('Pandoc'):
        print("   - Build PDF: make pdf")
        print("   - Build EPUB: make epub")
    else:
        print("   - Builds require pandoc installation first")

    print("\n3. Verify outputs:")
    print("   - Check output/ directory for generated files")
    print("   - Review build logs for errors")

    print("\n" + "=" * 70)


def main():
    """Main verification routine."""
    print("\n" + "=" * 70)
    print("LLM PROMPT ENGINEERING BOOK - BUILD VERIFICATION")
    print("=" * 70)
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version.split()[0]}")

    generate_build_report()

    print("\n" + "=" * 70)
    print("Verification Complete")
    print("=" * 70)


if __name__ == '__main__':
    main()
