#!/usr/bin/with-contenv bashio
# ==============================================================================
# Money Fest Home Assistant Add-on
# Startup script - handles configuration and initialization
# ==============================================================================

set -e

# -----------------------------------------------------------------------------
# Configuration from HA options
# -----------------------------------------------------------------------------
bashio::log.info "Loading configuration from Home Assistant..."

PORT=$(bashio::config 'port')
SECRET_KEY=$(bashio::config 'secret_key')
SESSION_MAX_AGE=$(bashio::config 'session_max_age')
LOG_LEVEL=$(bashio::config 'log_level')
AUTO_IMPORT_CATEGORIES=$(bashio::config 'auto_import_categories')
SSL_ENABLED=$(bashio::config 'ssl_enabled')

# Validate secret key
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "null" ]; then
    bashio::log.fatal "═══════════════════════════════════════════════════════"
    bashio::log.fatal "Secret key is not configured!"
    bashio::log.fatal ""
    bashio::log.fatal "Please set a strong secret key in the add-on configuration."
    bashio::log.fatal ""
    bashio::log.fatal "Generate one with:"
    bashio::log.fatal "  python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    bashio::log.fatal "═══════════════════════════════════════════════════════"
    exit 1
fi

# Export environment variables for FastAPI
export SECRET_KEY="$SECRET_KEY"
export DATABASE_PATH="/data/categorizer.db"
export SESSION_MAX_AGE="$SESSION_MAX_AGE"
export SSL_ENABLED="$SSL_ENABLED"
export SSL_CERT="/data/certs/cert.pem"
export SSL_KEY="/data/certs/key.pem"

bashio::log.info "Configuration loaded successfully"
bashio::log.info "Port: $PORT"
bashio::log.info "Database: $DATABASE_PATH"
bashio::log.info "Session max age: $SESSION_MAX_AGE seconds"
bashio::log.info "SSL enabled: $SSL_ENABLED"

# -----------------------------------------------------------------------------
# Database Initialization
# -----------------------------------------------------------------------------
bashio::log.info "Checking database status..."

if [ ! -f "$DATABASE_PATH" ]; then
    bashio::log.info "Database not found, will be created on first run"
    FIRST_RUN=true
else
    bashio::log.info "Existing database found at $DATABASE_PATH"
    FIRST_RUN=false
fi

# -----------------------------------------------------------------------------
# Category Import (First Run)
# -----------------------------------------------------------------------------
if [ "$FIRST_RUN" = true ] && [ "$AUTO_IMPORT_CATEGORIES" = true ]; then
    bashio::log.info "First run detected, will import categories after startup..."

    # Note: Categories will be imported by the FastAPI app on startup
    # The init_db() function creates tables, and we can import categories after
fi

# -----------------------------------------------------------------------------
# SSL Certificate Auto-Generation
# -----------------------------------------------------------------------------
if [ "$SSL_ENABLED" = "true" ]; then
    bashio::log.info "SSL is enabled, checking for certificates..."

    # Create certs directory if it doesn't exist
    mkdir -p /data/certs

    # Check if certificates exist
    if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
        bashio::log.info "SSL certificates not found, generating self-signed certificate..."
        bashio::log.info "Certificate will be saved to /data/certs/ (persistent storage)"

        # Generate self-signed certificate (valid for 10 years)
        openssl req -x509 -newkey rsa:4096 -nodes \
            -keyout "$SSL_KEY" \
            -out "$SSL_CERT" \
            -days 3650 \
            -subj "/C=US/ST=State/L=City/O=Home/CN=homeassistant.local" \
            -addext "subjectAltName=DNS:homeassistant.local,DNS:*.local,DNS:localhost,IP:127.0.0.1" \
            2>/dev/null

        if [ $? -eq 0 ]; then
            bashio::log.info "✓ SSL certificate generated successfully!"
            bashio::log.info "  Certificate: $SSL_CERT"
            bashio::log.info "  Private key: $SSL_KEY"
            bashio::log.warning "═══════════════════════════════════════════════════════"
            bashio::log.warning "Self-signed certificate created!"
            bashio::log.warning ""
            bashio::log.warning "Your browser will show a security warning. This is normal"
            bashio::log.warning "for self-signed certificates used in home networks."
            bashio::log.warning ""
            bashio::log.warning "To remove the warning, install the certificate on your devices:"
            bashio::log.warning "  Certificate location: /data/certs/cert.pem"
            bashio::log.warning ""
            bashio::log.warning "Access via: https://[YOUR-HA-IP]:$PORT"
            bashio::log.warning "═══════════════════════════════════════════════════════"
        else
            bashio::log.error "Failed to generate SSL certificate"
            bashio::log.error "Falling back to HTTP mode"
            export SSL_ENABLED="false"
        fi
    else
        bashio::log.info "✓ Existing SSL certificates found"
        bashio::log.info "  Certificate: $SSL_CERT"
        bashio::log.info "  Private key: $SSL_KEY"
    fi
