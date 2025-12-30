# HTTPS Setup Guide

Money Fest supports HTTPS for secure access with automatic certificate generation.

## Automatic Setup (Recommended)

The easiest way to enable HTTPS is to let Money Fest auto-generate certificates on first run.

### Step 1: Enable HTTPS

Create a `.env` file (or edit existing):

```bash
# .env
SECRET_KEY=your-secret-key-here
SSL_ENABLED=true
```

### Step 2: Start the Container

```bash
docker compose up -d
```

**That's it!** Money Fest will automatically:
- Generate a self-signed SSL certificate
- Save it to `data/certs/` (persistent storage)
- Start with HTTPS enabled

Certificates are generated once and reused on subsequent starts.

### Step 3: Access via HTTPS

Visit: **https://localhost:1111**

Your browser will show a security warning. Click "Advanced" → "Proceed to localhost" (exact wording varies by browser).

### Step 4: Trust the Certificate (Optional)

To remove browser warnings, install the certificate on your devices:

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain data/certs/cert.pem
```

**Linux:**
```bash
sudo cp data/certs/cert.pem /usr/local/share/ca-certificates/money-fest.crt
sudo update-ca-certificates
```

**Windows:**
1. Navigate to `data/certs/` folder
2. Double-click `cert.pem`
3. Click "Install Certificate"
4. Choose "Local Machine"
5. Select "Trusted Root Certification Authorities"
6. Click through to finish

**iOS/Android:**
1. Copy `data/certs/cert.pem` to your device (email, file sharing, etc.)
2. Open the certificate file
3. Follow prompts to install

## Manual Certificate Generation (Alternative)

If you prefer to generate certificates manually:

```bash
./generate-ssl-cert.sh
```

This creates certificates in the traditional `certs/` directory. To use these with the auto-generation setup, move them to `data/certs/`:

```bash
mkdir -p data/certs
mv certs/cert.pem data/certs/
mv certs/key.pem data/certs/
```

## Option 2: Reverse Proxy with Real Certificates

For internet-facing deployments or if you want real certificates, use a reverse proxy.

### Using Caddy (Simplest)

Create `Caddyfile`:

```
yourdomain.com {
    reverse_proxy categorizer:8080
}
```

Update `docker-compose.yml`:

```yaml
services:
  categorizer:
    # ... existing config ...
    # Remove ports section, use internal network only

  caddy:
    image: caddy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - categorizer

volumes:
  caddy_data:
  caddy_config:
```

Caddy automatically gets Let's Encrypt certificates!

### Using nginx

Create `nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /certs/cert.pem;
    ssl_certificate_key /certs/key.pem;

    location / {
        proxy_pass http://categorizer:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Switching Between HTTP and HTTPS

### To enable HTTPS:
```bash
# .env
SSL_ENABLED=true
```

```bash
docker compose restart
```

Access: **https://localhost:1111**

### To disable HTTPS:
```bash
# .env
SSL_ENABLED=false
```

```bash
docker compose restart
```

Access: **http://localhost:1111**

## Troubleshooting

### "SSL certificate not found" error

With auto-generation, this shouldn't happen. But if you see this error:

```bash
ls -la data/certs/
```

Should show:
- `cert.pem`
- `key.pem`

If missing and SSL_ENABLED=true, restart the container to trigger auto-generation:
```bash
docker compose restart
```

Check logs for certificate generation messages:
```bash
docker compose logs
```

### Browser still shows HTTP

1. Clear browser cache
2. Use `https://` explicitly in URL
3. Check `SSL_ENABLED=true` in .env
4. Restart container: `docker compose restart`

### Certificate expired

Self-signed certificates expire after 10 years. To regenerate:

```bash
rm -rf data/certs/
docker compose restart
```

The container will automatically generate a new certificate on startup.

### Can't access from mobile

1. Make sure mobile device is on same network
2. Use your computer's IP address: `https://192.168.1.X:1111`
3. Accept the security warning on mobile
4. For better experience, install the certificate on mobile (see Step 5 above)

## Security Notes

- **Self-signed certificates** are fine for home/local use but will show browser warnings
- **Let's Encrypt certificates** (via Caddy/nginx) are free and trusted by browsers
- Keep your `data/certs/key.pem` file secure - it's the private key
- Never commit certificates to Git (already in .gitignore)
- Auto-generated certificates are stored in `data/certs/` alongside your database
- Certificates are created once and persist across container restarts

## For Home Assistant Add-on

The Home Assistant add-on version automatically generates SSL certificates.

**To enable HTTPS in the add-on:**
1. Open add-on configuration in Home Assistant
2. Enable the "SSL Enabled" toggle
3. Save and restart the add-on

Certificates will be auto-generated and stored in `/data/certs/` (persistent add-on storage).

Access via: `https://[YOUR-HA-IP]:[PORT]`

**Note:** The add-on uses separate port access (not Ingress), so you'll access it directly via IP:PORT.
