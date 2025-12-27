"""
API integration tests for batch endpoints
"""

import pytest
import io
from app.services.user import create_user
from app.services.batch import create_batch
from app.services.category import import_categories_from_file


# Sample CSV content for testing
ACEMONEY_CSV = b"""transaction,date,payee,category,status,withdrawal,deposit,total,comment
,21.07.2023,DSB NETBUTIK,,,160.0,,,
,27.07.2023,Salary,,,,28511.61,,Monthly
"""

DANSKE_BANK_CSV = b""""Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"
"25.11.2024";"Netto ScanNGo";"-41,80";"98.302,29";"Udf\xc3\xb8rt";"Nej"
"26.11.2024";"Salary";"28.500,00";"126.693,28";"Udf\xc3\xb8rt";"Nej"
"""


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
    """Create a sample batch"""
    transactions = [
        {'date': '2024-01-15', 'payee': 'Store A', 'amount': -100.50,
         'original_category': '', 'original_comment': ''},
        {'date': '2024-01-20', 'payee': 'Salary', 'amount': 5000.00,
         'original_category': '', 'original_comment': ''},
        {'date': '2024-01-25', 'payee': 'Store B', 'amount': -50.00,
         'original_category': '', 'original_comment': ''}
    ]
    return create_batch(test_db, "Test Batch", test_user['id'], transactions)


