# Testing Strategy

## Overview

Testing focuses on the critical paths that would cause data loss or corruption if broken:
1. CSV parsing and generation
2. Categorization persistence
3. Real-time sync correctness

Lower priority: UI appearance (manual testing sufficient).

## Test Stack

- **pytest** - Test runner
- **pytest-asyncio** - Async test support for FastAPI
- **httpx** - Async HTTP client for API tests
- **pytest-cov** - Coverage reporting

## Test Categories

### 1. Unit Tests

#### CSV Parser (`test_csv_parser.py`)

```python
def test_parse_csv_basic():
    """Parse a well-formed CSV file"""
    
def test_parse_csv_latin1_encoding():
    """Handle latin-1 special characters (ø, å, æ)"""
    
def test_parse_csv_date_format():
    """Parse DD.MM.YYYY dates correctly"""
    
def test_parse_csv_withdrawal_amount():
    """Extract expense from withdrawal column"""
    
def test_parse_csv_deposit_amount():
    """Extract income from deposit column"""
    
def test_parse_csv_empty_fields():
    """Handle empty optional fields"""
    
def test_parse_csv_malformed_date():
    """Reject or handle malformed dates"""
    
def test_generate_csv_with_categories():
    """Generate CSV with filled category column"""
    
def test_generate_csv_preserves_encoding():
    """Output maintains latin-1 encoding"""
    
def test_generate_csv_includes_notes():
    """Notes appear in comment column"""
```

#### Rule Matching (`test_rules.py`)

```python
def test_rule_contains_match():
    """'IKEA' matches 'IKEA ))) 72547'"""
    
def test_rule_contains_case_insensitive():
    """'ikea' matches 'IKEA Store'"""
    
def test_rule_exact_match():
    """Exact match requires full string equality"""
    
def test_rule_exact_case_insensitive():
    """Exact match is still case-insensitive"""
    
def test_multiple_rules_match():
    """Transaction can match multiple rules"""
    
def test_no_rules_match():
    """Transaction with no matching rules returns empty"""
```

#### Category Logic (`test_categories.py`)

```python
def test_parse_category_parent_only():
    """'Clothing' -> parent=None, name='Clothing'"""
    
def test_parse_category_with_subcategory():
    """'Clothing:Shoes' -> parent='Clothing', name='Shoes'"""
    
def test_category_uniqueness():
    """Cannot create duplicate full_path"""
    
def test_frequent_categories_ordering():
    """Returns categories sorted by usage_count desc"""
```

### 2. Integration Tests

#### Batch Operations (`test_batch.py`)

```python
@pytest.fixture
def sample_csv():
    """Provide sample CSV content"""
    
async def test_upload_batch():
    """Upload CSV creates batch and transactions"""
    
async def test_upload_batch_calculates_date_range():
    """Batch date_start and date_end set from transactions"""
    
async def test_download_batch_archives():
    """Downloading batch sets status to archived"""
    
async def test_delete_batch_cascades():
    """Deleting batch removes all its transactions"""
    
async def test_list_batches_excludes_archived():
    """Default list omits archived batches"""
    
async def test_list_batches_includes_archived():
    """With flag, list includes archived batches"""
```

#### Transaction Operations (`test_transaction.py`)

```python
async def test_categorize_transaction():
    """Setting category updates transaction"""
    
async def test_categorize_records_user():
    """Categorization records who did it"""
    
async def test_categorize_updates_timestamp():
    """Categorization sets categorized_at"""
    
async def test_bulk_categorize():
    """Can categorize multiple transactions at once"""
    
async def test_batch_progress_calculation():
    """Progress correctly counts categorized vs total"""
    
async def test_batch_complete_detection():
    """Batch status changes to complete at 100%"""
```

#### Similar Transactions (`test_similar.py`)

```python
async def test_similar_by_payee():
    """Finds transactions with matching payee text"""
    
async def test_similar_by_payee_cross_batch():
    """Includes matches from other batches"""
    
async def test_similar_by_amount():
    """Finds transactions within amount threshold"""
    
async def test_surrounding_transactions():
    """Returns transactions near by date"""
```

### 3. API Tests

#### Authentication (`test_auth.py`)

