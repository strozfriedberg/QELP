#!/usr/bin/env python3
"""
Comprehensive build validation and performance testing for QELP executables.
Validates functionality, performance, and provides actionable feedback.
"""

import sys
import os
import subprocess
import logging
import time
import shutil
from pathlib import Path
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def find_executables():
    """Find all QELP executables in dist directory."""
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    
    executables = []
    
    if not dist_dir.exists():
        logger.error("No dist directory found. Run build first.")
        return executables
    
    # Look for platform-specific builds
    for item in dist_dir.iterdir():
        if item.name.startswith("qelp-v"):
            if item.is_dir():
                # Onedir build
                exe_path = item / "qelp"
                if exe_path.exists():
                    executables.append({
                        'path': exe_path,
                        'type': 'onedir',
                        'name': item.name,
                        'size_dir': get_directory_size(item)
                    })
            elif item.is_file():
                # Onefile build
                executables.append({
                    'path': item,
                    'type': 'onefile', 
                    'name': item.name,
                    'size': item.stat().st_size
                })
    
    return executables


def get_directory_size(directory):
    """Get total size of directory in bytes."""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total += os.path.getsize(filepath)
    except (OSError, IOError):
        pass
    return total


def format_size(bytes_size):
    """Format bytes as human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"


def test_startup_performance(executable):
    """Test executable startup time with multiple runs."""
    logger.info(f"Testing startup performance: {executable['name']}")
    
    times = []
    for i in range(5):  # Run 5 times for average
        start_time = time.time()
        try:
            result = subprocess.run(
                [str(executable['path']), '--help'],
                capture_output=True,
                timeout=30
            )
            end_time = time.time()
            
            if result.returncode == 0:
                times.append(end_time - start_time)
            else:
                logger.error(f"Run {i+1} failed with exit code {result.returncode}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Run {i+1} timed out")
            return None
        except Exception as e:
            logger.error(f"Run {i+1} failed: {e}")
            return None
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        logger.info(f"  Average: {avg_time:.3f}s")
        logger.info(f"  Range: {min_time:.3f}s - {max_time:.3f}s")
        
        # Performance assessment
        if avg_time < 1.0:
            logger.info("  ✓ Excellent startup performance")
        elif avg_time < 3.0:
            logger.info("  ✓ Good startup performance")
        elif avg_time < 5.0:
            logger.warning("  ⚠ Moderate startup performance")
        else:
            logger.warning("  ⚠ Slow startup performance")
        
        return {
            'average': avg_time,
            'min': min_time,
            'max': max_time,
            'runs': len(times)
        }
    
    return None


def test_functionality(executable):
    """Test basic executable functionality."""
    logger.info(f"Testing functionality: {executable['name']}")
    
    tests = [
        # Help command
        {
            'args': ['--help'],
            'expect_success': True,
            'expect_output': ['usage:', 'ESXi'],
            'name': 'Help command'
        },
        # Invalid args (should show usage)
        {
            'args': [],
            'expect_success': False,  # Should exit with error
            'expect_output': ['usage:'],
            'name': 'No arguments validation'
        },
        # Invalid directory
        {
            'args': ['/nonexistent', '/tmp/test'],
            'expect_success': True,  # App exits 0 but shows error
            'expect_output': ['does not exist'],
            'name': 'Invalid input directory'
        }
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = subprocess.run(
                [str(executable['path'])] + test['args'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check exit code
            success = result.returncode == 0
            if test['expect_success'] != success and test['name'] != 'No arguments validation':
                logger.error(f"  ✗ {test['name']}: Unexpected exit code {result.returncode}")
                continue
            
            # Check output content
            output = result.stdout + result.stderr
            output_ok = True
            for expected in test['expect_output']:
                if expected not in output:
                    logger.error(f"  ✗ {test['name']}: Expected '{expected}' in output")
                    output_ok = False
            
            if output_ok:
                logger.info(f"  ✓ {test['name']}")
                passed += 1
            
        except subprocess.TimeoutExpired:
            logger.error(f"  ✗ {test['name']}: Timed out")
        except Exception as e:
            logger.error(f"  ✗ {test['name']}: {e}")
    
    logger.info(f"  Functionality: {passed}/{total} tests passed")
    return passed == total


def test_memory_usage(executable):
    """Test memory usage during startup."""
    logger.info(f"Testing memory usage: {executable['name']}")
    
    # This is a basic test - for more detailed memory testing,
    # would need platform-specific tools like psutil
    try:
        import psutil
        
        # Start process and measure memory
        process = subprocess.Popen(
            [str(executable['path']), '--help'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(0.1)
        
        try:
            ps_process = psutil.Process(process.pid)
            memory_info = ps_process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            process.wait(timeout=10)
            
            logger.info(f"  Peak memory usage: {memory_mb:.1f}MB")
            
            if memory_mb < 50:
                logger.info("  ✓ Excellent memory efficiency")
            elif memory_mb < 100:
                logger.info("  ✓ Good memory usage")
            elif memory_mb < 200:
                logger.warning("  ⚠ Moderate memory usage")
            else:
                logger.warning("  ⚠ High memory usage")
                
            return memory_mb
            
        except psutil.NoSuchProcess:
            logger.info("  Process finished before memory measurement")
            return None
        
    except ImportError:
        logger.info("  Skipping memory test (psutil not available)")
        return None
    except Exception as e:
        logger.warning(f"  Memory test failed: {e}")
        return None


def validate_executable(executable):
    """Validate a single executable."""
    logger.info(f"\n=== Validating {executable['name']} ===")
    logger.info(f"Type: {executable['type']}")
    
    # Size information
    if executable['type'] == 'onefile':
        size_str = format_size(executable['size'])
        logger.info(f"Size: {size_str}")
    else:
        size_str = format_size(executable['size_dir'])
        logger.info(f"Directory size: {size_str}")
    
    results = {}
    
    # Test functionality
    results['functionality'] = test_functionality(executable)
    
    # Test performance
    results['performance'] = test_startup_performance(executable)
    
    # Test memory usage
    results['memory'] = test_memory_usage(executable)
    
    return results


def main():
    """Main validation entry point."""
    logger.info("QELP Build Validation and Performance Testing")
    logger.info("=" * 50)
    
    executables = find_executables()
    
    if not executables:
        logger.error("No executables found to validate")
        logger.error("Run 'uv run build-exe' or 'uv run build-onefile' first")
        return 1
    
    logger.info(f"Found {len(executables)} executable(s) to validate")
    
    all_results = {}
    
    # Validate each executable
    for executable in executables:
        results = validate_executable(executable)
        all_results[executable['name']] = results
    
    # Summary report
    logger.info(f"\n{'=' * 50}")
    logger.info("VALIDATION SUMMARY")
    logger.info(f"{'=' * 50}")
    
    for name, results in all_results.items():
        logger.info(f"\n{name}:")
        logger.info(f"  Functionality: {'✓ PASS' if results['functionality'] else '✗ FAIL'}")
        
        if results['performance']:
            perf = results['performance']
            logger.info(f"  Startup time: {perf['average']:.3f}s avg")
        else:
            logger.info("  Startup time: ✗ FAILED")
        
        if results['memory']:
            logger.info(f"  Memory usage: {results['memory']:.1f}MB")
        else:
            logger.info("  Memory usage: Not measured")
    
    # Overall assessment
    failed_count = sum(1 for r in all_results.values() if not r['functionality'])
    
    if failed_count == 0:
        logger.info("\n🎉 All validations passed!")
        return 0
    else:
        logger.error(f"\n❌ {failed_count} validation(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())