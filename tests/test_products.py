import pytest
from tests.conftest import client, test_user
@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for protected endpoints."""
    client.post("/register", json=test_user)
    response = client.post(
        "/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
def test_create_product(client, auth_headers):
    """Test creating a product."""
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 99.99,
        "stock": 10
    }
    response = client.post("/products", json=product_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == product_data["price"]
def test_list_products(client, auth_headers):
    """Test listing products."""
    # Create a product first
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 99.99,
        "stock": 10
    }
    client.post("/products", json=product_data, headers=auth_headers)
    # List products
    response = client.get("/products", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == product_data["name"]
def test_get_product(client, auth_headers):
    """Test getting a single product."""
    # Create a product
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 99.99,
        "stock": 10
    }
    create_response = client.post("/products", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]
    # Get the product
    response = client.get(f"/products/{product_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == product_data["name"]
def test_get_product_not_found(client, auth_headers):
    """Test getting a non-existent product."""
    response = client.get("/products/99999", headers=auth_headers)
    assert response.status_code == 404
def test_update_product(client, auth_headers):
    """Test updating a product."""
    # Create a product
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 99.99,
        "stock": 10
    }
    create_response = client.post("/products", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]
    # Update the product
    update_data = {
        "name": "Updated Product",
        "price": 149.99
    }
    response = client.patch(f"/products/{product_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == update_data["name"]
    assert response.json()["price"] == update_data["price"]
def test_delete_product(client, auth_headers):
    """Test deleting a product."""
    # Create a product
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 99.99,
        "stock": 10
    }
    create_response = client.post("/products", json=product_data, headers=auth_headers)
    product_id = create_response.json()["id"]
    # Delete the product
    response = client.delete(f"/products/{product_id}", headers=auth_headers)
    assert response.status_code == 204
    # Verify deletion
    response = client.get(f"/products/{product_id}", headers=auth_headers)
    assert response.status_code == 404
Step 6: Write Error Handling Tests
# tests/test_errors.py
import pytest
from tests.conftest import client, test_user
def test_404_error(client):
    """Test 404 error handling."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == True
    assert "message" in data
def test_validation_error(client, auth_headers):
    """Test validation error handling."""
    # Create a product with invalid data
    product_data = {
        "name": "",  # Empty name should fail
        "description": "This is a test product",
        "price": -10,  # Negative price should fail
        "stock": -5  # Negative stock should fail
    }
    response = client.post("/products", json=product_data, headers=auth_headers)
    assert response.status_code in [400, 422]  # Validation error
    data = response.json()
    assert data["error"] == True
def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints."""
    response = client.get("/users")
    assert response.status_code == 401  # Unauthorized
def test_forbidden_access(client, test_user, auth_headers):
    """Test forbidden access to admin-only endpoints."""
    # Regular user (not admin) tries to access admin endpoint
    response = client.get("/users", headers=auth_headers)
    assert response.status_code == 403  # Forbidden