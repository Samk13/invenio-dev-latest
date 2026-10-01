#!/usr/bin/env bash
# Renew the shared cookiecutter development certificate pair only when needed.
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CERT_DIR="$PROJECT_ROOT/docker/nginx"
CERT_FILE="$CERT_DIR/test.crt"
KEY_FILE="$CERT_DIR/test.key"

# Older cookiecutter certificates lack the SANs required for verified S3 HTTPS.
if test -s "$CERT_FILE" && test -s "$KEY_FILE" \
    && openssl x509 -in "$CERT_FILE" -checkend 0 -noout >/dev/null 2>&1 \
    && openssl x509 -in "$CERT_FILE" -noout -ext subjectAltName 2>/dev/null | grep -q 'DNS:localhost' \
    && openssl x509 -in "$CERT_FILE" -checkhost localhost -noout >/dev/null 2>&1 \
    && openssl x509 -in "$CERT_FILE" -checkhost s3 -noout >/dev/null 2>&1 \
    && openssl x509 -in "$CERT_FILE" -checkip 127.0.0.1 -noout >/dev/null 2>&1 \
    && openssl x509 -in "$CERT_FILE" -checkip ::1 -noout >/dev/null 2>&1; then
    echo "Reusing existing development certificates in $CERT_DIR"
else
    mkdir -p "$CERT_DIR"
    # Match cookiecutter-invenio-rdm/hooks/post_gen_project.sh, adding HTTPS hostnames.
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out "$CERT_FILE" -keyout "$KEY_FILE" -days 365 \
        -subj "/C=CH/ST=./L=./O=./OU=./CN=localhost/emailAddress=." \
        -addext "subjectAltName=DNS:localhost,DNS:s3,IP:127.0.0.1,IP:::1"
    echo "Development certificates generated in $CERT_DIR"
    echo "Restart RustFS and rebuild the Nginx image to use the updated certificate."
fi
# RustFS runs as a non-root container user. This shared key is for development only.
chmod 755 "$CERT_DIR"
chmod 644 "$CERT_FILE" "$KEY_FILE"

echo "No system trust or Keychain changes were made."
