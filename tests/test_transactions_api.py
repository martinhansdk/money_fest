"""
API integration tests for transaction endpoints
"""

import pytest
from app.services.batch import create_batch
from app.services.user import create_user
from app.services.category import import_categories_from_file


@pytest.fixture
def categories(test_db):
    """Import test categories"""
    import_categories_from_file(test_db, '/app/categories.txt')


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user_id = create_user(test_db, "testuser", "password123")
    return {'id': user_id, 'username': 'testuser'}


@pytest.fixture
def test_user2(test_db):
    """Create a second test user"""
    user_id = create_user(test_db, "testuser2", "password123")
    return {'id': user_id, 'username': 'testuser2'}


@pytest.fixture
def sample_batch(test_db, test_user):
    """Create a sample batch with transactions"""
    transactions = [
        {
            'date': '2024-01-15',
            'payee': 'Store A',
            'amount': -100.50,
            'original_category': '',
            'original_comment': ''
        },
        {
            'date': '2024-01-20',
            'payee': 'Salary',
            'amount': 5000.00,
            'original_category': '',
            'original_comment': 'Monthly'
        },
        {
            'date': '2024-01-25',
            'payee': 'Store B',
            'amount': -50.00,
            'original_category': '',
            'original_comment': ''
        }
    ]

    batch_id = create_batch(test_db, "Test Batch", test_user['id'], transactions)
    return batch_id


class TestGetBatchTransactions:
    """Tests for GET /batches/{batch_id}/transactions endpoint"""

    def test_get_batch_transactions_success(self, authenticated_client, sample_batch):
        """Test getting transactions for a batch"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3

        # Check transaction structure
        transaction = data[0]
        required_fields = ['id', 'batch_id', 'date', 'payee', 'amount',
                          'category', 'note', 'status', 'created_at', 'updated_at']
        for field in required_fields:
            assert field in transaction

    def test_get_batch_transactions_ordered_by_date(self, authenticated_client, sample_batch):
        """Test that transactions are ordered by date"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")

        assert response.status_code == 200
        data = response.json()

        dates = [t['date'] for t in data]
        assert dates == sorted(dates)

    def test_get_batch_transactions_requires_auth(self, client, sample_batch):
        """Test that endpoint requires authentication"""
        response = client.get(f"/batches/{sample_batch}/transactions")

        assert response.status_code == 401

    def test_get_batch_transactions_ownership_check(self, client, test_db, test_user2, sample_batch):
        """Test that users can only get their own batch's transactions"""
        # Create a client authenticated as user2
        from app.auth import create_session
        session_id = create_session(test_user2['id'])

        response = client.get(
            f"/batches/{sample_batch}/transactions",
            cookies={"session_id": session_id}
        )

        assert response.status_code == 404

    def test_get_batch_transactions_batch_not_found(self, authenticated_client):
        """Test getting transactions for non-existent batch"""
        response = authenticated_client.get("/batches/99999/transactions")

        assert response.status_code == 404


