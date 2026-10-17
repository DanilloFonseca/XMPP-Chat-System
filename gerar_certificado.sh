#!/usr/bin/env bash

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)/ejabberd"
DOMINIO="localhost"

openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout "$DIR/server.key" -out "$DIR/server.crt" \
  -subj "/CN=$DOMINIO/O=IMD0907/C=BR" \
  -addext "subjectAltName=DNS:$DOMINIO,IP:127.0.0.1"

cat "$DIR/server.crt" "$DIR/server.key" > "$DIR/server.pem"
rm -f "$DIR/server.key"

chmod 644 "$DIR/server.pem"

echo "Certificado gerado em $DIR/server.pem"
openssl x509 -in "$DIR/server.crt" -noout -subject -fingerprint -sha256
