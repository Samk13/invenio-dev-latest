#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 KTH.
#
# KTH-RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

set -euo pipefail

# ${VAR:+...} expands to nothing if VAR is unset/empty, or substitutes ... if VAR exists
# For Apple Silicon (M1/M2), /opt/homebrew/lib is the correct Homebrew library path
# --- Fix for Apple Silicon Homebrew paths ---
export DYLD_LIBRARY_PATH="/opt/homebrew/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"


echo "Installing dev packages ..."


# Base directory for local packages
BASE_DIR="$HOME/Documents/CODE/INVENIO"

# List of local packages to install
PACKAGES=(
  # invenio-accounts
  # invenio-administration
  invenio-app-rdm
  invenio-communities
  invenio-rdm-records
  # invenio-search-ui
  # invenio-requests
  # invenio-jobs
  # invenio-vocabularies
)


echo "Installing dev packages ..."

# Build full path arguments
PACKAGE_PATHS=()
for package in "${PACKAGES[@]}"; do
  PACKAGE_PATHS+=("$BASE_DIR/$package")
done

echo "Package paths: ${PACKAGE_PATHS[@]}"
# Install packages
uv run invenio-cli packages install "${PACKAGE_PATHS[@]}"

# echo "Packages installed successfully. don't forget to set --no-sync if you want to run invenio-cli run"
# echo "uv run --no-sync invenio-cli run"

# Build a list of "-e <path>" arguments for pip install
# PIP_EDITABLE_ARGS=()
# for path in "${PACKAGE_PATHS[@]}"; do
#   PIP_EDITABLE_ARGS+=("-e" "$path")
# done

# echo "run this if needed:"
# echo "uv pip install ${PIP_EDITABLE_ARGS[@]}"
# uv pip install "${PIP_EDITABLE_ARGS[@]}"
