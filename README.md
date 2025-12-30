# Money Fest

A self-hosted web application for collaborative bank transaction categorization on mobile devices. Built for couples to jointly categorize their bank transactions in small batches using smartphones, with real-time synchronization.

## Features

**Phase 1 (Complete):**
- ✅ User authentication with secure sessions
- ✅ Mobile-friendly login UI
- ✅ Database schema for transactions, categories, batches, and rules
- ✅ CLI tools for user management and setup
- ✅ 175 pre-defined expense categories

**Phase 2 (Complete):**
- ✅ CSV upload with auto-format detection (AceMoney & Danske Bank)
- ✅ Flexible encoding support (UTF-8, ISO-8859-1, latin-1)
- ✅ Multiple date format support (DD.MM.YYYY, DD-MM-YYYY)
- ✅ Batch management (create, list, delete, archive/unarchive)
- ✅ Transaction listing and updates
- ✅ Bulk transaction categorization
- ✅ Category management with usage tracking
- ✅ Frequent categories endpoint
- ✅ CSV download in AceMoney format
- ✅ Progress tracking (X/Y categorized, percentage)
- ✅ Date range calculation
- ✅ Ownership verification for multi-user support

**Phase 3 (Complete):**
- ✅ Full-featured categorization UI
- ✅ Mobile-responsive transaction table
- ✅ Filter tabs (All/Uncategorized/Categorized)
- ✅ Multi-select with bulk categorization
- ✅ Hierarchical category selector with search
- ✅ Real-time progress tracking
- ✅ Toast notifications

**Phase 4 (Complete):**
- ✅ WebSocket real-time synchronization
- ✅ Multi-user collaboration support
- ✅ Auto-reconnect with exponential backoff
- ✅ Live transaction updates across clients
- ✅ Batch completion celebration animation

**Phase 5 (Complete):**
- ✅ Rules engine with pattern matching
- ✅ Category suggestions based on rules
- ✅ Rules management UI with live preview
- ✅ Create rules from transactions
- ✅ Multiple matching rules support

**Phase 6 (Complete):**
- ✅ Similar transaction fuzzy matching with configurable tolerance
- ✅ Reference transaction display in suggestions
- ✅ Smart matching algorithm balancing precision and recall

**Phase 7 (Complete):**
- ✅ Web-based first-time setup (no CLI required)
- ✅ Web-based user management
- ✅ HTTPS support with automatic certificate generation
- ✅ Mobile-optimized interface

**Phase 8 (In Progress):**
- ✅ Home Assistant add-on configuration
- ✅ Automatic SSL certificate generation (10-year validity)
- 🔄 Production deployment
- 🔄 Final documentation

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

### 3. First-Time Setup

**Option A: Web-Based Setup (Recommended)**

1. Open your browser to `http://localhost:1111/setup`
2. Fill out the setup form:
   - **Username**: 3-50 characters
   - **Password**: 8+ characters
   - **Confirm Password**: Must match
3. Click "Create User"
4. You'll be redirected to the login page
5. Log in with your new credentials

**The `/setup` page becomes inaccessible after the first user is created (security feature).**

To create additional users, log in and click the "Users" button in the header.

**Option B: CLI Setup (Advanced)**

```bash
# Create first user
docker exec -it categorizer python -m app.cli create-user martin

# Create second user
docker exec -it categorizer python -m app.cli create-user wife

# Import categories (optional - auto-imported on first run)
docker exec categorizer python -m app.cli import-categories /app/categories.txt
```

### 4. Optional: Enable HTTPS

For secure access over your local network:

```bash
# Create .env file
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" > .env
echo "SSL_ENABLED=true" >> .env

# Restart container
docker-compose restart
```

Access via `https://localhost:1111` (certificates auto-generated with 10-year validity).

See [HTTPS-SETUP.md](HTTPS-SETUP.md) for detailed instructions.

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

### reset-password

Reset a user's password without losing data.

```bash
# Interactive mode (most secure, requires -it flag)
docker exec -it categorizer python -m app.cli reset-password <username>

# Non-interactive mode with --password flag
docker exec categorizer python -m app.cli reset-password <username> --password <newpassword>

# Using environment variable
docker exec -e USER_PASSWORD=<newpassword> categorizer python -m app.cli reset-password <username>
```

**Examples:**
```bash
# Interactive (will prompt for password)
docker exec -it categorizer python -m app.cli reset-password martin

# Non-interactive with password argument
docker exec categorizer python -m app.cli reset-password martin --password newpassword123
```

Password must be at least 8 characters. User must exist in the database.

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

## Home Assistant Add-on

