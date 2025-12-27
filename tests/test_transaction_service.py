"""
Tests for transaction service layer
"""

import pytest
from app.services.batch import create_batch
from app.services.transaction import (
    list_transactions,
    get_transaction_by_id,
    update_transaction,
    bulk_update_transactions,
    category_exists,
    clear_transaction_category,
    get_uncategorized_transactions,
    get_categorized_transactions
)
from app.services.user import create_user
from app.services.category import import_categories_from_file


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


@pytest.fixture
def categories(test_db):
    """Import test categories"""
    import_categories_from_file(test_db, '/app/categories.txt')


class TestListTransactions:
    """Tests for list_transactions function"""

    def test_list_transactions_success(self, test_db, test_user, sample_batch):
        """Test successfully listing transactions"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])

        assert len(transactions) == 3
        assert all('id' in t for t in transactions)
        assert all('payee' in t for t in transactions)
        assert all('amount' in t for t in transactions)

    def test_list_transactions_ordered_by_date(self, test_db, test_user, sample_batch):
        """Test that transactions are ordered by date"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])

        dates = [t['date'] for t in transactions]
        assert dates == sorted(dates)

    def test_list_transactions_ownership_check(self, test_db, test_user, test_user2, sample_batch):
        """Test that users can only list their own batch's transactions"""
        with pytest.raises(ValueError, match="not found|permission"):
            list_transactions(test_db, sample_batch, test_user2['id'])

    def test_list_transactions_batch_not_found(self, test_db, test_user):
        """Test error when batch doesn't exist"""
        with pytest.raises(ValueError, match="not found|permission"):
            list_transactions(test_db, 99999, test_user['id'])


class TestGetTransactionById:
    """Tests for get_transaction_by_id function"""

    def test_get_transaction_success(self, test_db, test_user, sample_batch):
        """Test successfully getting a transaction"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        transaction = get_transaction_by_id(test_db, transaction_id)

        assert transaction is not None
        assert transaction['id'] == transaction_id
        assert transaction['payee'] == 'Store A'
        assert transaction['amount'] == -100.50

    def test_get_transaction_not_found(self, test_db):
        """Test getting non-existent transaction"""
        transaction = get_transaction_by_id(test_db, 99999)
        assert transaction is None


class TestUpdateTransaction:
    """Tests for update_transaction function"""

    def test_update_transaction_category(self, test_db, test_user, sample_batch, categories):
        """Test updating transaction category"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        # Update category
        updated = update_transaction(
            test_db,
            transaction_id,
            category="Food:Groceries",
            note=None
        )

        assert updated['category'] == "Food:Groceries"
        assert updated['status'] == 'categorized'

    def test_update_transaction_note(self, test_db, test_user, sample_batch, categories):
        """Test updating transaction note"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        # Update note
        updated = update_transaction(
            test_db,
            transaction_id,
            category="Food:Groceries",
            note="Weekly shopping"
        )

        assert updated['category'] == "Food:Groceries"
        assert updated['note'] == "Weekly shopping"

    def test_update_transaction_category_and_note(self, test_db, test_user, sample_batch, categories):
        """Test updating both category and note"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        updated = update_transaction(
            test_db,
            transaction_id,
            category="Food:Groceries",
            note="Test note"
        )

        assert updated['category'] == "Food:Groceries"
        assert updated['note'] == "Test note"
        assert updated['status'] == 'categorized'

    def test_update_transaction_clear_category(self, test_db, test_user, sample_batch, categories):
        """Test clearing a transaction's category"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        # First set a category
        update_transaction(test_db, transaction_id, category="Food:Groceries")

        # Then clear it
        updated = update_transaction(test_db, transaction_id, category=None)

        assert updated['category'] is None
        assert updated['status'] == 'uncategorized'

    def test_update_transaction_invalid_category(self, test_db, test_user, sample_batch):
        """Test error when updating with non-existent category"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        with pytest.raises(ValueError, match="does not exist"):
            update_transaction(
                test_db,
                transaction_id,
                category="NonExistent:Category"
            )

    def test_update_transaction_not_found(self, test_db):
        """Test error when transaction doesn't exist"""
        with pytest.raises(ValueError, match="not found"):
            update_transaction(test_db, 99999, category="Food")

    def test_update_transaction_increments_usage_count(self, test_db, test_user, sample_batch, categories):
        """Test that updating a transaction increments category usage count"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        # Get initial usage count
        cursor = test_db.execute(
            "SELECT usage_count FROM categories WHERE full_path = ?",
            ("Food:Groceries",)
        )
        initial_count = cursor.fetchone()[0]

        # Update transaction
        update_transaction(test_db, transaction_id, category="Food:Groceries")

        # Check usage count increased
        cursor = test_db.execute(
            "SELECT usage_count FROM categories WHERE full_path = ?",
            ("Food:Groceries",)
        )
        new_count = cursor.fetchone()[0]

        assert new_count == initial_count + 1


class TestBulkUpdateTransactions:
    """Tests for bulk_update_transactions function"""

    def test_bulk_update_success(self, test_db, test_user, sample_batch, categories):
        """Test successfully bulk updating transactions"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_ids = [t['id'] for t in transactions[:2]]  # First two

        count = bulk_update_transactions(
            test_db,
            transaction_ids,
            category="Food:Groceries",
            note="Bulk update"
        )

        assert count == 2

        # Verify updates
        for txn_id in transaction_ids:
            txn = get_transaction_by_id(test_db, txn_id)
            assert txn['category'] == "Food:Groceries"
            assert txn['note'] == "Bulk update"

    def test_bulk_update_empty_list_error(self, test_db, test_user):
        """Test error when transaction IDs list is empty"""
        with pytest.raises(ValueError, match="No transaction IDs provided"):
            bulk_update_transactions(test_db, [], category="Food")

    def test_bulk_update_invalid_category(self, test_db, test_user, sample_batch):
        """Test error with invalid category"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_ids = [t['id'] for t in transactions]

        with pytest.raises(ValueError, match="does not exist"):
            bulk_update_transactions(
                test_db,
                transaction_ids,
                category="Invalid:Category"
            )

    def test_bulk_update_skips_nonexistent_transactions(self, test_db, test_user, sample_batch, categories):
        """Test that bulk update skips transactions that don't exist"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_ids = [transactions[0]['id'], 99999, transactions[1]['id']]

        count = bulk_update_transactions(
            test_db,
            transaction_ids,
            category="Food:Groceries"
        )

        # Should update 2 (skipping the non-existent one)
        assert count == 2

    def test_bulk_update_only_category(self, test_db, test_user, sample_batch, categories):
        """Test bulk update with only category (no note)"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_ids = [t['id'] for t in transactions]

        count = bulk_update_transactions(
            test_db,
            transaction_ids,
            category="Food:Groceries",
            note=None
        )

        assert count == 3

        # Verify only category was set
        for txn_id in transaction_ids:
            txn = get_transaction_by_id(test_db, txn_id)
            assert txn['category'] == "Food:Groceries"


class TestCategoryExists:
    """Tests for category_exists function"""

    def test_category_exists_true(self, test_db, categories):
        """Test checking for existing category"""
        assert category_exists(test_db, "Food:Groceries") is True

    def test_category_exists_false(self, test_db):
        """Test checking for non-existent category"""
        assert category_exists(test_db, "NonExistent:Category") is False


class TestClearTransactionCategory:
    """Tests for clear_transaction_category function"""

    def test_clear_category(self, test_db, test_user, sample_batch, categories):
        """Test clearing a transaction's category"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])
        transaction_id = transactions[0]['id']

        # Set a category first
        update_transaction(test_db, transaction_id, category="Food:Groceries")

        # Clear it
        updated = clear_transaction_category(test_db, transaction_id)

        assert updated['category'] is None
        assert updated['status'] == 'uncategorized'


