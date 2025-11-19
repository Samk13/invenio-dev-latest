#!/bin/bash

# Number of users to create (default: 10)
NUM_USERS=${1:-10}

echo "Creating $NUM_USERS users..."

# Create the first fixed user
echo "Creating first fixed user: test@test.com"
uv run invenio users create test@test.com --password 123456 -c -a -u test

# Create users 1..(NUM_USERS-1)
for ((i=1; i<NUM_USERS; i++)); do
    EMAIL="test$i@test$i.com"
    USERNAME="test$i"
    echo "Creating user: $EMAIL  username: $USERNAME"
    uv run invenio users create "$EMAIL" --password 123456 -c -a -u "$USERNAME"
done

echo "Done!"