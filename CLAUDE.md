# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QELP (Quick ESXi Log Parser) is a Python tool that parses ESXi logs and produces CSV reports in a timeline format. It processes ESXi support bundles or log archives (zip, tar, gz, tgz) and extracts relevant security events from various log types.

## Development Commands

### Package Management (UV)
- `uv sync` - Install dependencies and sync the environment
- `uv sync --group dev` - Install with development dependencies
- `uv lock` - Update lockfile dependencies
- `uv run qelp <input_dir> <output_dir>` - Run the main application
- `uv add <package>` - Add new runtime dependency
- `uv add --group dev <package>` - Add development dependency
- `uv remove <package>` - Remove dependency

### Testing
- `uv run pytest` - Run all tests
- `uv run pytest tests/test_support.py` - Run specific test file
- `uv run pytest -v` - Run tests with verbose output

### Executable Building (PyInstaller)
- `uv run build-exe` - Build directory-based executable (faster startup)
- `uv run build-onefile` - Build single-file executable (portable)
- `uv run test-exe` - Test built executable functionality
- `uv run validate-build` - Comprehensive build validation and performance testing
- `uv run clean-build --all` - Clean all build artifacts and temporary files

### Development Dependencies
- `pytest` - Testing framework
- `pytest-mock` - Mock support for tests
- `pytest-watcher` - File watching for continuous testing
- `pyinstaller` - Create standalone executables
- `psutil` - System and process monitoring for build validation
- `toml` - Configuration file parsing

## Architecture Overview

### Core Components

1. **esxi_to_csv.py** - Main entry point and log pattern definitions
   - Contains `LOG_IDENTIFIERS` list defining patterns for different ESXi log types
   - `main()` function orchestrates the entire parsing process
   - Defines regex patterns for hostd, syslog, shell, auth, vmauthd, vmkernel, vobd, and rhttpproxy logs

2. **support.py** - Core processing classes
   - `ArchiveExtractor` - Handles extraction of various archive formats
   - `FileWrapper` - Provides unified interface for reading plain/gzipped files
   - `Parser` - Main parsing engine using pattern matching and threading
   - `Timeliner` - Creates chronological timeline of security events
   - `Configure` - CLI argument parsing and validation

3. **local_logger.py** - Simple logging configuration

### Key Data Structures

- `LogIdentifier` - namedtuple defining filename patterns and content patterns for each log type
- `ContentPattern` - namedtuple containing regex and access types
- `AccessType` - namedtuple defining access type names and description handlers
- `DescriptionHandler` - namedtuple controlling timeline inclusion and pattern matching

### Processing Flow

1. Extract archives using `ArchiveExtractor`
2. Identify log files by filename patterns
3. Parse logs using multithreaded pattern matching
4. Generate individual CSV files per log type
5. Create consolidated timeline CSV with chronologically sorted events

### Pattern Matching System

The tool uses a sophisticated pattern matching system that:
- Identifies log types by filename patterns
- Applies specific regex patterns to extract structured data
- Categorizes events by access types (Logon, User_activity, Remote_access, etc.)
- Determines timeline inclusion based on security relevance

## Testing Structure

Tests are organized in `tests/` directory:
- `test_support.py` - Unit tests for core classes
- Uses unittest framework with mock objects
- Tests archive extraction, file processing, and CSV generation

## Executable Distribution

QELP includes a complete PyInstaller-based build system for creating standalone executables.

### Build Modes

1. **Directory Build** (`uv run build-exe`)
   - Creates a directory with the executable and dependencies
   - Faster startup time (~0.05s)
   - Larger size (~23MB)
   - Best for local development and faster execution

2. **Single File Build** (`uv run build-onefile`)
   - Creates a single executable file
   - Slower startup time (~0.3s) due to extraction
   - Smaller size (~10MB)
   - Best for distribution and portability

### Cross-Platform Support

Executables are automatically named with version and platform information:
- Format: `qelp-v{version}-{platform}{extension}`
- Examples:
  - `qelp-v0.1.0-darwin-arm64` (macOS Apple Silicon)
  - `qelp-v0.1.0-linux-x64` (Linux x86_64)
  - `qelp-v0.1.0-windows-x64.exe` (Windows x86_64)

### Build Validation

The build system includes comprehensive validation:

```bash
# Build and validate in one command
uv run build-onefile && uv run validate-build

# Validation includes:
# - Functionality testing (help, argument validation, error handling)
# - Startup performance measurement (5-run average)
# - Memory usage monitoring
# - Size reporting and optimization recommendations
```

### Build Management

```bash
# Clean build artifacts
uv run clean-build --build     # Remove build/ and dist/
uv run clean-build --cache     # Remove Python cache files
uv run clean-build --temp      # Remove temporary files
uv run clean-build --all       # Remove everything
uv run clean-build --dry-run   # Preview what would be cleaned

# Show disk usage
uv run clean-build --usage
```

### Troubleshooting

1. **Build Fails**: Ensure `uv sync --group dev` has been run
2. **Missing Banner**: Art library is automatically included via hiddenimports
3. **Large Executable**: Use `--onedir` for smaller individual file sizes
4. **Slow Startup**: Use `--onedir` for faster startup times
5. **Permission Errors**: Run cleanup: `uv run clean-build --all`

## Configuration

- Entry point defined in `pyproject.toml` as `qelp = 'qelp.esxi_to_csv:main'`
- Dependencies managed through UV with locked versions
- Supports Python >= 3.8
- Uses `art` library for ASCII banner display
- Build scripts integrated as UV commands for seamless workflow