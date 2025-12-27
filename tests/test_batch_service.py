"""
Tests for batch service layer
"""

import pytest
from datetime import datetime
from app.services.batch import (
    create_batch,
    get_batch_by_id,
    list_batches,
    delete_batch,
    archive_batch,
    unarchive_batch,
    calculate_batch_date_range,
    get_batch_progress,
    verify_batch_ownership
)
from app.services.user import create_user


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
def sample_transactions():
    """Sample transactions for testing"""
    return [
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
            'original_category': 'Income:Salary',
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


class TestCreateBatch:
    """Tests for create_batch function"""

    def test_create_batch_success(self, test_db, test_user, sample_transactions):
        """Test successfully creating a batch"""
        batch_id = create_batch(
            test_db,
            "January 2024",
            test_user['id'],
            sample_transactions
        )

        assert batch_id > 0

        # Verify batch was created
        batch = get_batch_by_id(test_db, batch_id)
        assert batch is not None
        assert batch['name'] == "January 2024"
        assert batch['user_id'] == test_user['id']
        assert batch['status'] == 'in_progress'
        assert batch['date_range_start'] == '2024-01-15'
        assert batch['date_range_end'] == '2024-01-25'

    def test_create_batch_empty_name_error(self, test_db, test_user, sample_transactions):
        """Test error when batch name is empty"""
        with pytest.raises(ValueError, match="Batch name is required"):
            create_batch(test_db, "", test_user['id'], sample_transactions)

        with pytest.raises(ValueError, match="Batch name is required"):
            create_batch(test_db, "   ", test_user['id'], sample_transactions)

    def test_create_batch_empty_transactions_error(self, test_db, test_user):
        """Test error when transactions list is empty"""
        with pytest.raises(ValueError, match="At least one transaction is required"):
            create_batch(test_db, "Test Batch", test_user['id'], [])

    def test_create_batch_creates_transactions(self, test_db, test_user, sample_transactions):
        """Test that transactions are created with the batch"""
        batch_id = create_batch(
            test_db,
            "Test Batch",
            test_user['id'],
            sample_transactions
        )

        # Verify transactions were created
        cursor = test_db.execute(
            "SELECT COUNT(*) FROM transactions WHERE batch_id = ?",
            (batch_id,)
        )
        count = cursor.fetchone()[0]
        assert count == 3

    def test_create_batch_transaction_status(self, test_db, test_user, sample_transactions):
        """Test that transaction status is set correctly"""
        batch_id = create_batch(
            test_db,
            "Test Batch",
            test_user['id'],
            sample_transactions
        )

        # Get transactions
        cursor = test_db.execute(
            "SELECT status, category FROM transactions WHERE batch_id = ? ORDER BY id",
            (batch_id,)
        )
        rows = cursor.fetchall()

        # First transaction has no category -> uncategorized
        assert rows[0][0] == 'uncategorized'
        assert rows[0][1] is None

        # Second transaction has category -> categorized
        assert rows[1][0] == 'categorized'
        assert rows[1][1] == 'Income:Salary'

        # Third transaction has no category -> uncategorized
        assert rows[2][0] == 'uncategorized'


class TestGetBatchById:
    """Tests for get_batch_by_id function"""

    def test_get_batch_by_id_success(self, test_db, test_user, sample_transactions):
        """Test getting a batch by ID"""
        batch_id = create_batch(
            test_db,
            "Test Batch",
            test_user['id'],
            sample_transactions
        )

        batch = get_batch_by_id(test_db, batch_id)

        assert batch is not None
        assert batch['id'] == batch_id
        assert batch['name'] == "Test Batch"
        assert batch['user_id'] == test_user['id']
        assert batch['status'] == 'in_progress'

    def test_get_batch_by_id_not_found(self, test_db):
        """Test getting a non-existent batch"""
        batch = get_batch_by_id(test_db, 99999)
        assert batch is None

    def test_get_batch_with_progress(self, test_db, test_user, sample_transactions):
        """Test that batch includes progress information"""
        batch_id = create_batch(
            test_db,
            "Test Batch",
            test_user['id'],
            sample_transactions
        )

        batch = get_batch_by_id(test_db, batch_id)

        assert 'total_count' in batch
        assert 'categorized_count' in batch
        assert 'progress_percent' in batch

        assert batch['total_count'] == 3
        assert batch['categorized_count'] == 1  # Only one has original_category
        assert batch['progress_percent'] == pytest.approx(33.3, rel=0.1)


class TestListBatches:
    """Tests for list_batches function"""

    def test_list_batches_empty(self, test_db, test_user):
        """Test listing batches when there are none"""
        batches = list_batches(test_db, test_user['id'])
        assert batches == []

    def test_list_batches_returns_user_batches(self, test_db, test_user, test_user2, sample_transactions):
        """Test that list_batches only returns batches for the specified user"""
        # Create batch for user 1
        batch1_id = create_batch(test_db, "User 1 Batch", test_user['id'], sample_transactions)

        # Create batch for user 2
        batch2_id = create_batch(test_db, "User 2 Batch", test_user2['id'], sample_transactions)

        # User 1 should only see their batch
        user1_batches = list_batches(test_db, test_user['id'])
        assert len(user1_batches) == 1
        assert user1_batches[0]['id'] == batch1_id

        # User 2 should only see their batch
        user2_batches = list_batches(test_db, test_user2['id'])
        assert len(user2_batches) == 1
        assert user2_batches[0]['id'] == batch2_id

    def test_list_batches_excludes_archived(self, test_db, test_user, sample_transactions):
        """Test that archived batches are excluded by default"""
        # Create two batches
        batch1_id = create_batch(test_db, "Batch 1", test_user['id'], sample_transactions)
        batch2_id = create_batch(test_db, "Batch 2", test_user['id'], sample_transactions)

        # Archive one batch
        archive_batch(test_db, batch2_id)

        # List should only return non-archived batch
        batches = list_batches(test_db, test_user['id'], include_archived=False)
        assert len(batches) == 1
        assert batches[0]['id'] == batch1_id

    def test_list_batches_includes_archived(self, test_db, test_user, sample_transactions):
        """Test that archived batches are included when requested"""
        # Create two batches
        batch1_id = create_batch(test_db, "Batch 1", test_user['id'], sample_transactions)
        batch2_id = create_batch(test_db, "Batch 2", test_user['id'], sample_transactions)

        # Archive one batch
        archive_batch(test_db, batch2_id)

        # List with include_archived=True should return both
        batches = list_batches(test_db, test_user['id'], include_archived=True)
        assert len(batches) == 2

    def test_list_batches_ordered_by_created_at(self, test_db, test_user, sample_transactions):
        """Test that batches are ordered by creation date (newest first)"""
        batch1_id = create_batch(test_db, "Batch 1", test_user['id'], sample_transactions)
        batch2_id = create_batch(test_db, "Batch 2", test_user['id'], sample_transactions)
        batch3_id = create_batch(test_db, "Batch 3", test_user['id'], sample_transactions)

        batches = list_batches(test_db, test_user['id'])

        # Should be in reverse order (newest first)
        assert batches[0]['id'] == batch3_id
        assert batches[1]['id'] == batch2_id
        assert batches[2]['id'] == batch1_id

    def test_list_batches_with_progress(self, test_db, test_user, sample_transactions):
        """Test that listed batches include progress information"""
        create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        batches = list_batches(test_db, test_user['id'])

        assert len(batches) == 1
        batch = batches[0]
        assert 'total_count' in batch
        assert 'categorized_count' in batch
        assert 'progress_percent' in batch


class TestDeleteBatch:
    """Tests for delete_batch function"""

    def test_delete_batch_success(self, test_db, test_user, sample_transactions):
        """Test successfully deleting a batch"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        # Delete batch
        delete_batch(test_db, batch_id, test_user['id'])

        # Verify batch is gone
        batch = get_batch_by_id(test_db, batch_id)
        assert batch is None

    def test_delete_batch_cascades_transactions(self, test_db, test_user, sample_transactions):
        """Test that deleting a batch also deletes its transactions"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        # Verify transactions exist
        cursor = test_db.execute(
            "SELECT COUNT(*) FROM transactions WHERE batch_id = ?",
            (batch_id,)
        )
        assert cursor.fetchone()[0] == 3

        # Delete batch
        delete_batch(test_db, batch_id, test_user['id'])

        # Verify transactions are gone
        cursor = test_db.execute(
            "SELECT COUNT(*) FROM transactions WHERE batch_id = ?",
            (batch_id,)
        )
        assert cursor.fetchone()[0] == 0

    def test_delete_batch_not_found_error(self, test_db, test_user):
        """Test error when deleting non-existent batch"""
        with pytest.raises(ValueError, match="not found"):
            delete_batch(test_db, 99999, test_user['id'])

    def test_delete_batch_ownership_check(self, test_db, test_user, test_user2, sample_transactions):
        """Test that users can only delete their own batches"""
        # Create batch for user 1
        batch_id = create_batch(test_db, "User 1 Batch", test_user['id'], sample_transactions)

        # User 2 should not be able to delete user 1's batch
        with pytest.raises(ValueError, match="not found|permission"):
            delete_batch(test_db, batch_id, test_user2['id'])

        # Batch should still exist
        batch = get_batch_by_id(test_db, batch_id)
        assert batch is not None


class TestArchiveBatch:
    """Tests for archive_batch and unarchive_batch functions"""

    def test_archive_batch(self, test_db, test_user, sample_transactions):
        """Test archiving a batch"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        # Archive batch
        archive_batch(test_db, batch_id)

        # Verify status changed
        batch = get_batch_by_id(test_db, batch_id)
        assert batch['status'] == 'archived'

    def test_unarchive_batch(self, test_db, test_user, sample_transactions):
        """Test unarchiving a batch"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        # Archive then unarchive
        archive_batch(test_db, batch_id)
        unarchive_batch(test_db, batch_id)

        # Verify status changed back
        batch = get_batch_by_id(test_db, batch_id)
        assert batch['status'] == 'in_progress'

    def test_archive_batch_idempotent(self, test_db, test_user, sample_transactions):
        """Test that archiving an already archived batch doesn't error"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        # Archive twice
        archive_batch(test_db, batch_id)
        archive_batch(test_db, batch_id)

        # Should still be archived
        batch = get_batch_by_id(test_db, batch_id)
        assert batch['status'] == 'archived'


class TestCalculateBatchDateRange:
    """Tests for calculate_batch_date_range function"""

    def test_calculate_date_range(self, test_db, test_user, sample_transactions):
        """Test calculating date range for a batch"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        start_date, end_date = calculate_batch_date_range(test_db, batch_id)

        assert start_date == '2024-01-15'
        assert end_date == '2024-01-25'

    def test_calculate_date_range_empty_batch(self, test_db, test_user):
        """Test calculating date range for a batch with no transactions"""
        # Create empty batch (this shouldn't happen in practice but test the edge case)
        cursor = test_db.execute(
            "INSERT INTO batches (name, user_id, status) VALUES (?, ?, 'in_progress')",
            ("Empty Batch", test_user['id'])
        )
        batch_id = cursor.lastrowid
        test_db.commit()

        start_date, end_date = calculate_batch_date_range(test_db, batch_id)

        assert start_date is None
        assert end_date is None


class TestGetBatchProgress:
    """Tests for get_batch_progress function"""

    def test_get_batch_progress(self, test_db, test_user, sample_transactions):
        """Test getting batch progress"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        progress = get_batch_progress(test_db, batch_id)

        assert progress['total_count'] == 3
        assert progress['categorized_count'] == 1  # Only one has original_category
        assert progress['progress_percent'] == pytest.approx(33.3, rel=0.1)

    def test_get_batch_progress_all_categorized(self, test_db, test_user):
        """Test progress when all transactions are categorized"""
        transactions = [
            {
                'date': '2024-01-01',
                'payee': 'Test',
                'amount': -10.0,
                'original_category': 'Food',
                'original_comment': ''
            },
            {
                'date': '2024-01-02',
                'payee': 'Test2',
                'amount': -20.0,
                'original_category': 'Transport',
                'original_comment': ''
            }
        ]

        batch_id = create_batch(test_db, "Test Batch", test_user['id'], transactions)
        progress = get_batch_progress(test_db, batch_id)

        assert progress['total_count'] == 2
        assert progress['categorized_count'] == 2
        assert progress['progress_percent'] == 100.0

    def test_get_batch_progress_none_categorized(self, test_db, test_user):
        """Test progress when no transactions are categorized"""
        transactions = [
            {
                'date': '2024-01-01',
                'payee': 'Test',
                'amount': -10.0,
                'original_category': '',
                'original_comment': ''
            }
        ]

        batch_id = create_batch(test_db, "Test Batch", test_user['id'], transactions)
        progress = get_batch_progress(test_db, batch_id)

        assert progress['total_count'] == 1
        assert progress['categorized_count'] == 0
        assert progress['progress_percent'] == 0.0


class TestVerifyBatchOwnership:
    """Tests for verify_batch_ownership function"""

    def test_verify_ownership_true(self, test_db, test_user, sample_transactions):
        """Test verifying ownership when user owns the batch"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        assert verify_batch_ownership(test_db, batch_id, test_user['id']) is True

    def test_verify_ownership_false(self, test_db, test_user, test_user2, sample_transactions):
        """Test verifying ownership when user doesn't own the batch"""
        batch_id = create_batch(test_db, "Test Batch", test_user['id'], sample_transactions)

        assert verify_batch_ownership(test_db, batch_id, test_user2['id']) is False

    def test_verify_ownership_batch_not_found(self, test_db, test_user):
        """Test verifying ownership for non-existent batch"""
        assert verify_batch_ownership(test_db, 99999, test_user['id']) is False