class TestUploadBatch:
    """Tests for POST /batches endpoint"""

    def test_upload_batch_acemoney_success(self, authenticated_client):
        """Test uploading AceMoney format CSV"""
        files = {'file': ('test.csv', io.BytesIO(ACEMONEY_CSV), 'text/csv')}
        data = {'name': 'July 2023'}

        response = authenticated_client.post(
            "/batches",
            files=files,
            data=data
        )

        assert response.status_code == 201
        batch = response.json()

        assert batch['name'] == 'July 2023'
        assert batch['status'] == 'in_progress'
        assert batch['total_count'] == 2
        assert batch['date_range_start'] == '2023-07-21'
        assert batch['date_range_end'] == '2023-07-27'

    def test_upload_batch_danske_bank_success(self, authenticated_client):
        """Test uploading Danske Bank format CSV"""
        files = {'file': ('test.csv', io.BytesIO(DANSKE_BANK_CSV), 'text/csv')}
        data = {'name': 'November 2024'}

        response = authenticated_client.post(
            "/batches",
            files=files,
            data=data
        )

        assert response.status_code == 201
        batch = response.json()

        assert batch['name'] == 'November 2024'
        assert batch['total_count'] == 2
        assert batch['date_range_start'] == '2024-11-25'
        assert batch['date_range_end'] == '2024-11-26'

    def test_upload_batch_empty_file_error(self, authenticated_client):
        """Test error when uploading empty file"""
        files = {'file': ('empty.csv', io.BytesIO(b''), 'text/csv')}
        data = {'name': 'Empty Batch'}

        response = authenticated_client.post(
            "/batches",
            files=files,
            data=data
        )

        assert response.status_code == 400
        assert "empty" in response.json()['detail'].lower()

    def test_upload_batch_invalid_csv_format_error(self, authenticated_client):
        """Test error when CSV format cannot be detected"""
        invalid_csv = b"wrong,headers,here\ndata,data,data\n"
        files = {'file': ('invalid.csv', io.BytesIO(invalid_csv), 'text/csv')}
        data = {'name': 'Invalid Batch'}

        response = authenticated_client.post(
            "/batches",
            files=files,
            data=data
        )

        assert response.status_code == 400
        assert "detect" in response.json()['detail'].lower()

    def test_upload_batch_missing_name_error(self, authenticated_client):
        """Test error when batch name is missing"""
        files = {'file': ('test.csv', io.BytesIO(ACEMONEY_CSV), 'text/csv')}

        response = authenticated_client.post(
            "/batches",
            files=files
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_upload_batch_requires_auth(self, client):
        """Test that endpoint requires authentication"""
        files = {'file': ('test.csv', io.BytesIO(ACEMONEY_CSV), 'text/csv')}
        data = {'name': 'Test Batch'}

        response = client.post(
            "/batches",
            files=files,
            data=data
        )

        assert response.status_code == 401

    def test_upload_batch_creates_transactions(self, authenticated_client, test_db):
        """Test that uploading a batch creates transactions"""
        files = {'file': ('test.csv', io.BytesIO(ACEMONEY_CSV), 'text/csv')}
        data = {'name': 'Test Batch'}

        response = authenticated_client.post(
            "/batches",
            files=files,
            data=data
        )

        assert response.status_code == 201
        batch_id = response.json()['id']

        # Verify transactions were created
        cursor = test_db.execute(
            "SELECT COUNT(*) FROM transactions WHERE batch_id = ?",
            (batch_id,)
        )
        assert cursor.fetchone()[0] == 2


class TestGetBatches:
    """Tests for GET /batches endpoint"""

    def test_get_batches_success(self, authenticated_client, sample_batch):
        """Test getting list of batches"""
        response = authenticated_client.get("/batches")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Check batch structure
        batch = data[0]
        required_fields = ['id', 'name', 'user_id', 'status', 'date_range_start',
                          'date_range_end', 'created_at', 'total_count',
                          'categorized_count', 'progress_percent']
        for field in required_fields:
            assert field in batch

    def test_get_batches_excludes_archived_by_default(self, authenticated_client, test_db, test_user):
        """Test that archived batches are excluded by default"""
        # Create two batches
        transactions = [{'date': '2024-01-01', 'payee': 'Test', 'amount': -10.0,
                        'original_category': '', 'original_comment': ''}]
        batch1_id = create_batch(test_db, "Batch 1", test_user['id'], transactions)
        batch2_id = create_batch(test_db, "Batch 2", test_user['id'], transactions)

        # Archive one
        test_db.execute("UPDATE batches SET status = 'archived' WHERE id = ?", (batch2_id,))
        test_db.commit()

        response = authenticated_client.get("/batches")

        assert response.status_code == 200
        data = response.json()

        batch_ids = [b['id'] for b in data]
        assert batch1_id in batch_ids
        assert batch2_id not in batch_ids

    def test_get_batches_includes_archived_when_requested(self, authenticated_client, test_db, test_user):
        """Test including archived batches"""
        # Create two batches
        transactions = [{'date': '2024-01-01', 'payee': 'Test', 'amount': -10.0,
                        'original_category': '', 'original_comment': ''}]
        batch1_id = create_batch(test_db, "Batch 1", test_user['id'], transactions)
        batch2_id = create_batch(test_db, "Batch 2", test_user['id'], transactions)

        # Archive one
        test_db.execute("UPDATE batches SET status = 'archived' WHERE id = ?", (batch2_id,))
        test_db.commit()

        response = authenticated_client.get("/batches?include_archived=true")

        assert response.status_code == 200
        data = response.json()

        batch_ids = [b['id'] for b in data]
        assert batch1_id in batch_ids
        assert batch2_id in batch_ids

    def test_get_batches_ordered_by_created_at(self, authenticated_client, test_db, test_user):
        """Test that batches are ordered by creation date (newest first)"""
        transactions = [{'date': '2024-01-01', 'payee': 'Test', 'amount': -10.0,
                        'original_category': '', 'original_comment': ''}]

        batch1_id = create_batch(test_db, "Batch 1", test_user['id'], transactions)
        batch2_id = create_batch(test_db, "Batch 2", test_user['id'], transactions)
        batch3_id = create_batch(test_db, "Batch 3", test_user['id'], transactions)

        response = authenticated_client.get("/batches")

        assert response.status_code == 200
        data = response.json()

        # Should be in reverse order (newest first)
        batch_ids = [b['id'] for b in data]
        assert batch_ids.index(batch3_id) < batch_ids.index(batch2_id)
        assert batch_ids.index(batch2_id) < batch_ids.index(batch1_id)

    def test_get_batches_only_returns_user_batches(self, client, test_db, test_user, test_user2):
        """Test that users only see their own batches"""
        from app.auth import create_session

        transactions = [{'date': '2024-01-01', 'payee': 'Test', 'amount': -10.0,
                        'original_category': '', 'original_comment': ''}]

        # Create batch for user1
        batch1_id = create_batch(test_db, "User 1 Batch", test_user['id'], transactions)
        # Create batch for user2
        batch2_id = create_batch(test_db, "User 2 Batch", test_user2['id'], transactions)

        # User 1 should only see their batch
        session1 = create_session(test_user['id'])
        response = client.get("/batches", cookies={"session_id": session1})
        data = response.json()
        batch_ids = [b['id'] for b in data]
        assert batch1_id in batch_ids
        assert batch2_id not in batch_ids

        # User 2 should only see their batch
        session2 = create_session(test_user2['id'])
        response = client.get("/batches", cookies={"session_id": session2})
        data = response.json()
        batch_ids = [b['id'] for b in data]
        assert batch2_id in batch_ids
        assert batch1_id not in batch_ids

    def test_get_batches_requires_auth(self, client):
        """Test that endpoint requires authentication"""
        response = client.get("/batches")

        assert response.status_code == 401


class TestGetBatch:
    """Tests for GET /batches/{id} endpoint"""

    def test_get_batch_success(self, authenticated_client, sample_batch):
        """Test getting a specific batch"""
        response = authenticated_client.get(f"/batches/{sample_batch}")

        assert response.status_code == 200
        batch = response.json()

        assert batch['id'] == sample_batch
        assert 'name' in batch
        assert 'progress_percent' in batch

    def test_get_batch_not_found(self, authenticated_client):
        """Test getting non-existent batch"""
        response = authenticated_client.get("/batches/99999")

        assert response.status_code == 404

    def test_get_batch_ownership_check(self, client, test_db, test_user2, sample_batch):
        """Test that users can only get their own batches"""
        from app.auth import create_session

        session_id = create_session(test_user2['id'])
        response = client.get(
            f"/batches/{sample_batch}",
            cookies={"session_id": session_id}
        )

        assert response.status_code == 404

    def test_get_batch_requires_auth(self, client, sample_batch):
        """Test that endpoint requires authentication"""
        response = client.get(f"/batches/{sample_batch}")

        assert response.status_code == 401


class TestDeleteBatch:
    """Tests for DELETE /batches/{id} endpoint"""

    def test_delete_batch_success(self, authenticated_client, sample_batch):
        """Test deleting a batch"""
        response = authenticated_client.delete(f"/batches/{sample_batch}")

        assert response.status_code == 200
        assert "deleted" in response.json()['message'].lower()

        # Verify batch is gone
        response = authenticated_client.get(f"/batches/{sample_batch}")
        assert response.status_code == 404

    def test_delete_batch_not_found(self, authenticated_client):
        """Test deleting non-existent batch"""
        response = authenticated_client.delete("/batches/99999")

        assert response.status_code == 404

    def test_delete_batch_ownership_check(self, client, test_db, test_user2, sample_batch):
        """Test that users can only delete their own batches"""
        from app.auth import create_session

        session_id = create_session(test_user2['id'])
        response = client.delete(
            f"/batches/{sample_batch}",
            cookies={"session_id": session_id}
        )

        assert response.status_code == 404

    def test_delete_batch_requires_auth(self, client, sample_batch):
        """Test that endpoint requires authentication"""
        response = client.delete(f"/batches/{sample_batch}")

        assert response.status_code == 401


class TestArchiveBatch:
    """Tests for POST /batches/{id}/archive endpoint"""

    def test_archive_batch_success(self, authenticated_client, sample_batch):
        """Test archiving a batch"""
        response = authenticated_client.post(f"/batches/{sample_batch}/archive")

        assert response.status_code == 200
        assert "archived" in response.json()['message'].lower()

        # Verify batch is archived
        response = authenticated_client.get(f"/batches/{sample_batch}")
        assert response.json()['status'] == 'archived'

    def test_archive_batch_not_found(self, authenticated_client):
        """Test archiving non-existent batch"""
        response = authenticated_client.post("/batches/99999/archive")

        assert response.status_code == 404

    def test_archive_batch_ownership_check(self, client, test_db, test_user2, sample_batch):
        """Test that users can only archive their own batches"""
        from app.auth import create_session

        session_id = create_session(test_user2['id'])
        response = client.post(
            f"/batches/{sample_batch}/archive",
            cookies={"session_id": session_id}
        )

        assert response.status_code == 404

    def test_archive_batch_requires_auth(self, client, sample_batch):
        """Test that endpoint requires authentication"""
        response = client.post(f"/batches/{sample_batch}/archive")

        assert response.status_code == 401


class TestUnarchiveBatch:
    """Tests for POST /batches/{id}/unarchive endpoint"""

    def test_unarchive_batch_success(self, authenticated_client, test_db, sample_batch):
        """Test unarchiving a batch"""
        # Archive first
        test_db.execute("UPDATE batches SET status = 'archived' WHERE id = ?", (sample_batch,))
        test_db.commit()

        response = authenticated_client.post(f"/batches/{sample_batch}/unarchive")

        assert response.status_code == 200
        assert "unarchived" in response.json()['message'].lower()

        # Verify batch is unarchived
        response = authenticated_client.get(f"/batches/{sample_batch}")
        assert response.json()['status'] == 'in_progress'

    def test_unarchive_batch_not_found(self, authenticated_client):
        """Test unarchiving non-existent batch"""
        response = authenticated_client.post("/batches/99999/unarchive")

        assert response.status_code == 404

    def test_unarchive_batch_requires_auth(self, client, sample_batch):
        """Test that endpoint requires authentication"""
        response = client.post(f"/batches/{sample_batch}/unarchive")

        assert response.status_code == 401


class TestDownloadBatch:
    """Tests for GET /batches/{id}/download endpoint"""

    def test_download_batch_success(self, authenticated_client, sample_batch):
        """Test downloading a batch as CSV"""
        response = authenticated_client.get(f"/batches/{sample_batch}/download")

        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/csv; charset=utf-8'
        assert 'content-disposition' in response.headers
        assert 'attachment' in response.headers['content-disposition']

        # Verify CSV content
        csv_content = response.content
        assert b'transaction,date,payee,category' in csv_content

    def test_download_batch_archives_after_download(self, authenticated_client, sample_batch):
        """Test that batch is archived after download"""
        response = authenticated_client.get(f"/batches/{sample_batch}/download")

        assert response.status_code == 200

        # Verify batch is now archived
        response = authenticated_client.get(f"/batches/{sample_batch}")
        assert response.json()['status'] == 'archived'

    def test_download_batch_not_found(self, authenticated_client):
        """Test downloading non-existent batch"""
        response = authenticated_client.get("/batches/99999/download")

        assert response.status_code == 404

    def test_download_batch_ownership_check(self, client, test_db, test_user2, sample_batch):
        """Test that users can only download their own batches"""
        from app.auth import create_session

        session_id = create_session(test_user2['id'])
        response = client.get(
            f"/batches/{sample_batch}/download",
            cookies={"session_id": session_id}
        )

        assert response.status_code == 404

    def test_download_batch_requires_auth(self, client, sample_batch):
        """Test that endpoint requires authentication"""
        response = client.get(f"/batches/{sample_batch}/download")

        assert response.status_code == 401


class TestBatchResponseModel:
    """Tests for batch response model validation"""

    def test_batch_response_has_all_fields(self, authenticated_client, sample_batch):
        """Test that batch response includes all required fields"""
        response = authenticated_client.get(f"/batches/{sample_batch}")

        assert response.status_code == 200
        batch = response.json()

        required_fields = ['id', 'name', 'user_id', 'status', 'date_range_start',
                          'date_range_end', 'created_at', 'updated_at',
                          'total_count', 'categorized_count', 'progress_percent']
        for field in required_fields:
            assert field in batch

    def test_batch_progress_fields_are_numbers(self, authenticated_client, sample_batch):
        """Test that progress fields are numeric"""
        response = authenticated_client.get(f"/batches/{sample_batch}")

        assert response.status_code == 200
        batch = response.json()

        assert isinstance(batch['total_count'], int)
        assert isinstance(batch['categorized_count'], int)
        assert isinstance(batch['progress_percent'], (int, float))
        assert 0 <= batch['progress_percent'] <= 100
