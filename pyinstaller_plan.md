# Detailed PyInstaller Integration Plan for QELP

## Git Workflow Overview
- Work on feature branch `feature/pyinstaller-integration` off current main branch
- Each commit represents a single logical step (<40 line diffs)
- Test after each commit, refactor if needed before proceeding
- Commit messages follow format: "action: brief description"
- User will provide sample data for acceptance testing (not committed)

## Detailed Implementation Steps

### Step 1: Branch Setup and Dependency Addition
**Branch:** Create `feature/pyinstaller-integration` 
**Files:** `pyproject.toml`
**Commit:** "deps: add pyinstaller to dev dependencies"
**Test:** `uv sync --group dev` succeeds, `uv run pyinstaller --version` works
**Lines:** ~3 lines (add pyinstaller>=6.0 to dev group)

### Step 2: Create Build Infrastructure Foundation
**Files:** `scripts/build.py` (new file)
**Commit:** "build: add core build script with UV integration"
**Content:** Clean, modular build script with error handling, logging, and UV environment setup
**Test:** Script runs without errors, shows help and available commands
**Lines:** ~30 lines
**Refactor Check:** Is the build script architecture extensible and well-organized?

### Step 3: Generate and Customize Spec File
**Files:** `qelp.spec` (new file)
**Commit:** "build: add optimized PyInstaller spec file"
**Action:** Generate spec, then customize for console app, optimize imports, handle art library
**Content:** Clean spec with proper console configuration, version info, icon handling
**Test:** Spec produces working executable that runs `--help` correctly
**Lines:** ~35 lines
**Refactor Check:** Is spec file well-organized with clear sections and comments?

### Step 4: Add Executable Testing Framework
**Files:** `scripts/test_executable.py` (new file)
**Commit:** "test: add executable validation framework"
**Content:** Framework to test executables without requiring committed sample data
**Test:** Framework validates basic executable functionality (help, version, argument parsing)
**Lines:** ~35 lines
**Refactor Check:** Is testing framework flexible enough for comprehensive validation?

### Step 5: Optimize Art Library and Dependencies
**Files:** `qelp.spec` (modify)
**Commit:** "build: optimize dependencies and art library handling"
**Action:** Fine-tune hiddenimports, exclude unnecessary modules, ensure art works correctly
**Test:** Executable displays banner, smaller file size, faster startup
**Lines:** ~15 lines modified
**Refactor Check:** Are dependency optimizations maintainable as project grows?

### Step 6: Add Build Mode Options and Error Handling
**Files:** `scripts/build.py` (modify)
**Commit:** "build: add onefile/onedir modes with robust error handling"
**Content:** Both build modes, comprehensive error handling, build cleanup, progress reporting
**Test:** Both modes produce working executables, errors are handled gracefully
**Lines:** ~25 lines added
**Refactor Check:** Is error handling comprehensive? Are build modes cleanly separated?

### Step 7: Create UV Integration and Shortcuts
**Files:** `pyproject.toml` (modify)
**Commit:** "build: add UV run shortcuts and tool configuration"
**Content:** Add project.scripts for build commands, proper tool configuration
**Test:** `uv run build-exe` and `uv run build-onefile` work reliably
**Lines:** ~10 lines
**Refactor Check:** Are UV integrations following best practices?

### Step 8: Add Cross-Platform and Version Support  
**Files:** `scripts/build.py` (modify), `qelp.spec` (modify)
**Commit:** "build: add cross-platform support and version embedding"
**Content:** Platform-specific naming, version extraction from pyproject.toml, proper output paths
**Test:** Executables have correct names and version info on current platform
**Lines:** ~20 lines total
**Refactor Check:** Is platform handling robust and version info accurate?

### Step 9: Add Build Validation and Performance Testing
**Files:** `scripts/validate_build.py` (new file)
**Commit:** "test: add comprehensive build validation"
**Content:** Performance comparison, functionality validation, size reporting, startup time testing
**Test:** Validation runs against user-provided sample data, reports meaningful metrics
**Lines:** ~40 lines
**Refactor Check:** Does validation provide actionable feedback on build quality?

### Step 10: Add Build Management and Documentation
**Files:** `scripts/clean_build.py` (new file), `CLAUDE.md` (modify)
**Commit:** "build: add build management and complete documentation"
**Content:** Build cleanup script, comprehensive docs with troubleshooting, distribution guide
**Test:** Documentation is accurate, cleanup script removes all build artifacts
**Lines:** ~30 lines total
**Refactor Check:** Is documentation complete and troubleshooting section helpful?

## Plan Improvements Made
1. **Better Architecture:** Build script designed for maintainability and extensibility
2. **Robust Testing:** Testing framework works with external sample data, no committed test files
3. **Performance Focus:** Validation includes performance metrics and size optimization
4. **Error Handling:** Comprehensive error handling throughout build process
5. **Version Management:** Automatic version embedding from pyproject.toml
6. **Build Hygiene:** Dedicated cleanup tools and build artifact management
7. **Documentation Quality:** Comprehensive docs with troubleshooting guidance
8. **Reproducible Builds:** Clear process that produces consistent results
9. **User Experience:** Clear progress reporting and meaningful error messages
10. **Maintenance:** Modular design makes future updates easier

## Risk Mitigation
- Each commit tested against full test suite to prevent regression
- Build validation uses actual log processing workload for realistic testing
- Comprehensive error handling prevents build failures from unclear causes
- Modular design enables easy rollback of problematic changes
- Documentation includes troubleshooting for common issues

## Success Criteria
- Working executables for both onefile and onedir modes
- Executables match source performance and functionality 
- Clear, automated build process integrated with UV workflow
- Comprehensive validation ensures build quality
- Complete documentation enables independent use by other developers