Money Fest can be installed as a Home Assistant add-on for seamless integration with your smart home.

### Features

- **Web-based setup** - Create users via browser (no CLI required)
- **Auto-SSL** - Automatic certificate generation when enabled
- **Persistent storage** - Database and certificates stored in `/data`
- **Multi-architecture** - Supports amd64, aarch64, armv7
- **Separate port access** - Not Ingress, accessible via IP:PORT

### Installation

1. Add the repository to Home Assistant:
   - Settings → Add-ons → Repositories
   - Add repository URL

2. Install "Money Fest" from the add-on store

3. Configure the add-on:
   - Set a strong `secret_key`
   - Optionally enable `ssl_enabled`
   - Adjust port, log level, etc.

4. Start the add-on

5. First-time setup:
   - Visit `http://[YOUR-HA-IP]:[PORT]/setup`
   - Create your first user via web form
   - Log in and start categorizing!

See [money_fest/DOCS.md](money_fest/DOCS.md) for complete documentation.

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

**Note:** Tests are excluded from the Docker container by default (production optimization). To run tests:

**Option 1: Build a dev container with tests**
```bash
# Temporarily remove tests/ from .dockerignore
sed -i '/^tests\//d' .dockerignore

# Rebuild container
docker compose build
docker compose up -d

# Run tests
docker exec categorizer pytest -v
docker exec categorizer pytest --cov=app --cov-report=html
```

