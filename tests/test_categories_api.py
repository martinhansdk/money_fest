"""
API integration tests for category endpoints
"""

import pytest
from app.services.category import import_categories_from_file
from app.services.user import create_user


@pytest.fixture
def categories(test_db):
    """Import test categories"""
    import_categories_from_file(test_db, '/app/categories.txt')


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user_id = create_user(test_db, "testuser", "password123")
    return {'id': user_id, 'username': 'testuser'}


class TestGetCategories:
    """Tests for GET /categories endpoint"""

    def test_get_categories_success(self, authenticated_client, categories):
        """Test getting all categories"""
        response = authenticated_client.get("/categories")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check structure
        category = data[0]
        assert 'id' in category
        assert 'name' in category
        assert 'full_path' in category
        assert 'usage_count' in category

    def test_get_categories_requires_auth(self, client, categories):
        """Test that endpoint requires authentication"""
        response = client.get("/categories")

        assert response.status_code == 401

    def test_get_categories_sorted_by_full_path(self, authenticated_client, categories):
        """Test that categories are sorted by full_path"""
        response = authenticated_client.get("/categories")

        assert response.status_code == 200
        data = response.json()

        full_paths = [c['full_path'] for c in data]
        assert full_paths == sorted(full_paths)

    def test_get_categories_empty_database(self, authenticated_client):
        """Test getting categories when none exist"""
        response = authenticated_client.get("/categories")

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestGetFrequentCategories:
    """Tests for GET /categories/frequent endpoint"""

    def test_get_frequent_categories_default_limit(self, authenticated_client, categories, test_db):
        """Test getting frequent categories with default limit"""
        # Increment usage count for some categories
        test_db.execute("UPDATE categories SET usage_count = 10 WHERE full_path = 'Food:Groceries'")
        test_db.execute("UPDATE categories SET usage_count = 5 WHERE full_path = 'Transport:Gas'")
        test_db.commit()

        response = authenticated_client.get("/categories/frequent")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 15  # Default limit
        assert all(c['usage_count'] > 0 for c in data)

    def test_get_frequent_categories_custom_limit(self, authenticated_client, categories, test_db):
        """Test getting frequent categories with custom limit"""
        # Increment usage count for multiple categories
        for i in range(20):
            test_db.execute(
                "UPDATE categories SET usage_count = ? WHERE id = ?",
                (i + 1, i + 1)
            )
        test_db.commit()

        response = authenticated_client.get("/categories/frequent?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert len(data) <= 5

    def test_get_frequent_categories_ordered_by_usage(self, authenticated_client, categories, test_db):
        """Test that frequent categories are ordered by usage count (descending)"""
        # Set specific usage counts
        test_db.execute("UPDATE categories SET usage_count = 100 WHERE full_path = 'Food:Groceries'")
        test_db.execute("UPDATE categories SET usage_count = 50 WHERE full_path = 'Transport:Gas'")
        test_db.execute("UPDATE categories SET usage_count = 25 WHERE full_path = 'Utilities:Electric'")
        test_db.commit()

        response = authenticated_client.get("/categories/frequent")

        assert response.status_code == 200
        data = response.json()

        if len(data) >= 3:
            # Check that usage counts are in descending order
            usage_counts = [c['usage_count'] for c in data]
            assert usage_counts == sorted(usage_counts, reverse=True)

    def test_get_frequent_categories_requires_auth(self, client, categories):
        """Test that endpoint requires authentication"""
        response = client.get("/categories/frequent")

        assert response.status_code == 401

    def test_get_frequent_categories_limit_validation(self, authenticated_client, categories):
        """Test limit parameter validation"""
        # Limit too low
        response = authenticated_client.get("/categories/frequent?limit=0")
        assert response.status_code == 422

        # Limit too high
        response = authenticated_client.get("/categories/frequent?limit=100")
        assert response.status_code == 422

        # Valid limits
        response = authenticated_client.get("/categories/frequent?limit=1")
        assert response.status_code == 200

        response = authenticated_client.get("/categories/frequent?limit=50")
        assert response.status_code == 200

    def test_get_frequent_categories_excludes_unused(self, authenticated_client, categories, test_db):
        """Test that categories with usage_count = 0 are excluded"""
        # Set one category to have usage, rest at 0
        test_db.execute("UPDATE categories SET usage_count = 0")
        test_db.execute("UPDATE categories SET usage_count = 10 WHERE full_path = 'Food:Groceries'")
        test_db.commit()

        response = authenticated_client.get("/categories/frequent")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]['full_path'] == 'Food:Groceries'
        assert data[0]['usage_count'] == 10


class TestCategoryResponseModel:
    """Tests for category response model validation"""

    def test_category_response_has_all_fields(self, authenticated_client, categories):
        """Test that category response includes all required fields"""
        response = authenticated_client.get("/categories")

        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            category = data[0]
            required_fields = ['id', 'name', 'parent', 'full_path', 'usage_count', 'created_at']
            for field in required_fields:
                assert field in category

    def test_category_parent_can_be_null(self, authenticated_client, categories):
        """Test that category parent field can be null for top-level categories"""
        response = authenticated_client.get("/categories")

        assert response.status_code == 200
        data = response.json()

        # Find a top-level category (one without a colon)
        top_level = [c for c in data if ':' not in c['full_path']]

        if len(top_level) > 0:
            assert top_level[0]['parent'] is None
