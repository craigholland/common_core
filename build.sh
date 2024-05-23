#!/bin/bash

set -e

# Run tests
poetry run pytest -v -s

# Update the version in pyproject.toml based on CHANGELOG.md
python update_version.py

# Build the project
poetry build
