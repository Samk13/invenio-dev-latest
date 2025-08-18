#!/bin/bash
#
# Copyright (C) 2022-2024 KTH.

# ----------------------
# DO NOT USE IT IN PROD!
# ----------------------

# Exit on any error
# This option causes a pipeline (a sequence of commands separated by |) to return the exit status of the last command in the pipeline that failed.
# If all commands succeed, it returns the exit status of the last command. Without this option, a pipeline returns the exit status of the last command in the
# pipeline, even if one of the earlier commands fails.
set -euo pipefail

CONTAINER_NAME="worker"
# Find the container ID whose name starts with "CONTAINER_NAME"
container_id=$(docker ps --format "{{.ID}}\t{{.Names}}" | awk "/${CONTAINER_NAME}/ {print \$1}")

# Check if the container ID was found
if [ -z "$container_id" ]; then
    echo "Container name provided '${CONTAINER_NAME}' not found, please check the name and try again."
    exit 1
fi

# Execute scripts inside the container
echo "Start wipe_recreate script ..."
docker exec -it "$container_id" bash -c './wipe_recreate.sh'

# echo "Start roles_setup script ..."
# docker exec -it "$container_id" bash -c './scripts/roles_setup.sh'

# echo "Start vocabularies_import script ..."
# docker exec -it "$container_id" bash -c './scripts/vocabularies_import.sh'

echo "Done!"