fi

# -----------------------------------------------------------------------------
# First-Time User Setup Instructions
# -----------------------------------------------------------------------------
if [ "$FIRST_RUN" = true ]; then
    # Determine URL scheme based on SSL setting
    if [ "$SSL_ENABLED" = "true" ]; then
        URL_SCHEME="https"
    else
        URL_SCHEME="http"
    fi

    bashio::log.warning "═══════════════════════════════════════════════════════"
    bashio::log.warning "First-time setup required!"
    bashio::log.warning ""
    bashio::log.warning "After the add-on starts, create your first user by visiting:"
    bashio::log.warning ""
    bashio::log.warning "  $URL_SCHEME://[YOUR-HA-IP]:$PORT/setup"
    bashio::log.warning ""
    bashio::log.warning "You can find your Home Assistant IP address in:"
    bashio::log.warning "  Settings → System → Network"
    bashio::log.warning ""
    bashio::log.warning "Or from a mobile device on the same network:"
    bashio::log.warning "  $URL_SCHEME://homeassistant.local:$PORT/setup"
    bashio::log.warning ""
    bashio::log.warning "After creating your first user, the /setup page will"
    bashio::log.warning "become inaccessible for security."
    bashio::log.warning ""
    bashio::log.warning "To create additional users later, use the web UI at:"
    bashio::log.warning "  $URL_SCHEME://[YOUR-HA-IP]:$PORT/static/users.html"
    bashio::log.warning "═══════════════════════════════════════════════════════"
fi

# -----------------------------------------------------------------------------
# Start Money Fest Application
# -----------------------------------------------------------------------------
bashio::log.info "Starting Money Fest..."

# Convert log level to uvicorn format
case "$LOG_LEVEL" in
    debug)
        UVICORN_LOG_LEVEL="debug"
        ;;
    info)
        UVICORN_LOG_LEVEL="info"
        ;;
    warning)
        UVICORN_LOG_LEVEL="warning"
        ;;
    error)
        UVICORN_LOG_LEVEL="error"
        ;;
    *)
        UVICORN_LOG_LEVEL="info"
        ;;
esac

bashio::log.info "Log level: $UVICORN_LOG_LEVEL"

# Import categories if first run and enabled
if [ "$FIRST_RUN" = true ] && [ "$AUTO_IMPORT_CATEGORIES" = true ]; then
    # Start uvicorn in background to initialize database
    bashio::log.info "Starting server briefly to initialize database..."
    uvicorn app.main:app --host 0.0.0.0 --port "$PORT" &
    UVICORN_PID=$!

    # Wait for server to start
    sleep 3

    # Import categories
    bashio::log.info "Importing categories..."
    python -m app.cli import-categories /app/categories.txt || {
        bashio::log.warning "Failed to auto-import categories"
        bashio::log.warning "You can manually import later if needed"
    }

    # Stop the background server
    kill $UVICORN_PID
    wait $UVICORN_PID 2>/dev/null || true

    bashio::log.info "Categories imported successfully"
fi

# Start uvicorn with appropriate settings
bashio::log.info "Money Fest is ready!"

if [ "$SSL_ENABLED" = "true" ]; then
    bashio::log.info "Access the web interface at https://[YOUR-HA-IP]:$PORT"

    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "$PORT" \
        --log-level "$UVICORN_LOG_LEVEL" \
        --ssl-keyfile "$SSL_KEY" \
        --ssl-certfile "$SSL_CERT" \
        --no-access-log
else
    bashio::log.info "Access the web interface at http://[YOUR-HA-IP]:$PORT"

    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "$PORT" \
        --log-level "$UVICORN_LOG_LEVEL" \
        --no-access-log
fi
