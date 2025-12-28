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

**Phase 6-8 (Upcoming):**
- Similar transaction matching
- Mobile device testing
- Performance optimization
- Final deployment polish

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
- Default setup uses HTTP (not HTTPS). For production, add a reverse proxy (nginx, Caddy) with SSL/TLS
- Passwords are hashed with bcrypt
- Sessions use secure random tokens
- Minimum password length: 8 characters

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
- [ ] **Phase 6:** Similar transactions (fuzzy matching)
- [~] **Phase 7:** Polish (UX improvements, mobile optimization) - Partially complete
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

**Version:** 0.5.0 (Phases 1-5 Complete - Rules Engine & Real-Time Sync)
