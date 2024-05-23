#!/bin/bash

set -e

# Run tests
poetry run pytest -v -s

# Run linters
poetry run black common_core -l 79
poetry run flake8 common_core

# Update the version in pyproject.toml based on CHANGELOG.md
python update_version.py

# Build the project
poetry build
