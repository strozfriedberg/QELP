#!/usr/bin/env python3
"""
Executable validation framework for QELP PyInstaller builds.
Tests executables without requiring committed sample data.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path
import tempfile
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def find_executable():
    """Find the QELP executable in dist directory."""
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    
    if not dist_dir.exists():
        return None
    
    # Look for platform-specific builds first (new naming scheme)
    for item in dist_dir.iterdir():
        if item.name.startswith("qelp-v"):
            if item.is_dir():
                # Onedir build: look for qelp executable inside
                exe_path = item / "qelp"
                if exe_path.exists():
                    return exe_path
            elif item.is_file():
                # Onefile build
                return item
    
    # Fallback to legacy naming for backwards compatibility
    # Check for onedir build
    onedir_exe = dist_dir / "qelp" / "qelp"
    if onedir_exe.exists():
        return onedir_exe
    
    # Check for onefile build
    onefile_exe = dist_dir / "qelp"
    if onefile_exe.exists():
        return onefile_exe
    
    # Check for Windows executable
    win_exe = dist_dir / "qelp.exe"
    if win_exe.exists():
        return win_exe
    
    return None


def test_help_output(executable_path):
    """Test that executable shows help and banner correctly."""
    logger.info("Testing help output and banner display")
    
    try:
        result = subprocess.run(
            [str(executable_path), '--help'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Help command failed with exit code {result.returncode}")
            return False
        
        output = result.stdout
        
        # Check for banner (ESXi ASCII art)
        if "ESXi" not in output or "_____" not in output:
            logger.error("ASCII banner not found in help output")
            return False
        
        # Check for basic help text
        required_text = [
            "usage:",
            "input_dir",
            "output_dir",
            "ESXi Logs-to-CSV parses triage data"
        ]
        
        for text in required_text:
            if text not in output:
                logger.error(f"Required help text not found: '{text}'")
                return False
        
        logger.info("✓ Help output and banner test passed")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Help command timed out")
        return False
    except Exception as e:
        logger.error(f"Help test failed: {e}")
        return False


def test_argument_validation(executable_path):
    """Test argument validation without processing files."""
    logger.info("Testing argument validation")
    
    test_cases = [
        # No arguments - should show usage
        ([], 2, "usage:"),
        # Invalid input directory - app shows error but exits 0
        (["/nonexistent/input", "/tmp/output"], 0, "does not exist or is not a directory")
    ]
    
    for args, expected_code, expected_output in test_cases:
        try:
            result = subprocess.run(
                [str(executable_path)] + args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if expected_code and result.returncode != expected_code:
                logger.error(f"Args {args}: expected exit {expected_code}, got {result.returncode}")
                return False
            
            if expected_output and expected_output not in (result.stdout + result.stderr):
                logger.error(f"Args {args}: expected output '{expected_output}' not found")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Argument test timed out for args: {args}")
            return False
        except Exception as e:
            logger.error(f"Argument test failed for {args}: {e}")
            return False
    
    logger.info("✓ Argument validation test passed")
    return True


def test_startup_performance(executable_path):
    """Test executable startup time performance."""
    logger.info("Testing startup performance")
    
    import time
    
    # Test help command startup time (should be under 5 seconds)
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [str(executable_path), '--help'],
            capture_output=True,
            timeout=10
        )
        
        elapsed_time = time.time() - start_time
        
        if elapsed_time > 5.0:
            logger.warning(f"Startup time {elapsed_time:.2f}s may be slow")
        else:
            logger.info(f"✓ Startup time: {elapsed_time:.2f}s")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Startup performance test timed out")
        return False
    except Exception as e:
        logger.error(f"Startup performance test failed: {e}")
        return False


def main():
    """Run all executable validation tests."""
    logger.info("QELP Executable Validation Framework")
    
    executable_path = find_executable()
    if not executable_path:
        logger.error("No executable found in dist/ directory")
        logger.error("Run PyInstaller build first")
        sys.exit(1)
    
    logger.info(f"Testing executable: {executable_path}")
    
    # Run all tests
    tests = [
        ("Help Output & Banner", test_help_output),
        ("Argument Validation", test_argument_validation),
        ("Startup Performance", test_startup_performance),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        if test_func(executable_path):
            passed += 1
        else:
            logger.error(f"✗ {test_name} FAILED")
    
    # Summary
    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())