FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for bcrypt)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from add-on directory (for production builds)
# In development, these are overridden by volume mounts in docker-compose.yml
COPY money_fest/app/ ./app/
COPY money_fest/categories.txt .
COPY start.sh .

# Make start script executable
RUN chmod +x /app/start.sh

# Create data directory
RUN mkdir -p /app/data && chmod 777 /app/data

# Expose port
EXPOSE 8080

# Run the application
CMD ["/app/start.sh"]
