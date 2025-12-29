# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Container                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  FastAPI Backend                      │   │
│  │                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │   HTTP      │  │  WebSocket  │  │   Static    │  │   │
│  │  │   Routes    │  │   Handler   │  │   Files     │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │         │                │                │          │   │
│  │         └────────────────┼────────────────┘          │   │
│  │                          │                           │   │
│  │                   ┌──────┴──────┐                    │   │
│  │                   │   Services  │                    │   │
│  │                   └──────┬──────┘                    │   │
│  │                          │                           │   │
│  │                   ┌──────┴──────┐                    │   │
│  │                   │   SQLite    │                    │   │
│  │                   └─────────────┘                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │
         │                    │
    ┌────┴────┐          ┌────┴────┐
    │ Phone 1 │          │ Phone 2 │
    │ (User)  │          │ (Wife)  │
    └─────────┘          └─────────┘
```

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Python 3.11+ / FastAPI | User familiar with Python, FastAPI has good WebSocket support |
| Database | SQLite | Simple, no extra container, easy backup, sufficient for 2 users |
| Frontend | HTML + Vanilla JS + CSS | No build step, works everywhere, minimal complexity |
| Real-time | WebSocket | Native browser support, FastAPI has good support |
| Container | Docker | Single container with volume for SQLite persistence |

## Data Model

### Entity Relationship

```
┌─────────┐       ┌─────────────┐       ┌──────────┐
│  User   │───────│ Transaction │───────│  Batch   │
└─────────┘       └─────────────┘       └──────────┘
     │                   │
     │            ┌──────┴──────┐
     │            │             │
     │       ┌────┴────┐  ┌─────┴─────┐
     │       │Category │  │   Rule    │
     │       └─────────┘  └───────────┘
     │                          │
     └──────────────────────────┘
```

### Tables

#### users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### categories
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent TEXT,                    -- NULL for top-level, e.g., "Clothing"
    name TEXT NOT NULL,             -- "Clothing" or "Shoes"
    full_path TEXT UNIQUE NOT NULL, -- "Clothing" or "Clothing:Shoes"
    usage_count INTEGER DEFAULT 0,  -- For frequent category sorting
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### batches
```sql
CREATE TABLE batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,             -- User-provided name
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_start DATE,                -- Earliest transaction date
    date_end DATE,                  -- Latest transaction date
    status TEXT DEFAULT 'in_progress', -- in_progress, complete, archived
    archived_at TIMESTAMP
);
```

#### transactions
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    payee TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,  -- Negative for withdrawals
    category_id INTEGER REFERENCES categories(id),
    note TEXT,
    categorized_by INTEGER REFERENCES users(id),
    categorized_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_batch ON transactions(batch_id);
CREATE INDEX idx_transactions_payee ON transactions(payee);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_amount ON transactions(amount);
```

#### rules
```sql
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,          -- The cleaned payee pattern
    match_type TEXT DEFAULT 'contains', -- 'contains' or 'exact'
    category_id INTEGER NOT NULL REFERENCES categories(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rules_pattern ON rules(pattern);
```

## API Design

### REST Endpoints

#### Authentication
- `POST /auth/login` - Login, returns session cookie
- `POST /auth/logout` - Logout, clears session

#### Batches
- `GET /batches` - List batches (query param: include_archived=true)
- `POST /batches` - Upload CSV, create batch
- `GET /batches/{id}` - Get batch details
- `GET /batches/{id}/download` - Download categorized CSV, auto-archives
- `DELETE /batches/{id}` - Delete batch and all transactions
- `POST /batches/{id}/unarchive` - Restore archived batch

#### Transactions
- `GET /batches/{id}/transactions` - List transactions in batch
- `PATCH /transactions/{id}` - Update category/note
- `POST /transactions/bulk-categorize` - Categorize multiple transactions

#### Categories
- `GET /categories` - List all categories
- `POST /categories` - Add new category
- `GET /categories/frequent` - Get top N most used

#### Rules
- `GET /rules` - List all rules
- `POST /rules` - Create rule
- `DELETE /rules/{id}` - Delete rule
- `GET /transactions/{id}/suggestions` - Get matching rules for transaction

#### Similar Transactions
- `GET /transactions/{id}/similar` - Get similar transactions
  - Query params:
    - `min_similarity` (float, 0.0-1.0, default 0.6) - Minimum similarity for fuzzy payee matching
    - `tolerance` (float, 0.0-1.0, default 0.10) - Tolerance for amount matching (±%)
  - Returns: Dict with `by_payee`, `by_amount`, `surrounding`, and reference `transaction`

### WebSocket

Single WebSocket endpoint: `WS /ws`

#### Client → Server Messages
```json
{"type": "subscribe", "batch_id": 123}
{"type": "unsubscribe", "batch_id": 123}
```

#### Server → Client Messages
```json
{"type": "transaction_updated", "batch_id": 123, "transaction_id": 456, "category": "Food:Groceries", "by": "Martin"}
{"type": "batch_complete", "batch_id": 123}
{"type": "batch_progress", "batch_id": 123, "done": 47, "total": 103}
```

## Frontend Structure

```
static/
├── index.html          # Main app shell
├── css/
│   └── style.css       # All styles
└── js/
    ├── app.js          # Main application logic
    ├── api.js          # API client
    ├── ws.js           # WebSocket handler
    ├── ui.js           # UI components/rendering
    └── categories.js   # Category selector logic
```

### Pages/Views (Single Page, JS-switched)
1. **Login** - Username/password form
2. **Batch List** - Main view, shows all batches with progress
3. **Categorize** - Transaction list for a batch, category selector
4. **Rules** - Manage rules (secondary, accessed from menu)

## File Structure

```
transaction-categorizer/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes
│   ├── config.py            # Configuration
│   ├── database.py          # SQLite connection, init
│   ├── models.py            # Pydantic models
│   ├── auth.py              # Authentication logic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── batch.py         # Batch operations
│   │   ├── transaction.py   # Transaction operations
│   │   ├── category.py      # Category operations
│   │   ├── rule.py          # Rule operations
│   │   └── csv_parser.py    # CSV import/export
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── batches.py
│   │   ├── transactions.py
│   │   ├── categories.py
│   │   └── rules.py
│   └── websocket.py         # WebSocket handler
├── static/                  # Frontend files
│   └── ...
├── data/                    # SQLite DB location (Docker volume)
│   └── categorizer.db
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_csv_parser.py
    ├── test_batch.py
    ├── test_transaction.py
    ├── test_rules.py
    └── test_websocket.py
```

## Security Considerations

- Passwords hashed with bcrypt
- Session-based auth with secure cookies
- HTTPS should be handled by reverse proxy (not in app)
- No sensitive data logging
- SQL injection prevented by parameterized queries

## Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  categorizer:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

### Initial Setup
1. First run creates database schema
2. Must create two user accounts (CLI command or first-run UI)
3. Import categories from provided list

### Backup
SQLite database is a single file at `data/categorizer.db`. Back up this file.
