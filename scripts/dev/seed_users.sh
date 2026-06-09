#!/bin/bash


# run like ./scripts/dev/seed_users.sh 10 20 
# first argument is the number of users to create, second argument is the starting index for user numbering
COUNT=${1:-10}
START=${2:-1}
PASSWORD="123456"

END=$((START + COUNT - 1))

echo "Creating $COUNT users from $START to $END..."

for ((i=START; i<=END; i++)); do
    EMAIL="test${i}@test${i}.com"
    USERNAME="test${i}"

    echo "Creating user: $EMAIL username: $USERNAME"

    uv run invenio users create "$EMAIL" \
        --password "$PASSWORD" \
        -c -a \
        -u "$USERNAME" \
        || echo "Skipping existing user: $EMAIL"
done

echo "Done!"