```python
async def test_login_success():
    """Valid credentials return session"""
    
async def test_login_failure():
    """Invalid credentials return 401"""
    
async def test_protected_route_without_auth():
    """Protected routes return 401 without session"""
    
async def test_protected_route_with_auth():
    """Protected routes work with valid session"""
    
async def test_logout_clears_session():
    """Logout invalidates session"""
```

#### API Endpoints (`test_api.py`)

```python
async def test_create_batch():
    """POST /batches creates batch"""
    
async def test_get_batches():
    """GET /batches returns batch list"""
    
async def test_get_batch_transactions():
    """GET /batches/{id}/transactions returns transactions"""
    
async def test_update_transaction():
    """PATCH /transactions/{id} updates category"""
    
async def test_create_rule():
    """POST /rules creates rule"""
    
async def test_get_suggestions():
    """GET /transactions/{id}/suggestions returns matching rules"""
```

### 4. WebSocket Tests (`test_websocket.py`)

```python
async def test_websocket_connect():
    """Client can establish WebSocket connection"""
    
async def test_websocket_subscribe():
    """Client can subscribe to batch"""
    
async def test_websocket_broadcast_on_categorize():
    """Categorization broadcasts to other clients"""
    
async def test_websocket_batch_complete():
    """100% completion broadcasts batch_complete"""
    
async def test_websocket_reconnect():
    """Client can reconnect after disconnect"""
```

### 5. End-to-End Tests

Manual testing checklist (not automated):

#### Upload Flow
- [ ] Upload CSV file with special characters
- [ ] Verify transactions appear correctly
- [ ] Verify date range calculated
- [ ] Verify progress shows 0/N

#### Categorization Flow
- [ ] Select transaction, assign category
- [ ] Verify category persists after refresh
- [ ] Test frequent categories
- [ ] Test search
- [ ] Test drill-down
- [ ] Add note to transaction

#### Rules Flow
- [ ] Create rule from transaction
- [ ] Edit payee pattern
- [ ] Verify rule applies to other transactions
- [ ] Delete rule

#### Multi-User Flow
- [ ] Login as user 1 on phone 1
- [ ] Login as user 2 on phone 2
- [ ] Both view same batch
- [ ] User 1 categorizes transaction
- [ ] Verify user 2 sees update in real-time
- [ ] Categorize last transaction, verify both see celebration

#### Download Flow
- [ ] Download completed batch
- [ ] Verify CSV has categories
- [ ] Verify batch is archived
- [ ] Verify archived batch hidden from default list

## Test Data

### Sample CSV (`tests/fixtures/sample.csv`)

```csv
transaction,date,payee,category,status,withdrawal,deposit,total,comment
,21.07.2023,DSB NETBUTIK       09589,,,160.0,,,
,21.07.2023,ALDI Øst 090       00395,,,146.45,,,
,22.07.2023,MobilePay Henrik Damm,,,100.0,,,
,24.07.2023,GOOGLE *Google g.co/helpp,,,39.0,,,
,27.07.2023,Lønoverførsel,,,,28511.61,,
```

### Sample Categories (`tests/fixtures/categories.txt`)

Subset of real categories for testing:

```
Food
Food:Groceries
Food:Dining out
Transportation
Transportation:Public transit
Automobile:Gasoline
```

## Test Configuration

### conftest.py

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import get_db, init_db

@pytest.fixture
def test_db():
    """Create fresh test database"""
    # Use in-memory SQLite for speed
    # Initialize schema
    # Yield connection
    # Cleanup

@pytest.fixture
async def client(test_db):
    """Async test client with test database"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def authenticated_client(client):
    """Client with valid session"""
    # Create test user
    # Login
    # Return client with session cookie
```

## Coverage Goals

- CSV parser: 100% (critical for data integrity)
- Rule matching: 100% (affects categorization suggestions)
- API endpoints: 90%+ (all happy paths, key error cases)
- WebSocket: 80% (basic functionality)
- UI: Manual testing only

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_csv_parser.py

# Run specific test
pytest tests/test_csv_parser.py::test_parse_csv_latin1_encoding

# Run with verbose output
pytest -v
```

## CI Considerations

If setting up CI later:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
```
