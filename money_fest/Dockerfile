# Use Home Assistant's build arguments for multi-arch support
ARG BUILD_FROM
ARG BUILD_VERSION
FROM ${BUILD_FROM}

# Set working directory
WORKDIR /app

# Install system dependencies needed for Python packages and SSL
# gcc: required for bcrypt compilation
# musl-dev: required for Alpine compatibility
# libffi-dev: required for cryptography packages
# openssl: required for SSL certificate generation
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY categories.txt .

# Create data directory with proper permissions
RUN mkdir -p /data && chmod 755 /data

# Copy and set up run script
COPY run.sh /
RUN chmod +x /run.sh

# Expose port (declarative, actual port from config.yaml)
EXPOSE 8080

# Labels required by Home Assistant
LABEL \
    io.hass.name="Money Fest" \
    io.hass.description="Collaborative bank transaction categorizer" \
    io.hass.arch="amd64|aarch64|armv7" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}"

# Run script handles initialization and starts the service
CMD ["/run.sh"]
