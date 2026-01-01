# Development Setup

## Directory Structure

This repository contains both the Home Assistant add-on and a standalone Docker setup for development:

```
money_fest/
├── money_fest/              # Home Assistant add-on (source of truth)
│   ├── app/                # Application code
│   ├── Dockerfile          # Add-on Dockerfile
│   ├── config.yaml         # Add-on configuration
│   └── CHANGELOG.md        # Version history
├── Dockerfile              # Standalone development Dockerfile
├── docker-compose.yml      # Development environment
└── start.sh                # Startup script
```

## Single Source of Truth

**All application code lives in `money_fest/app/`**. This is the canonical source used for both:
- Home Assistant add-on builds
- Development environment (mounted as volumes)

## Development Workflow

### Quick Start

```bash
# Start development environment
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Fast Development Iteration

The development setup uses **volume mounts** instead of copying files into the container. This means:

✅ **No rebuild needed** - Changes to Python code, HTML, CSS, JS are immediately reflected
✅ **Fast iteration** - Edit → Save → Refresh browser
✅ **Single source** - Edit files in `money_fest/app/` only

### What Requires Rebuild

Only these changes require `docker compose down && docker compose build && docker compose up -d`:

- Requirements changes (`requirements.txt`)
- Dockerfile changes
- System dependencies

### Making Changes

1. Edit files in `money_fest/app/` (e.g., `money_fest/app/static/categorize.html`)
2. For Python code changes, restart the container: `docker compose restart`
3. For HTML/CSS/JS changes, just refresh your browser

### Testing Add-on Build

To test that your changes work in the add-on environment:

```bash
cd money_fest
docker build -t money-fest-addon .
```

## Port Mapping

- Development: http://localhost:1111
- Container internal port: 8080

## Environment Variables

See `.env.example` for available configuration options. Create `.env` in the root directory:

```bash
cp .env.example .env
# Edit .env with your settings
```

## Database

Development database is stored in `./data/categorizer.db` and persisted between container restarts.

## Common Tasks

### Create a user
```bash
docker exec categorizer python -m app.cli create-user alice --password password123
```

### Import categories
```bash
docker exec categorizer python -m app.cli import-categories /app/categories.txt
```

### Reset database
```bash
rm -rf data/categorizer.db
docker compose restart
```
