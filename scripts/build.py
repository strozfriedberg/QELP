#!/usr/bin/env python3
"""
Build script for QELP using PyInstaller with UV environment integration.
Supports both onedir and onefile build modes with comprehensive error handling.
"""

import sys
import os
import logging
import argparse
import subprocess
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def setup_paths():
    """Setup and validate project paths."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src" / "qelp" / "esxi_to_csv.py"
    spec_onedir = project_root / "qelp.spec"
    spec_onefile = project_root / "qelp-onefile.spec"
    
    if not src_path.exists():
        logger.error(f"Source file not found: {src_path}")
        sys.exit(1)
        
    if not spec_onedir.exists():
        logger.error(f"Onedir spec file not found: {spec_onedir}")
        sys.exit(1)
        
    if not spec_onefile.exists():
        logger.error(f"Onefile spec file not found: {spec_onefile}")
        sys.exit(1)
    
    return project_root, src_path, spec_onedir, spec_onefile


def check_uv_environment():
    """Verify we're running in a UV environment with PyInstaller available."""
    try:
        import PyInstaller
        logger.info(f"PyInstaller found: version {PyInstaller.__version__}")
        return True
    except ImportError:
        logger.error("PyInstaller not found. Run 'uv sync --group dev' first.")
        return False


def clean_build_artifacts(project_root):
    """Clean up previous build artifacts."""
    logger.info("Cleaning previous build artifacts")
    
    artifacts = ["build", "dist", "__pycache__"]
    for artifact in artifacts:
        artifact_path = project_root / artifact
        if artifact_path.exists():
            try:
                if artifact_path.is_dir():
                    shutil.rmtree(artifact_path)
                else:
                    artifact_path.unlink()
                logger.info(f"✓ Removed {artifact}")
            except Exception as e:
                logger.warning(f"Could not remove {artifact}: {e}")


def run_pyinstaller(spec_path):
    """Run PyInstaller with error handling and progress reporting."""
    spec_name = spec_path.name
    build_type = "onefile" if "onefile" in spec_name else "onedir"
    logger.info(f"Building {build_type} executable using {spec_name}")
    
    cmd = ["pyinstaller", str(spec_path)]
    
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=spec_path.parent
        )
        
        if result.returncode != 0:
            logger.error("PyInstaller failed:")
            logger.error(result.stderr)
            return False
        
        logger.info("✓ Build completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"PyInstaller failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Build error: {e}")
        return False


def build_onedir(project_root, spec_onedir, spec_onefile):
    """Build onedir (directory) executable."""
    return run_pyinstaller(spec_onedir)


def build_onefile(project_root, spec_onedir, spec_onefile):
    """Build onefile (single executable) executable."""
    return run_pyinstaller(spec_onefile)


def main():
    """Main build script entry point."""
    parser = argparse.ArgumentParser(description="Build QELP executable")
    parser.add_argument("--onefile", action="store_true", 
                       help="Build single-file executable")
    parser.add_argument("--onedir", action="store_true", 
                       help="Build directory-based executable (default)")
    parser.add_argument("--clean", action="store_true",
                       help="Clean build artifacts before building")
    parser.add_argument("--help-build", action="store_true", 
                       help="Show detailed build help")
    
    args = parser.parse_args()
    
    if args.help_build:
        print("QELP Build System")
        print("================")
        print("Build modes:")
        print("  --onedir   Build directory-based executable (default, faster startup)")
        print("  --onefile  Build single-file executable (portable, slower startup)")
        print("")
        print("Options:")
        print("  --clean    Clean build artifacts before building")
        print("  --help     Show this help")
        print("")
        print("Examples:")
        print("  python scripts/build.py                # Build onedir executable")
        print("  python scripts/build.py --onefile      # Build onefile executable") 
        print("  python scripts/build.py --clean --onefile  # Clean then build onefile")
        return 0
    
    logger.info("QELP Build System")
    
    # Setup and validation
    project_root, src_path, spec_onedir, spec_onefile = setup_paths()
    if not check_uv_environment():
        sys.exit(1)
    
    # Clean if requested
    if args.clean:
        clean_build_artifacts(project_root)
    
    # Determine build mode
    if args.onefile and args.onedir:
        logger.error("Cannot specify both --onefile and --onedir")
        sys.exit(1)
    
    build_mode = "onefile" if args.onefile else "onedir"
    logger.info(f"Build mode: {build_mode}")
    
    # Build
    if build_mode == "onefile":
        success = build_onefile(project_root, spec_onedir, spec_onefile)
    else:
        success = build_onedir(project_root, spec_onedir, spec_onefile)
    
    if success:
        logger.info("🎉 Build completed successfully!")
        logger.info(f"Executable available in: {project_root / 'dist'}")
        return 0
    else:
        logger.error("❌ Build failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())