import pytest
from app import db
from app.models import User, MenuItem, Order, OrderItem
from datetime import datetime, timedelta

@pytest.fixture
def seed_customer_api_data(app):
    with app.app_context():
        # Clear data
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(MenuItem).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Users
        user1 = User(username='customer1', email='customer1@example.com')
        user1.set_password('password')
        db.session.add(user1)
        db.session.flush()

        # Menu Items
        item1 = MenuItem(name='Burger', description='Classic Burger', price=8.00, stock=5)
        item2 = MenuItem(name='Fries', description='Large Fries', price=3.00, stock=10)
        item3 = MenuItem(name='Drink', description='Soda', price=2.00, stock=0) # Out of stock
        db.session.add_all([item1, item2, item3])
        db.session.commit()

        db.session.refresh(user1)
        db.session.refresh(item1)
        db.session.refresh(item2)
        db.session.refresh(item3)

        return {
            'user1_id': user1.id,
            'item1_id': item1.id, # Burger
            'item2_id': item2.id, # Fries
            'item3_id': item3.id, # Drink (out of stock)
        }

def test_create_order_success(client, seed_customer_api_data):
    user_id = seed_customer_api_data['user1_id']
    item1_id = seed_customer_api_data['item1_id']
    item2_id = seed_customer_api_data['item2_id']

    request_payload = {
        'user_id': user_id,
        'items': [
            {'item_id': item1_id, 'quantity': 1}, # Burger (stock 5)
            {'item_id': item2_id, 'quantity': 2}  # Fries (stock 10)
        ]
    }
    response = client.post('/api/v1/orders', json=request_payload)
    assert response.status_code == 201
    data = response.get_json()
    assert 'Order created successfully' in data['message']
    assert data['order_id'] is not None
    assert data['total_amount'] == 1 * 8.00 + 2 * 3.00 # 8 + 6 = 14.00

    with client.application.app_context():
        order = db.session.get(Order, data['order_id'])
        assert order.user_id == user_id
        assert order.status == 'pending'
        assert len(order.items.all()) == 2

        # Verify stock deduction
        item1 = db.session.get(MenuItem, item1_id)
        item2 = db.session.get(MenuItem, item2_id)
        assert item1.stock == 4 # 5 - 1
        assert item2.stock == 8 # 10 - 2

def test_create_order_insufficient_stock(client, seed_customer_api_data):
    user_id = seed_customer_api_data['user1_id']
    item1_id = seed_customer_api_data['item1_id'] # Burger, stock 5

    request_payload = {
        'user_id': user_id,
        'items': [
            {'item_id': item1_id, 'quantity': 6} # Request 6, stock 5
        ]
    }
    response = client.post('/api/v1/orders', json=request_payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'Not enough stock for Burger' in data['message']

    with client.application.app_context():
        assert Order.query.count() == 0 # No order should be created
        item1 = db.session.get(MenuItem, item1_id)
        assert item1.stock == 5 # Stock should be unchanged

def test_create_order_item_not_found(client, seed_customer_api_data):
    user_id = seed_customer_api_data['user1_id']
    item1_id = seed_customer_api_data['item1_id']

    request_payload = {
        'user_id': user_id,
        'items': [
            {'item_id': item1_id, 'quantity': 1},
            {'item_id': 999, 'quantity': 1} # Non-existent item
        ]
    }
    response = client.post('/api/v1/orders', json=request_payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'MenuItem with ID 999 not found' in data['message']

    with client.application.app_context():
        assert Order.query.count() == 0 # No order should be created

def test_create_order_user_not_found(client, seed_customer_api_data):
    item1_id = seed_customer_api_data['item1_id']

    request_payload = {
        'user_id': 999, # Non-existent user
        'items': [
            {'item_id': item1_id, 'quantity': 1}
        ]
    }
    response = client.post('/api/v1/orders', json=request_payload)
    assert response.status_code == 404
    data = response.get_json()
    assert 'User with ID 999 not found' in data['message']

    with client.application.app_context():
        assert Order.query.count() == 0 # No order should be created

def test_create_order_missing_user_id(client, seed_customer_api_data):
    item1_id = seed_customer_api_data['item1_id']

    request_payload = {
        'items': [
            {'item_id': item1_id, 'quantity': 1}
        ]
    }
    response = client.post('/api/v1/orders', json=request_payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'User ID is required' in data['message']

def test_create_order_missing_items_data(client, seed_customer_api_data):
    user_id = seed_customer_api_data['user1_id']

    request_payload = {
        'user_id': user_id
    }
    response = client.post('/api/v1/orders', json=request_payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'Items data (list of item_id and quantity) is required' in data['message']