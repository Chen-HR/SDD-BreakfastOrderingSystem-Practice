import pytest
from src.models import User, MenuItem, Order, OrderItem
import uuid
import datetime
from decimal import Decimal # Import Decimal

@pytest.fixture(scope='function')
def customer_user(db):
    """Provides a customer user for tests."""
    customer_user_id = uuid.UUID('b0d5c0e0-0a0c-4c0d-8c0b-0d0c0a0d0c0a')
    # Check if user already exists in the current session/transaction
    user = db.session.get(User, customer_user_id)
    if not user:
        user = User(user_id=customer_user_id, email='customer@example.com', role='customer')
        user.set_password('customer_password')
        db.session.add(user)
        db.session.commit() # Commit here to ensure user exists for API calls
    return user

@pytest.fixture(scope='function')
def auth_client(client, customer_user):
    """Provides an authenticated client for tests."""
    login_data = {
        'email': customer_user.email,
        'password': 'customer_password'
    }
    response = client.post('/api/v1/auth/login', json=login_data)
    assert response.status_code == 200
    access_token = response.json['access_token']
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
    return client

def test_create_order_success(auth_client, db, customer_user):
    # Arrange
    menu_item1 = MenuItem(name="Coffee", price=Decimal('5.00'), stock_level=100)
    menu_item2 = MenuItem(name="Sandwich", price=Decimal('10.00'), stock_level=50)
    db.session.add_all([menu_item1, menu_item2])
    db.session.commit()

    items_payload = [
        {'item_id': str(menu_item1.item_id), 'quantity': 2},
        {'item_id': str(menu_item2.item_id), 'quantity': 1}
    ]

    # Act
    response = auth_client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 201
    data = response.json
    assert data['message'] == 'Order created successfully'
    assert 'order_id' in data
    assert data['total_amount'] == '20.00'
    assert data['status'] == 'pending'

    # Verify database state
    order = db.session.get(Order, uuid.UUID(data['order_id']))
    assert order is not None
    assert len(order.items) == 2
    assert menu_item1.stock_level == 98
    assert menu_item2.stock_level == 49

def test_create_order_insufficient_stock(auth_client, db, customer_user):
    # Arrange
    menu_item = MenuItem(name="Test Item", price=Decimal('10.00'), stock_level=5)
    db.session.add(menu_item)
    db.session.commit()

    items_payload = [
        {'item_id': str(menu_item.item_id), 'quantity': 10}
    ]

    # Act
    response = auth_client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Insufficient stock' in response.json['message']
    assert menu_item.stock_level == 5 # Stock should not have changed

def test_create_order_item_not_found(auth_client, db, customer_user):
    # Arrange
    items_payload = [
        {'item_id': str(uuid.uuid4()), 'quantity': 1}
    ]

    # Act
    response = auth_client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Menu item not found' in response.json['message']

def test_create_order_empty_items(auth_client, db, customer_user):
    # Arrange
    items_payload = []

    # Act
    response = auth_client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Items are required to create an order' in response.json['message']

def test_create_order_missing_items_payload(auth_client, db, customer_user):
    # Act
    response = auth_client.post('/api/v1/orders', json={})

    # Assert
    assert response.status_code == 400
    assert 'Items are required to create an order' in response.json['message']

def test_get_menu(client, db):
    # Arrange
    # Ensure a clean slate for menu items
    db.session.query(MenuItem).delete()
    db.session.commit()

    menu_item1 = MenuItem(name="Coffee", price=Decimal('3.50'), stock_level=10, image_url="http://example.com/coffee.jpg")
    menu_item2 = MenuItem(name="Tea", price=Decimal('2.50'), stock_level=0, image_url="http://example.com/tea.jpg") # Should not appear
    menu_item3 = MenuItem(name="Pastry", price=Decimal('4.00'), stock_level=5, image_url="http://example.com/pastry.jpg")
    db.session.add_all([menu_item1, menu_item2, menu_item3])
    db.session.commit()

    # Act
    response = client.get('/api/v1/menu')

    # Assert
    assert response.status_code == 200
    data = response.json
    print(f"DEBUG: Menu API response data: {data}") # Debug print
    assert len(data) == 2 # Only Coffee and Pastry should be returned (stock_level > 0)

    # Verify content of returned items
    item_names = [item['name'] for item in data]
    assert "Coffee" in item_names
    assert "Pastry" in item_names
    assert "Tea" not in item_names

    for item in data:
        if item['name'] == "Coffee":
            assert item['price'] == '3.50'
            assert item['stock_level'] == 10
            assert item['image_url'] == "http://example.com/coffee.jpg"
        elif item['name'] == "Pastry":
            assert item['price'] == '4.00'
            assert item['stock_level'] == 5
            assert item['image_url'] == "http://example.com/pastry.jpg"


