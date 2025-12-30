#!/bin/bash
# Start script for Money Fest
# Supports both HTTP and HTTPS modes

set -e

# Default values
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8080}
SSL_ENABLED=${SSL_ENABLED:-false}
SSL_CERT=${SSL_CERT:-/app/data/certs/cert.pem}
SSL_KEY=${SSL_KEY:-/app/data/certs/key.pem}

echo "Starting Money Fest..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "SSL Enabled: $SSL_ENABLED"

if [ "$SSL_ENABLED" = "true" ]; then
    # Create certs directory if it doesn't exist
    mkdir -p /app/data/certs

    # Check if SSL files exist
    if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
        echo "SSL enabled but certificates not found. Generating self-signed certificate..."
        echo "Certificate will be saved to /app/data/certs/ (persistent storage)"
        echo ""

        # Generate self-signed certificate (valid for 10 years)
        openssl req -x509 -newkey rsa:4096 -nodes \
            -keyout "$SSL_KEY" \
            -out "$SSL_CERT" \
            -days 3650 \
            -subj "/C=US/ST=State/L=City/O=Home/CN=localhost" \
            -addext "subjectAltName=DNS:localhost,DNS:*.local,IP:127.0.0.1" \
            2>/dev/null

        if [ $? -eq 0 ]; then
            echo "✓ SSL certificate generated successfully!"
            echo "  Certificate: $SSL_CERT"
            echo "  Private key: $SSL_KEY"
            echo ""
            echo "NOTE: Your browser will show a security warning for self-signed certificates."
            echo "This is normal for local development. See HTTPS-SETUP.md for details."
            echo ""
        else
            echo "ERROR: Failed to generate SSL certificate"
            echo "Generate certificates manually with: ./generate-ssl-cert.sh"
            exit 1
        fi
    else
        echo "✓ Using existing SSL certificates"
        echo "  Certificate: $SSL_CERT"
        echo "  Private key: $SSL_KEY"
    fi

    echo ""
    echo "Starting with HTTPS..."

    # Start uvicorn with SSL
    exec uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --ssl-keyfile "$SSL_KEY" \
        --ssl-certfile "$SSL_CERT"
else
    echo ""
    echo "Starting with HTTP (no SSL)..."
    echo "To enable HTTPS, set SSL_ENABLED=true in .env and restart"

    # Start uvicorn without SSL
    exec uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT"
fi
