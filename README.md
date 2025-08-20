# Quick ESXI Log Parser (QELP)

QELP (Quick ESXi Log Parser) is a Python tool that parses ESXi logs in a quick and efficient fashion.
QELP requires ESXi support bundles or log archives as input and produces CSV reports in a timeline format.

Installation
=============

    Install uv: https://docs.astral.sh/uv/getting-started/installation/
    > git clone https://github.com/strozfriedberg/qelp.git
    > cd qelp
    > uv sync

    Qelp can also be downlaoded as a standalone binary from Releases section

Usage
================

    > uv run qelp <path\to\input_directory> <path\to\output_directory>

    If you prefer using compiled binary

    > qelp.exe <path\to\input_directory> <path\to\output_directory>

  Input directory must contain ESXi support or log archives having `zip`, `tar`, `gz`, or `tgz` extensions only.

Example
================
    > uv run qelp C:\ESXi_input_dir C:\ESXi_output_dir
QELP will search for ESXi log archives (having `zip`, `tar`, `gz`, or `tgz` extensions) in `C:\ESXi_input_dir` and will generate sub-directories (`<esxi_log_archive>_results`) in `C:\ESXi_output_dir`. Each result directory will contain extracted logs and CSV reports from the respective ESXi log archives.

For example, if `C:\ESXi_input_dir` contains an archive named `ESXi_test_log.tgz` then `C:\ESXi_output_dir\ESXi_test_log.tgz_results` will be generated containing extracted logs and CSV reports

Copyright
================
Copyright 2025, LevelBlue. QELP is licensed under the Apache License, Version 2.0.