class TestGetUncategorizedTransactions:
    """Tests for get_uncategorized_transactions function"""

    def test_get_uncategorized_transactions(self, test_db, test_user, sample_batch, categories):
        """Test getting only uncategorized transactions"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])

        # Categorize first transaction
        update_transaction(test_db, transactions[0]['id'], category="Food:Groceries")

        # Get uncategorized
        uncategorized = get_uncategorized_transactions(test_db, sample_batch, test_user['id'])

        assert len(uncategorized) == 2  # 2 out of 3 are uncategorized
        assert all(t['status'] == 'uncategorized' for t in uncategorized)

    def test_get_uncategorized_all_categorized(self, test_db, test_user, sample_batch, categories):
        """Test when all transactions are categorized"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])

        # Categorize all
        for txn in transactions:
            update_transaction(test_db, txn['id'], category="Food:Groceries")

        # Get uncategorized
        uncategorized = get_uncategorized_transactions(test_db, sample_batch, test_user['id'])

        assert len(uncategorized) == 0


class TestGetCategorizedTransactions:
    """Tests for get_categorized_transactions function"""

    def test_get_categorized_transactions(self, test_db, test_user, sample_batch, categories):
        """Test getting only categorized transactions"""
        transactions = list_transactions(test_db, sample_batch, test_user['id'])

        # Categorize first two transactions
        update_transaction(test_db, transactions[0]['id'], category="Food:Groceries")
        update_transaction(test_db, transactions[1]['id'], category="Income:Salary")

        # Get categorized
        categorized = get_categorized_transactions(test_db, sample_batch, test_user['id'])

        assert len(categorized) == 2
        assert all(t['status'] == 'categorized' for t in categorized)
        assert all(t['category'] is not None for t in categorized)

    def test_get_categorized_none_categorized(self, test_db, test_user, sample_batch):
        """Test when no transactions are categorized"""
        categorized = get_categorized_transactions(test_db, sample_batch, test_user['id'])

        assert len(categorized) == 0
