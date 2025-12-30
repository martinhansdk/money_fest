#!/bin/bash
# Generate self-signed SSL certificate for Money Fest
# For production use, replace with a certificate from Let's Encrypt or your CA

set -e

CERT_DIR="./certs"
DAYS_VALID=3650  # 10 years

# Create certs directory if it doesn't exist
mkdir -p "$CERT_DIR"

echo "Generating self-signed SSL certificate..."
echo ""
echo "This certificate will be valid for $DAYS_VALID days (10 years)."
echo "Browsers will show a security warning because it's self-signed."
echo "This is normal for local/home use."
echo ""

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days $DAYS_VALID \
    -subj "/C=DK/ST=Region/L=City/O=Home/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.local,IP:127.0.0.1,IP:192.168.1.0/24"

echo ""
echo "✓ SSL certificate generated successfully!"
echo ""
echo "Certificate: $CERT_DIR/cert.pem"
echo "Private key: $CERT_DIR/key.pem"
echo ""
echo "To enable HTTPS:"
echo "1. Update docker-compose.yml to use SSL_ENABLED=true"
echo "2. Restart the container: docker compose restart"
echo ""
echo "To trust this certificate on your devices:"
echo "  - macOS: Import cert.pem to Keychain, set to 'Always Trust'"
echo "  - Windows: Import cert.pem to 'Trusted Root Certification Authorities'"
echo "  - Linux: Copy cert.pem to /usr/local/share/ca-certificates/ and run update-ca-certificates"
echo "  - iOS/Android: Email cert.pem to yourself and install it"
echo ""
