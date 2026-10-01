#!/usr/bin/env bash
# Generate self-signed RustFS development certificates without system trust changes.
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CERT_DIR="$PROJECT_ROOT/docker/certs"

mkdir -p "$CERT_DIR"
# Match cookiecutter-invenio-rdm/hooks/post_gen_project.sh, adding HTTPS hostnames.
openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$CERT_DIR/cert.pem" -keyout "$CERT_DIR/key.pem" -days 365 \
    -subj "/C=CH/ST=./L=./O=./OU=./CN=localhost/emailAddress=." \
    -addext "subjectAltName=DNS:localhost,DNS:s3,IP:127.0.0.1,IP:::1"
cp "$CERT_DIR/cert.pem" "$CERT_DIR/ca.pem"
# RustFS runs as a non-root container user and must be able to read the leaf key.
# These files are Git-ignored and for development only.
chmod 755 "$CERT_DIR"
chmod 644 "$CERT_DIR/cert.pem" "$CERT_DIR/key.pem" "$CERT_DIR/ca.pem"

echo "RustFS self-signed certificates generated in $CERT_DIR"
echo "No system trust or Keychain changes were made."
echo "Set AWS_CA_BUNDLE=./docker/certs/ca.pem in .env for the native app."
echo "The S3 setup script detects this certificate automatically."
echo "Accept the browser certificate warning at https://localhost:9000/health"
echo "RustFS console: https://localhost:9001/rustfs/console/auth/login/"
echo "Default login: CHANGE_ME / CHANGE_ME (unless overridden)."
echo "Accept the console certificate warning too if prompted."
echo "Nginx keeps its separate test.crt/test.key."