class TestUpdateTransaction:
    """Tests for PUT /transactions/{id} endpoint"""

    def test_update_transaction_category(self, authenticated_client, sample_batch, categories):
        """Test updating transaction category"""
        # Get a transaction
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
        transaction_id = response.json()[0]['id']

        # Update category
        response = authenticated_client.put(
            f"/transactions/{transaction_id}",
            json={"category": "Food:Groceries", "note": None}
        )

        assert response.status_code == 200
        data = response.json()

        assert data['category'] == "Food:Groceries"
        assert data['status'] == 'categorized'

    def test_update_transaction_note(self, authenticated_client, sample_batch, categories):
        """Test updating transaction note"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
        transaction_id = response.json()[0]['id']

        response = authenticated_client.put(
            f"/transactions/{transaction_id}",
            json={"category": "Food:Groceries", "note": "Weekly shopping"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data['category'] == "Food:Groceries"
        assert data['note'] == "Weekly shopping"

    def test_update_transaction_clear_category(self, authenticated_client, sample_batch, categories):
        """Test clearing a transaction's category"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
        transaction_id = response.json()[0]['id']

        # Set category first
        authenticated_client.put(
            f"/transactions/{transaction_id}",
            json={"category": "Food:Groceries"}
        )

        # Clear it
        response = authenticated_client.put(
            f"/transactions/{transaction_id}",
            json={"category": None, "note": None}
        )

        assert response.status_code == 200
        data = response.json()

        assert data['category'] is None
        assert data['status'] == 'uncategorized'

    def test_update_transaction_invalid_category(self, authenticated_client, sample_batch):
        """Test error when updating with non-existent category"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
        transaction_id = response.json()[0]['id']

        response = authenticated_client.put(
            f"/transactions/{transaction_id}",
            json={"category": "NonExistent:Category"}
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()['detail']

    def test_update_transaction_not_found(self, authenticated_client):
        """Test updating non-existent transaction"""
        response = authenticated_client.put(
            "/transactions/99999",
            json={"category": "Food"}
        )

        assert response.status_code == 404

    def test_update_transaction_requires_auth(self, client, sample_batch):
        """Test that endpoint requires authentication"""
        response = client.put(
            "/transactions/1",
            json={"category": "Food"}
        )

        assert response.status_code == 401


class TestBulkUpdateTransactions:
    """Tests for PUT /transactions/bulk endpoint"""

    def test_bulk_update_success(self, authenticated_client, sample_batch, categories):
        """Test bulk updating transactions"""
        # Get transactions
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
        transactions = response.json()
        transaction_ids = [t['id'] for t in transactions[:2]]

        # Bulk update
        response = authenticated_client.put(
            "/transactions/bulk",
            json={
                "transaction_ids": transaction_ids,
                "category": "Food:Groceries",
                "note": "Bulk update"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['updated'] == 2

        # Verify updates
        for txn_id in transaction_ids:
            response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
            txns = response.json()
            txn = [t for t in txns if t['id'] == txn_id][0]
            assert txn['category'] == "Food:Groceries"
            assert txn['note'] == "Bulk update"

    def test_bulk_update_empty_list_error(self, authenticated_client):
        """Test error when transaction IDs list is empty"""
        response = authenticated_client.put(
            "/transactions/bulk",
            json={
                "transaction_ids": [],
                "category": "Food"
            }
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_bulk_update_invalid_category(self, authenticated_client, sample_batch):
        """Test error with invalid category"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
        transactions = response.json()
        transaction_ids = [t['id'] for t in transactions]

        response = authenticated_client.put(
            "/transactions/bulk",
            json={
                "transaction_ids": transaction_ids,
                "category": "Invalid:Category"
            }
        )

        assert response.status_code == 400
        assert "does not exist" in response.json()['detail']

    def test_bulk_update_only_category(self, authenticated_client, sample_batch, categories):
        """Test bulk update with only category (no note)"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")
        transactions = response.json()
        transaction_ids = [t['id'] for t in transactions]

        response = authenticated_client.put(
            "/transactions/bulk",
            json={
                "transaction_ids": transaction_ids,
                "category": "Food:Groceries"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['updated'] == 3

    def test_bulk_update_requires_auth(self, client):
        """Test that endpoint requires authentication"""
        response = client.put(
            "/transactions/bulk",
            json={
                "transaction_ids": [1, 2],
                "category": "Food"
            }
        )

        assert response.status_code == 401


class TestTransactionResponseModel:
    """Tests for transaction response model validation"""

    def test_transaction_response_has_all_fields(self, authenticated_client, sample_batch):
        """Test that transaction response includes all required fields"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")

        assert response.status_code == 200
        data = response.json()

        assert len(data) > 0
        transaction = data[0]

        required_fields = ['id', 'batch_id', 'date', 'payee', 'amount',
                          'category', 'note', 'status', 'created_at', 'updated_at']
        for field in required_fields:
            assert field in transaction

    def test_transaction_nullable_fields(self, authenticated_client, sample_batch):
        """Test that category and note can be null"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")

        assert response.status_code == 200
        data = response.json()

        # Find an uncategorized transaction
        uncategorized = [t for t in data if t['status'] == 'uncategorized']

        if len(uncategorized) > 0:
            assert uncategorized[0]['category'] is None

    def test_transaction_date_format(self, authenticated_client, sample_batch):
        """Test that transaction dates are in YYYY-MM-DD format"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")

        assert response.status_code == 200
        data = response.json()

        for transaction in data:
            # Should be YYYY-MM-DD format
            assert len(transaction['date']) == 10
            assert transaction['date'].count('-') == 2

    def test_transaction_amount_format(self, authenticated_client, sample_batch):
        """Test that transaction amounts are floats"""
        response = authenticated_client.get(f"/batches/{sample_batch}/transactions")

        assert response.status_code == 200
        data = response.json()

        for transaction in data:
            assert isinstance(transaction['amount'], (int, float))
