# Money Fest

A self-hosted web application for collaborative bank transaction categorization on mobile devices. Built for couples to jointly categorize their bank transactions in small batches using smartphones, with real-time synchronization.

## Features

**Phase 1 (Current):**
- ✅ User authentication with secure sessions
- ✅ Mobile-friendly login UI
- ✅ Database schema for transactions, categories, batches, and rules
- ✅ CLI tools for user management and setup
- ✅ 175 pre-defined expense categories

**Phase 2-8 (Upcoming):**
- Batch upload and management
- Transaction categorization UI
- Real-time WebSocket sync
- Rules engine for auto-suggestions
- Similar transaction matching
- Export to CSV for AceMoney

## Tech Stack

- **Backend:** Python 3.11+ with FastAPI
- **Database:** SQLite
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Deployment:** Docker & docker-compose

## Prerequisites

- Docker (20.10+)
- docker-compose (1.29+)

## Quick Start

### 1. Clone and Build

```bash
git clone <repository-url>
cd money_fest
docker-compose build
```

### 2. Start the Application

```bash
docker-compose up -d
```

The application will be available at `http://localhost:1111`

### 3. Initial Setup

#### Create Users

```bash
# Option 1: Using --password flag (simple but less secure)
docker exec categorizer python -m app.cli create-user martin --password yourpassword

# Option 2: Using interactive mode (most secure, requires -it flag)
docker exec -it categorizer python -m app.cli create-user martin
# Enter password when prompted

# Option 3: Using environment variable
docker exec -e USER_PASSWORD=yourpassword categorizer python -m app.cli create-user martin

# Create second user
docker exec categorizer python -m app.cli create-user wife --password yourpassword
```

#### Import Categories

```bash
docker exec categorizer python -m app.cli import-categories /app/categories.txt
```

This imports 175 pre-defined expense categories.

### 4. Access the Application

Open your browser to `http://localhost:1111` and login with one of the created users.

## CLI Commands

### create-user

Create a new user account.

```bash
# Interactive mode (most secure, requires -it flag)
docker exec -it categorizer python -m app.cli create-user <username>

# Non-interactive mode with --password flag
docker exec categorizer python -m app.cli create-user <username> --password <password>

# Using environment variable
docker exec -e USER_PASSWORD=<password> categorizer python -m app.cli create-user <username>
```

**Examples:**
```bash
# Interactive (will prompt for password)
docker exec -it categorizer python -m app.cli create-user martin

# Non-interactive with password argument
docker exec categorizer python -m app.cli create-user martin --password mypassword123

# Using environment variable
docker exec -e USER_PASSWORD=mypassword123 categorizer python -m app.cli create-user martin
```

Password must be at least 8 characters. **Note:** Using `--password` flag is less secure as it's visible in process lists.

### import-categories

Import categories from a file.

```bash
docker exec categorizer python -m app.cli import-categories [filepath]
```

**Default filepath:** `/app/categories.txt`

**Example:**
```bash
docker exec categorizer python -m app.cli import-categories
```

### backup

Create a backup of the database.

```bash
docker exec categorizer python -m app.cli backup [destination]
```

**Default destination:** `/app/data/`

**Example:**
```bash
docker exec categorizer python -m app.cli backup /app/data/
```

Backup files are named with timestamp: `categorizer_backup_YYYYMMDD_HHMMSS.db`

## Configuration

### Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```env
SECRET_KEY=your-secret-key-here
DATABASE_PATH=/app/data/categorizer.db
SESSION_MAX_AGE=2592000
```

**Generate a secure secret key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Docker Ports

Default port: `1111`

To change, edit `docker-compose.yml`:
```yaml
ports:
  - "1111:8080"  # Change first number to desired host port
```

## Development

### Running Tests

```bash
# Run all tests
docker exec categorizer pytest

# Run with coverage
docker exec categorizer pytest --cov=app --cov-report=html

# Run specific test file
docker exec categorizer pytest tests/test_auth.py

