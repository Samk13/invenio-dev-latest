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
# invenio-cli packages install ~/INVENIO/issues/invenio-app-rdm/ ~/INVENIO/issues/invenio-users-resources/ ~/INVENIO/issues/invenio-communities/ ~/INVENIO/issues/invenio-rdm-records/ ~/INVENIO/issues/invenio-records-resources/ ~/INVENIO/issues/invenio-accounts/ ~/INVENIO/issues/invenio-rdm-records/ ~/INVENIO/issues/invenio-users-resources/
invenio-cli packages install ~/INVENIO/issues/invenio-app-rdm
