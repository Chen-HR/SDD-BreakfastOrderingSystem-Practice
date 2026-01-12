import pytest
from src.models import User, MenuItem, Order, OrderItem
import uuid
import datetime
from flask_jwt_extended import create_access_token
from decimal import Decimal # Needed for creating MenuItems

# --- Fixtures for Admin Tests ---

@pytest.fixture(scope='function')
def admin_user(db):
    """Provides an admin user for tests with a unique email."""
    user_id = uuid.uuid4()
    email = f'admin_{user_id}@test.com'
    user = User(user_id=user_id, email=email, role='admin')
    user.set_password('admin_password')
    db.session.add(user)
    db.session.flush() # Flush to assign primary keys for relationships if needed
    return user

@pytest.fixture(scope='function')
def login_admin_user(client, admin_user):
    """Logs in the admin user and returns their JWT token."""
    login_data = {
        'email': admin_user.email,
        'password': 'admin_password'
    }
    response = client.post('/api/v1/auth/login', json=login_data)
    assert response.status_code == 200
    return response.json['access_token']

@pytest.fixture(scope='function')
def admin_auth_client(client, login_admin_user):
    """Provides an authenticated client for an admin user."""
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {login_admin_user}'
    return client

@pytest.fixture(scope='function')
def customer_user_for_admin_tests(db):
    """Provides a customer user for admin-related tests with a unique email."""
    user_id = uuid.uuid4()
    email = f'customer_{user_id}@test.com'
    user = User(user_id=user_id, email=email, role='customer')
    user.set_password('customer_password')
    db.session.add(user)
    db.session.flush()
    return user

@pytest.fixture(scope='function')
def login_customer_user_for_admin_tests(client, customer_user_for_admin_tests):
    """Logs in a customer user for admin-related tests and returns their JWT token."""
    login_data = {
        'email': customer_user_for_admin_tests.email,
        'password': 'customer_password'
    }
    response = client.post('/api/v1/auth/login', json=login_data)
    assert response.status_code == 200
    return response.json['access_token']

@pytest.fixture(scope='function')
def customer_auth_client_for_admin_tests(client, login_customer_user_for_admin_tests):
    """Provides an authenticated client for a customer user for admin-related tests."""
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {login_customer_user_for_admin_tests}'
    return client

# --- Helper to create menu items and orders for tests ---
def create_test_order(db, user_id, menu_item_specs, order_number_suffix="001"):
    order_number = f"ORD-{uuid.uuid4()}-{order_number_suffix}" # Ensure unique order number
    total_amount = Decimal('0.00')
    order_items_list = []

    for item_spec in menu_item_specs:
        menu_item = MenuItem(name=item_spec['name'], price=item_spec['price'], stock_level=item_spec['stock_level'])
        db.session.add(menu_item)
        db.session.flush() # Flush to get item_id before creating order item

        quantity = item_spec.get('quantity', 1)
        subtotal = menu_item.price * quantity
        total_amount += subtotal

        order_items_list.append(OrderItem(
            menu_item_id=menu_item.item_id,
            quantity=quantity,
            unit_price=menu_item.price,
            subtotal=subtotal
        ))
    
    order = Order(
        user_id=user_id,
        order_number=order_number,
        total_amount=total_amount,
        delivery_address='Test Address',
        status='pending'
    )
    order.items = order_items_list
    db.session.add(order)
    db.session.flush() # Flush to ensure order_id is assigned for potential child relationships
    return order, menu_item_specs


# --- Tests for Admin API endpoints ---

# Test GET /api/v1/admin/orders
def test_get_admin_orders_no_token(client):
    response = client.get('/api/v1/admin/orders')
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.json['msg']

def test_get_admin_orders_invalid_token(client):
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer invalid_token'
    response = client.get('/api/v1/admin/orders')
    assert response.status_code == 401
    assert "Signature verification failed" in response.json['msg']

def test_get_admin_orders_customer_token(customer_auth_client_for_admin_tests):
    response = customer_auth_client_for_admin_tests.get('/api/v1/admin/orders')
    assert response.status_code == 403
    assert "Administration rights required" in response.json['msg']

def test_get_admin_orders_admin_token_empty(admin_auth_client, db):
    # This test verifies that even with an admin token, if no orders exist, it returns empty
    # We need to ensure no orders from other tests are visible here due to session flush/commit issues
    # or that the test cleans up. Assuming default pytest-flask-sqlalchemy behavior with transaction.
    response = admin_auth_client.get('/api/v1/admin/orders')
    assert response.status_code == 200
    assert response.json == []