**Option 2: Run tests locally**
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v
pytest --cov=app --cov-report=html
```

**Test Coverage:**
- 33 comprehensive tests covering Phase 1
- Database schema, indexes, and constraints
- Authentication flows and sessions
- CLI commands and services
- Target: 80%+ overall, 90%+ for auth/user modules

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

## API Endpoints

### Authentication (Phase 1)

- `POST /auth/login` - Login with username and password
- `POST /auth/logout` - Logout and clear session
- `GET /auth/me` - Get current user (protected)

### Setup (Phase 7)

- `GET /setup` - First-time setup page (only accessible when no users exist)
- `POST /setup` - Create first user account
  - Body: `{"username": "admin", "password": "password123", "confirm_password": "password123"}`
  - Redirects to login after success
  - Returns 303 redirect to login if users already exist

### User Management (Phase 7)

- `GET /users/list` - List all users (protected)
- `POST /users/create` - Create new user (protected)
  - Body: `{"username": "newuser", "password": "password123", "confirm_password": "password123"}`

### Batches (Phase 2)

- `POST /batches` - Upload CSV file and create batch
  - Accepts: multipart/form-data (name, file)
  - Auto-detects CSV format (AceMoney or Danske Bank)
  - Returns: Batch with progress information
- `GET /batches?include_archived=false` - List all batches
  - Query params: `include_archived` (boolean, default false)
  - Returns: List of batches with progress
- `GET /batches/{id}` - Get batch details with progress
- `DELETE /batches/{id}` - Delete batch and all transactions
- `POST /batches/{id}/archive` - Archive a batch
- `POST /batches/{id}/unarchive` - Unarchive a batch
- `GET /batches/{id}/download` - Download batch as CSV (AceMoney format)
  - Automatically archives batch after download

### Transactions (Phase 2)

- `GET /batches/{batch_id}/transactions` - List transactions for a batch
- `PUT /transactions/{id}` - Update transaction category and/or note
  - Body: `{"category": "Food:Groceries", "note": "Weekly shopping"}`
- `PUT /transactions/bulk` - Bulk update multiple transactions
  - Body: `{"transaction_ids": [1,2,3], "category": "Food:Groceries"}`

### Categories (Phase 2)

- `GET /categories` - List all categories (175 items)
- `GET /categories/frequent?limit=15` - List frequently used categories
  - Query params: `limit` (int, 1-50, default 15)
  - Ordered by usage_count descending

### Rules (Phase 5)

- `GET /rules` - List all rules for current user
- `POST /rules` - Create new rule
  - Body: `{"pattern": "IKEA", "match_type": "contains", "category": "Home:Furniture"}`
- `GET /rules/{id}` - Get specific rule
- `PUT /rules/{id}` - Update rule
  - Body: `{"pattern": "...", "match_type": "...", "category": "..."}`
- `DELETE /rules/{id}` - Delete rule
- `GET /rules/suggestions/{transaction_id}` - Get category suggestions for transaction
  - Returns: List of matching rules with categories
- `POST /rules/preview` - Preview which transactions match a rule pattern
  - Body: `{"pattern": "IKEA", "match_type": "contains"}`
  - Returns: List of matching transactions

### WebSocket (Phase 4)

- `WS /ws` - WebSocket connection for real-time updates
  - Messages:
    - `{"type": "subscribe", "batch_id": 123}` - Subscribe to batch updates
    - `{"type": "transaction_updated", "batch_id": 123, "transaction": {...}}` - Transaction updated
    - `{"type": "batch_progress", "batch_id": 123, "categorized": 5, "total": 10}` - Progress update
    - `{"type": "batch_complete", "batch_id": 123}` - All transactions categorized

### Similar Transactions (Phase 6)

- `GET /similar/{transaction_id}` - Find similar categorized transactions
  - Query params: `tolerance` (float, 0.0-1.0, default 0.05 = 5%)
  - Returns: List of similar transactions with categories and reference info
  - Uses fuzzy matching on payee text and amount tolerance

### Health Check

- `GET /health` - Health check endpoint

### Static Files

- `GET /static/*` - Serve static files (HTML, CSS, JS)
- `GET /` - Redirect to login page

**Note:** The application runs internally on port 8080 inside the container, but is accessible on port 1111 on your host machine.

**Authentication:** All endpoints except `/auth/login` and `/health` require authentication via session cookie.

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
- **HTTPS Support**: Enable with `SSL_ENABLED=true` for automatic self-signed certificate generation (10-year validity)
- Passwords are hashed with bcrypt (industry standard)
- Sessions use cryptographically signed tokens with SECRET_KEY
- Session cookies are secure and HTTP-only
- Minimum password length: 8 characters
- For internet-facing deployments, use a reverse proxy (nginx, Caddy) with Let's Encrypt certificates

See [HTTPS-SETUP.md](HTTPS-SETUP.md) for SSL/TLS configuration details.

## CSV Formats

The application auto-detects and supports two CSV formats:

### Format 1: AceMoney (Default Output Format)

```csv
transaction,date,payee,category,status,withdrawal,deposit,total,comment
,21.07.2023,Store Name,,,100.50,,,
,22.07.2023,Salary,,,,5000.00,,
```

**Encoding:** latin-1 (for Danish characters: ø, å, æ)
**Delimiter:** comma (`,`)
**Date formats:** DD.MM.YYYY or DD-MM-YYYY (both supported)
**Amounts:** Separate withdrawal/deposit columns (only one populated per row)
- `withdrawal`: 100.50 → stored as -100.50 (expense)
- `deposit`: 5000.00 → stored as +5000.00 (income)

### Format 2: Danske Bank

```csv
"Dato";"Tekst";"Beløb";"Saldo";"Status";"Afstemt"
"25.11.2024";"Netto ScanNGo";"-41,80";"98.302,29";"Udført";"Nej"
"26.11.2024";"Salary";"28.500,00";"126.193,28";"Udført";"Nej"
```

**Encoding:** UTF-8 or ISO-8859-1 (both supported)
**Delimiter:** semicolon (`;`)
**Date format:** DD.MM.YYYY
**Amounts:** Single "Beløb" column with Danish decimal format
- Thousand separator: `.` (period)
- Decimal separator: `,` (comma)
- Example: "1.234,56" → stored as 1234.56
- Example: "-41,80" → stored as -41.80 (expense)
**Note:** "Saldo" (running balance) column is ignored

### Auto-Detection

Upload either format - the application automatically detects which format you're using based on:
1. File encoding (UTF-8, ISO-8859-1, or latin-1)
2. Delimiter (semicolon vs comma)
3. Header columns
4. Date format (automatically handles both DD.MM.YYYY and DD-MM-YYYY)

### Export Format

Downloaded CSV files are always in **AceMoney format** for import to AceMoney software.

## Roadmap

- [x] **Phase 1:** Foundation (authentication, database, CLI)
- [x] **Phase 2:** Core batch flow (CSV upload, batch management, transactions)
- [x] **Phase 3:** Categorization UI (transaction UI, category selector)
- [x] **Phase 4:** Real-time sync (WebSocket, celebrations)
- [x] **Phase 5:** Rules engine (suggestion-based categorization)
- [x] **Phase 6:** Similar transactions (fuzzy matching with configurable tolerance)
- [x] **Phase 7:** Polish (web setup, user management, HTTPS, mobile optimization)
- [~] **Phase 8:** Deployment (HA add-on, documentation) - In progress

## License

Private project for personal use.

## Support

For issues or questions, check:
- `docs/ARCHITECTURE.md` - System design
- `docs/REQUIREMENTS.md` - Feature specifications
- `docs/TODO.md` - Implementation checklist
- `docs/TESTING.md` - Testing strategy

---

**Version:** 0.8.0 (Phases 1-7 Complete - Web Setup, User Management, HTTPS, HA Add-on Ready)
