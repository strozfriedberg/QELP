#!/usr/bin/env python3
"""
Build cleanup management for QELP PyInstaller builds.
Removes build artifacts, temporary files, and provides selective cleanup options.
"""

import sys
import os
import logging
import argparse
import shutil
from pathlib import Path

# Configure logging  
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def clean_build_artifacts():
    """Clean PyInstaller build artifacts."""
    project_root = get_project_root()
    artifacts_cleaned = []
    
    # Standard PyInstaller artifacts
    artifacts = ["build", "dist"]
    
    for artifact in artifacts:
        artifact_path = project_root / artifact
        if artifact_path.exists():
            try:
                if artifact_path.is_dir():
                    shutil.rmtree(artifact_path)
                    size_info = "(directory)"
                else:
                    size = artifact_path.stat().st_size
                    artifact_path.unlink()
                    size_info = f"({size} bytes)"
                
                artifacts_cleaned.append(f"{artifact} {size_info}")
                logger.info(f"✓ Removed {artifact}")
            except Exception as e:
                logger.warning(f"Could not remove {artifact}: {e}")
    
    return artifacts_cleaned


def clean_python_cache():
    """Clean Python cache files and directories."""
    project_root = get_project_root()
    cache_cleaned = []
    
    # Find all __pycache__ directories
    for cache_dir in project_root.rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir)
            cache_cleaned.append(str(cache_dir.relative_to(project_root)))
            logger.info(f"✓ Removed {cache_dir.relative_to(project_root)}")
        except Exception as e:
            logger.warning(f"Could not remove {cache_dir}: {e}")
    
    # Find .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            cache_cleaned.append(str(pyc_file.relative_to(project_root)))
            logger.info(f"✓ Removed {pyc_file.relative_to(project_root)}")
        except Exception as e:
            logger.warning(f"Could not remove {pyc_file}: {e}")
    
    return cache_cleaned


def clean_temporary_files():
    """Clean temporary files and logs."""
    project_root = get_project_root()
    temp_cleaned = []
    
    # Log files
    for log_file in project_root.glob("*.log"):
        try:
            size = log_file.stat().st_size
            log_file.unlink()
            temp_cleaned.append(f"{log_file.name} ({size} bytes)")
            logger.info(f"✓ Removed {log_file.name}")
        except Exception as e:
            logger.warning(f"Could not remove {log_file.name}: {e}")
    
    # Temporary spec files that might be left behind
    for spec_file in project_root.glob("qelp_*.spec"):
        try:
            spec_file.unlink()
            temp_cleaned.append(spec_file.name)
            logger.info(f"✓ Removed {spec_file.name}")
        except Exception as e:
            logger.warning(f"Could not remove {spec_file.name}: {e}")
    
    return temp_cleaned


def clean_test_outputs():
    """Clean test output files."""
    project_root = get_project_root()
    test_cleaned = []
    
    # Test CSV files
    for test_file in project_root.glob("test_*.csv"):
        try:
            size = test_file.stat().st_size
            test_file.unlink()
            test_cleaned.append(f"{test_file.name} ({size} bytes)")
            logger.info(f"✓ Removed {test_file.name}")
        except Exception as e:
            logger.warning(f"Could not remove {test_file.name}: {e}")
    
    return test_cleaned


def show_disk_usage():
    """Show disk usage information for the project."""
    project_root = get_project_root()
    
    try:
        total_size = 0
        file_count = 0
        
        for item in project_root.rglob("*"):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    total_size += size
                    file_count += 1
                except (OSError, IOError):
                    pass
        
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.1f}{unit}"
                bytes_size /= 1024.0
            return f"{bytes_size:.1f}TB"
        
        logger.info(f"Project disk usage: {format_size(total_size)} ({file_count} files)")
        
        # Show dist directory size if it exists
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            dist_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
            logger.info(f"Dist directory: {format_size(dist_size)}")
        
    except Exception as e:
        logger.warning(f"Could not calculate disk usage: {e}")


def main():
    """Main cleanup entry point."""
    parser = argparse.ArgumentParser(description="Clean QELP build artifacts")
    parser.add_argument("--all", action="store_true",
                       help="Clean everything (build, cache, temp, test files)")
    parser.add_argument("--build", action="store_true", 
                       help="Clean build artifacts (build/, dist/)")
    parser.add_argument("--cache", action="store_true",
                       help="Clean Python cache files (__pycache__, *.pyc)")
    parser.add_argument("--temp", action="store_true",
                       help="Clean temporary files (*.log, temp specs)")
    parser.add_argument("--test", action="store_true",
                       help="Clean test output files (test_*.csv)")
    parser.add_argument("--usage", action="store_true",
                       help="Show disk usage information")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be cleaned without doing it")
    
    args = parser.parse_args()
    
    # Default to showing help if no args
    if not any(vars(args).values()):
        parser.print_help()
        return 0
    
    logger.info("QELP Build Cleanup Manager")
    logger.info("=" * 30)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be deleted")
        logger.info("")
    
    total_cleaned = []
    
    # Show usage first if requested
    if args.usage:
        show_disk_usage()
        logger.info("")
    
    # Clean based on options
    if args.all or args.build:
        logger.info("Cleaning build artifacts...")
        cleaned = clean_build_artifacts() if not args.dry_run else ["build/", "dist/"]
        total_cleaned.extend(cleaned)
        logger.info("")
    
    if args.all or args.cache:
        logger.info("Cleaning Python cache...")
        cleaned = clean_python_cache() if not args.dry_run else ["__pycache__/", "*.pyc"]
        total_cleaned.extend(cleaned)
        logger.info("")
    
    if args.all or args.temp:
        logger.info("Cleaning temporary files...")
        cleaned = clean_temporary_files() if not args.dry_run else ["*.log", "temp specs"]
        total_cleaned.extend(cleaned)
        logger.info("")
    
    if args.all or args.test:
        logger.info("Cleaning test outputs...")
        cleaned = clean_test_outputs() if not args.dry_run else ["test_*.csv"]
        total_cleaned.extend(cleaned)
        logger.info("")
    
    # Summary
    if total_cleaned:
        action = "Would clean" if args.dry_run else "Cleaned"
        logger.info(f"✅ {action} {len(total_cleaned)} item(s)")
        if args.dry_run:
            logger.info("Run without --dry-run to perform cleanup")
    else:
        logger.info("No files to clean")
    
    # Show final usage if requested
    if args.usage and not args.dry_run and total_cleaned:
        logger.info("")
        show_disk_usage()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())