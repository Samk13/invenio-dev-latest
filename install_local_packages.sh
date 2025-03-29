#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 KTH.
#
# KTH-RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Quit on errors
set -uo errexit

# Quit on unbound symbols
set -o nounset


echo "Installing dev packages ..."


# Base directory for local packages
BASE_DIR="/Users/$USER/Documents/CODE/INVENIO"

# List of local packages to install
PACKAGES=(
  invenio-app-rdm
#   invenio-users-resources
#   invenio-communities
#   invenio-rdm-records
#   invenio-records-resources
#   invenio-accounts
)

echo "Installing dev packages ..."

# Build full path arguments
PACKAGE_PATHS=()
for package in "${PACKAGES[@]}"; do
  PACKAGE_PATHS+=("$BASE_DIR/$package")
done

# Install packages
invenio-cli packages install "${PACKAGE_PATHS[@]}"