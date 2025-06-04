#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 KTH.
#
# KTH-RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
export DYLD_LIBRARY_PATH="/opt/homebrew/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
# Quit on errors
set -uo errexit

# Quit on unbound symbols
set -o nounset


echo "Creating Community administration-moderation role ..."
invenio roles create administration-moderation

echo "Creating Community administration role ..."
invenio roles create administration

echo "Allow Access ..."

echo "Allow administration-moderation to role administration-moderation ..."
invenio access allow administration-moderation role administration-moderation

echo "Allow administration-access to role administration ..."
invenio access allow administration-access role administration

echo "Allow superuser-access to role administration ..."
invenio access allow superuser-access role administration

echo "add test@test.com as administrator"

invenio roles add test@test.com administration
invenio roles add test@test.com administration-moderation

echo "create domains..."
invenio domains create organization
invenio domains create company
invenio domains create mailprovider
invenio domains create spammer

echo "done!"
