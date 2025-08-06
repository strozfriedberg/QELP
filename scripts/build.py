#!/usr/bin/env python3
"""
Build script for QELP using PyInstaller with UV environment integration.
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def setup_paths():
    """Setup and validate project paths."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src" / "qelp" / "esxi_to_csv.py"
    
    if not src_path.exists():
        logger.error(f"Source file not found: {src_path}")
        sys.exit(1)
    
    return project_root, src_path


def check_uv_environment():
    """Verify we're running in a UV environment with PyInstaller available."""
    try:
        import PyInstaller
        logger.info(f"PyInstaller found: version {PyInstaller.__version__}")
    except ImportError:
        logger.error("PyInstaller not found. Run 'uv sync --group dev' first.")
        sys.exit(1)


def main():
    """Main build script entry point."""
    parser = argparse.ArgumentParser(description="Build QELP executable")
    parser.add_argument("--help-build", action="store_true", 
                       help="Show available build commands")
    
    args = parser.parse_args()
    
    if args.help_build:
        print("QELP Build Commands:")
        print("  python scripts/build.py --help-build  Show this help")
        print("\nNext: PyInstaller spec generation and build modes will be added")
        return
    
    logger.info("QELP Build System - Foundation")
    
    project_root, src_path = setup_paths()
    check_uv_environment()
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Source file: {src_path}")
    logger.info("Build infrastructure ready")


if __name__ == "__main__":
    main()