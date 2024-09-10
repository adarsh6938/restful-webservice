import pytest
import os
from fastapi.testclient import TestClient
from app.main import app, get_db  # Import your FastAPI app and dependencies
from app.database import Base, SessionLocal, engine

# Set environment variables for the test
os.environ["DATABASE_URL"] = "postgresql://customeruser:password@localhost:5432/customerdb"
os.environ["PYTHONPATH"] = "/app"

# TestClient to interact with the FastAPI app
client = TestClient(app)

# Set up the database before running tests
@pytest.fixture(scope="module")
def setup_database():
    # Drop and recreate the tables to have a clean start for testing
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Create a session for this module's tests
    db = SessionLocal()
    yield db
    db.close()

# Fixtures to generate test data
@pytest.fixture
def new_customer():
    return {
        "first_name": "John",
        "middle_name": "A",
        "last_name": "Doe",
        "prefix": "Mr.",
        "suffix": "Jr.",
        "email": "john.doe@example.com",
        "phone_number": "123-456-7890"
    }

@pytest.fixture
def updated_customer():
    return {
        "first_name": "Jane",
        "middle_name": "B",
        "last_name": "Doe",
        "prefix": "Ms.",
        "suffix": "Sr.",
        "email": "jane.doe@example.com",
        "phone_number": "098-765-4321"
    }

# Test cases

# 1. Test creating a customer
def test_create_customer(new_customer, setup_database):
    response = client.post("/v1/customers/", json=new_customer, auth=("admin", "password"))
    assert response.status_code == 200
    assert response.json()["email"] == new_customer["email"]

# 2. Test retrieving all customers
def test_read_customers(new_customer, setup_database):
    # Ensure at least one customer exists
    client.post("/v1/customers/", json=new_customer, auth=("admin", "password"))

    # Retrieve all customers
    response = client.get("/v1/customers/", auth=("admin", "password"))
    assert response.status_code == 200
    assert len(response.json()) > 0  # Ensure at least one customer exists

# 3. Test retrieving a customer by ID
def test_read_customer_by_id(new_customer, setup_database):
    # Create a customer first
    create_response = client.post("/v1/customers/", json=new_customer, auth=("admin", "password"))
    customer_id = create_response.json()["id"]

    # Retrieve the customer by ID
    response = client.get(f"/v1/customers/{customer_id}", auth=("admin", "password"))
    assert response.status_code == 200
    assert response.json()["id"] == customer_id

# 4. Test retrieving a customer by email
def test_read_customer_by_email(new_customer, setup_database):
    # Create a customer first
    client.post("/v1/customers/", json=new_customer, auth=("admin", "password"))

    # Retrieve the customer by email
    response = client.get(f"/v1/customers/email/{new_customer['email']}", auth=("admin", "password"))
    assert response.status_code == 200
    assert response.json()["email"] == new_customer["email"]

# 5. Test updating a customer
def test_update_customer(new_customer, updated_customer, setup_database):
    # Create a customer first
    create_response = client.post("/v1/customers/", json=new_customer, auth=("admin", "password"))
    customer_id = create_response.json()["id"]

    # Update the customer
    response = client.put(f"/v1/customers/{customer_id}", json=updated_customer, auth=("admin", "password"))
    assert response.status_code == 200
    assert response.json()["email"] == updated_customer["email"]
    assert response.json()["first_name"] == updated_customer["first_name"]

# 6. Test deleting a customer
def test_delete_customer(new_customer, setup_database):
    # Create a customer first
    create_response = client.post("/v1/customers/", json=new_customer, auth=("admin", "password"))
    customer_id = create_response.json()["id"]

    # Delete the customer
    response = client.delete(f"/v1/customers/{customer_id}", auth=("admin", "password"))
    assert response.status_code == 200

    # Verify the customer no longer exists
    get_response = client.get(f"/v1/customers/{customer_id}", auth=("admin", "password"))
    assert get_response.status_code == 404
