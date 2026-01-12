import pytest
from src.models import User, MenuItem, Order, OrderItem
import uuid
import datetime

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

def test_create_order_success(client, db, customer_user):
    # Arrange
    menu_item1 = MenuItem(name="Coffee", price=5.00, stock_level=100)
    menu_item2 = MenuItem(name="Sandwich", price=10.00, stock_level=50)
    db.session.add_all([menu_item1, menu_item2])
    db.session.commit()

    items_payload = [
        {'item_id': str(menu_item1.item_id), 'quantity': 2},
        {'item_id': str(menu_item2.item_id), 'quantity': 1}
    ]

    # Act
    response = client.post('/api/v1/orders', json={'items': items_payload})

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

def test_create_order_insufficient_stock(client, db, customer_user):
    # Arrange
    menu_item = MenuItem(name="Test Item", price=10.00, stock_level=5)
    db.session.add(menu_item)
    db.session.commit()

    items_payload = [
        {'item_id': str(menu_item.item_id), 'quantity': 10}
    ]

    # Act
    response = client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Insufficient stock' in response.json['message']
    assert menu_item.stock_level == 5 # Stock should not have changed

def test_create_order_item_not_found(client, db, customer_user):
    # Arrange
    items_payload = [
        {'item_id': str(uuid.uuid4()), 'quantity': 1}
    ]

    # Act
    response = client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Menu item not found' in response.json['message']

def test_create_order_empty_items(client, db, customer_user):
    # Arrange
    items_payload = []

    # Act
    response = client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Items are required to create an order' in response.json['message']

def test_create_order_missing_items_payload(client, db, customer_user):
    # Act
    response = client.post('/api/v1/orders', json={})

    # Assert
    assert response.status_code == 400
    assert 'Items are required to create an order' in response.json['message']