def test_get_admin_orders_admin_token_with_data(admin_auth_client, db, admin_user):
    # Arrange: Create an order
    order, _ = create_test_order(db, admin_user.user_id, [
        {'name': "Coffee", 'price': Decimal('5.00'), 'stock_level': 100, 'quantity': 1},
        {'name': "Sandwich", 'price': Decimal('10.00'), 'stock_level': 50, 'quantity': 1}
    ], "GET-DATA")

    # Act
    response = admin_auth_client.get('/api/v1/admin/orders')

    # Assert
    assert response.status_code == 200
    data = response.json
    assert len(data) == 1 # Only one order created in this test
    
    order_data = data[0]
    assert order_data['order_id'] == str(order.order_id)
    assert order_data['order_number'] == order.order_number
    assert order_data['total_amount'] == str(order.total_amount) # Decimal serialized to string
    assert order_data['status'] == 'pending'
    assert len(order_data['items']) == 2

    item_names = [item['name'] for item in order_data['items']]
    assert 'Coffee' in item_names
    assert 'Sandwich' in item_names

# Test PUT /api/v1/admin/orders/<uuid:order_id>/status
def test_update_order_status_no_token(client, db, customer_user_for_admin_tests):
    # Arrange: Create an order
    order, _ = create_test_order(db, customer_user_for_admin_tests.user_id, [{'name': "Item to Update", 'price': Decimal('10.00'), 'stock_level': 10}])
    
    # Act
    response = client.put(f'/api/v1/admin/orders/{order.order_id}/status', json={'status': 'in_progress'})
    
    # Assert
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.json['msg']

def test_update_order_status_customer_token(customer_auth_client_for_admin_tests, db, customer_user_for_admin_tests):
    # Arrange: Create an order
    order, _ = create_test_order(db, customer_user_for_admin_tests.user_id, [{'name': "Item to Update", 'price': Decimal('10.00'), 'stock_level': 10}])

    # Act
    response = customer_auth_client_for_admin_tests.put(f'/api/v1/admin/orders/{order.order_id}/status', json={'status': 'in_progress'})
    
    # Assert
    assert response.status_code == 403
    assert "Administration rights required" in response.json['msg']

def test_update_order_status_admin_token_success(admin_auth_client, db, admin_user, customer_user_for_admin_tests):
    # Arrange: Create an order owned by a customer, to be updated by admin
    order, _ = create_test_order(db, customer_user_for_admin_tests.user_id, [{'name': "Item to Update", 'price': Decimal('10.00'), 'stock_level': 10}], "UPDATE-SUCCESS")

    new_status = 'in_progress'
    
    # Act
    response = admin_auth_client.put(f'/api/v1/admin/orders/{order.order_id}/status', json={'status': new_status})

    # Assert
    assert response.status_code == 200
    assert response.json['status'] == new_status
    updated_order = db.session.get(Order, order.order_id)
    assert updated_order.status == new_status

def test_update_order_status_order_not_found_admin_token(admin_auth_client, db):
    # Arrange
    non_existent_id = uuid.uuid4()
    new_status = 'delivered'

    # Act
    response = admin_auth_client.put(f'/api/v1/admin/orders/{non_existent_id}/status', json={'status': new_status})

    # Assert
    assert response.status_code == 404
    assert 'Order not found' in response.json['message']

def test_update_order_status_invalid_status_admin_token(admin_auth_client, db, customer_user_for_admin_tests):
    # Arrange
    order, _ = create_test_order(db, customer_user_for_admin_tests.user_id, [{'name': "Invalid Status Item", 'price': Decimal('5.00'), 'stock_level': 5}], "INVALID-STATUS")

    invalid_status = 'invalid_state'

    # Act
    response = admin_auth_client.put(f'/api/v1/admin/orders/{order.order_id}/status', json={'status': invalid_status})

    # Assert
    assert response.status_code == 400
    assert 'Invalid status' in response.json['message']

def test_update_order_status_missing_payload_admin_token(admin_auth_client, db, customer_user_for_admin_tests):
    # Arrange
    order, _ = create_test_order(db, customer_user_for_admin_tests.user_id, [{'name': "Missing Payload Item", 'price': Decimal('12.00'), 'stock_level': 12}], "MISSING-PAYLOAD")

    # Act
    response = admin_auth_client.put(f'/api/v1/admin/orders/{order.order_id}/status', json={})

    # Assert
    assert response.status_code == 400
    assert 'Status is required' in response.json['message']
