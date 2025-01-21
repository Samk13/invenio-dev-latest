#!/usr/bin/env bash
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

echo "Creating .venv ..."
uv venv --prompt uv-env && source .venv/bin/activate

echo "install invenio-cli with uv ..."
uv pip install "git+https://github.com/utnapischtim/invenio-cli@WIP-merged-up-uv-ports-branches"

echo "installing invenio ..."
uv run invenio-cli install

echo "done!"