# Run specific test
docker exec categorizer pytest tests/test_auth.py::test_login_endpoint_success
```

### Project Structure

```
money_fest/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database schema
│   ├── models.py            # Pydantic models
│   ├── auth.py              # Authentication
│   ├── cli.py               # CLI commands
│   ├── routers/             # API endpoints
│   │   ├── auth.py
│   │   ├── batches.py       # Phase 2
│   │   ├── transactions.py  # Phase 2
│   │   ├── categories.py    # Phase 2
│   │   └── rules.py         # Phase 2
│   ├── services/            # Business logic
│   │   ├── user.py
│   │   ├── category.py
│   │   └── backup.py
│   └── static/              # Frontend
│       ├── index.html
│       └── css/
│           └── style.css
├── tests/                   # Test suite
├── data/                    # SQLite database (volume)
├── categories.txt           # Category definitions
├── sample.csv              # Example CSV format
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Database Schema

**Tables:**
- `users` - User accounts
- `categories` - Expense categories (175 items)
- `batches` - Transaction batches (Phase 2)
- `transactions` - Individual transactions (Phase 2)
- `rules` - Auto-categorization rules (Phase 2)

## Backup & Restore

### Create Backup

```bash
docker exec categorizer python -m app.cli backup /app/data/
```

### Restore from Backup

1. Stop the container:
   ```bash
   docker-compose down
   ```

2. Replace the database file:
   ```bash
   cp data/categorizer_backup_YYYYMMDD_HHMMSS.db data/categorizer.db
   ```

3. Start the container:
   ```bash
   docker-compose up -d
   ```

### Backup from Host

The database file is stored in `./data/categorizer.db` on the host machine. You can copy it directly:

```bash
cp data/categorizer.db data/categorizer_backup_$(date +%Y%m%d_%H%M%S).db
```

## API Endpoints (Phase 1)

### Authentication

- `POST /auth/login` - Login with username and password
- `POST /auth/logout` - Logout and clear session
- `GET /auth/me` - Get current user (protected)

### Health Check

- `GET /health` - Health check endpoint

### Static Files

- `GET /static/*` - Serve static files (HTML, CSS, JS)
- `GET /` - Redirect to login page

**Note:** The application runs internally on port 8080 inside the container, but is accessible on port 1111 on your host machine.

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs categorizer
```

### Database errors

Reinitialize the database:
```bash
docker-compose down -v
docker-compose up -d
# Re-run initial setup (create users, import categories)
```

### Permission errors on database file

Ensure the `data/` directory has correct permissions:
```bash
chmod 777 data/
```

### Can't access on mobile device

1. Find your computer's IP address:
   ```bash
   # On Linux/Mac
   ip addr show | grep inet

   # On Windows
   ipconfig
   ```

2. Access from mobile: `http://<your-ip>:1111`

3. Ensure firewall allows port 1111

## Security Notes

- **Change the SECRET_KEY** in production (see Configuration)
- Default setup uses HTTP (not HTTPS). For production, add a reverse proxy (nginx, Caddy) with SSL/TLS
- Passwords are hashed with bcrypt
- Sessions use secure random tokens
- Minimum password length: 8 characters

## CSV Format

The application expects CSV files with this format (see `sample.csv`):

```csv
transaction,date,payee,category,status,withdrawal,deposit,total,comment
,21.07.2023,Store Name,,,100.50,,,
,22.07.2023,Salary,,,,5000.00,,
```

**Encoding:** latin-1 (for Danish characters: ø, å, æ)
**Date format:** DD.MM.YYYY
**Amounts:** withdrawal for expenses, deposit for income

## Roadmap

- [x] **Phase 1:** Foundation (authentication, database, CLI)
- [ ] **Phase 2:** Core batch flow (CSV upload, batch management)
- [ ] **Phase 3:** Categorization (transaction UI, category selector)
- [ ] **Phase 4:** Real-time sync (WebSocket, celebrations)
- [ ] **Phase 5:** Rules engine (auto-suggestions)
- [ ] **Phase 6:** Similar transactions (fuzzy matching)
- [ ] **Phase 7:** Polish (UX improvements, mobile optimization)
- [ ] **Phase 8:** Deployment (final testing, documentation)

## License

Private project for personal use.

## Support

For issues or questions, check:
- `docs/ARCHITECTURE.md` - System design
- `docs/REQUIREMENTS.md` - Feature specifications
- `docs/TODO.md` - Implementation checklist
- `docs/TESTING.md` - Testing strategy

---

**Version:** 0.1.0 (Phase 1 Complete)
