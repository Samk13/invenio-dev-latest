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
  invenio-app-rdm
  invenio-rdm-records
  invenio-drafts-resources
  invenio-records-resources
  # invenio-administration
  # invenio-accounts
  # invenio-banners
  # invenio-communities
  # invenio-users-resources
  # invenio-rdm-records
  # invenio-records-resources
# invenio-requests
# invenio-communities
# invenio-search-ui
)
# old invenio-rdm-records==10.9.2
# old invenio-communities==13.1.1


echo "Installing dev packages ..."

# Build full path arguments
PACKAGE_PATHS=()
for package in "${PACKAGES[@]}"; do
  PACKAGE_PATHS+=("$BASE_DIR/$package")
done
# Install packages
uv run invenio-cli packages install "${PACKAGE_PATHS[@]}"