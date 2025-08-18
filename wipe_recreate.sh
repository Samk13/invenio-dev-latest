#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
# Copyright (C) 2022-2024 KTH.
#
# Demo-InvenioRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


# ----------------------
# DO NOT USE IT IN PROD!
# ----------------------


# Quit on errors
set -uo errexit

# Quit on unbound symbols
set -o nounset

# Prompt to confirm action
# read -r -p "Are you sure you want to wipe everything and create a new empty instance? [y/N] " response
# if [[ ! ("$response" =~ ^([yY][eE][sS]|[yY])$) ]]
# then
#     exit 0
# fi


# Wipe
# ----

invenio shell --no-term-title -c "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"
# NOTE: db destroy is not needed since DB keeps being created
#       Just need to drop all tables from it.
invenio db drop --yes-i-know
invenio index destroy --force --yes-i-know
invenio index queue init purge

# Recreate
# --------
# NOTE: db init is not needed since DB keeps being created
#       Just need to create all tables from it.
echo "Create DB ..."
invenio db create
echo "Set default file location ..."
invenio files location create 'default-location' 's3://default' --default

invenio roles create admin
invenio access allow superuser-access role admin
echo "Initate indecies ..."
invenio index init --force
echo "Initate custom fields ..."
invenio rdm-records custom-fields init
echo "Initate communities custom fields ..."
invenio communities custom-fields init
echo "Declare the MQ queues required for statistics ..."
invenio queues declare

echo "Initate fixtures ..."
invenio rdm-records fixtures
echo "Creating rdm fixtures ..."
invenio rdm fixtures

# Static page create
echo "Initate static pages ..."
invenio rdm pages create --force

echo "Initiate domains ..."
invenio domains create organization
invenio domains create company
invenio domains create mailprovider
invenio domains create spammer

echo "End of wipe_recreate.sh script."


# Enable admin user
# echo "activate admin user ..."
# invenio users activate admin@inveniosoftware.org
