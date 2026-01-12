import pytest
from src.models import User, MenuItem, Order, OrderItem
import uuid
import datetime
from decimal import Decimal # Import Decimal
from flask_jwt_extended import create_access_token # Needed for creating test tokens if ever directly used

@pytest.fixture(scope='function')
def customer_user(db):
    """Provides a customer user for tests."""
    user_id = uuid.uuid4()
    email = f'customer_{user_id}@example.com' # Unique email
    user = User(user_id=user_id, email=email, role='customer')
    user.set_password('customer_password')
    db.session.add(user)
    db.session.commit() # Commit here to ensure user exists for API calls
    return user

@pytest.fixture(scope='function')
def login_customer_user(client, customer_user):
    """Logs in the customer user and returns their JWT token."""
    login_data = {
        'email': customer_user.email,
        'password': 'customer_password'
    }
    response = client.post('/api/v1/auth/login', json=login_data)
    assert response.status_code == 200
    return response.json['access_token']

@pytest.fixture(scope='function')
def customer_auth_client(client, login_customer_user):
    """Provides an authenticated client for tests."""
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {login_customer_user}'
    return client

def test_create_order_success(customer_auth_client, db, customer_user):
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
    response = customer_auth_client.post('/api/v1/orders', json={'items': items_payload})

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

def test_create_order_insufficient_stock(customer_auth_client, db, customer_user):
    # Arrange
    menu_item = MenuItem(name="Test Item", price=Decimal('10.00'), stock_level=5)
    db.session.add(menu_item)
    db.session.commit()

    items_payload = [
        {'item_id': str(menu_item.item_id), 'quantity': 10}
    ]

    # Act
    response = customer_auth_client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Insufficient stock' in response.json['message']
    assert menu_item.stock_level == 5 # Stock should not have changed

def test_create_order_item_not_found(customer_auth_client, db, customer_user):
    # Arrange
    items_payload = [
        {'item_id': str(uuid.uuid4()), 'quantity': 1}
    ]

    # Act
    response = customer_auth_client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Menu item not found' in response.json['message']

def test_create_order_empty_items(customer_auth_client, db, customer_user):
    # Arrange
    items_payload = []

    # Act
    response = customer_auth_client.post('/api/v1/orders', json={'items': items_payload})

    # Assert
    assert response.status_code == 400
    assert 'Items are required to create an order' in response.json['message']

def test_create_order_missing_items_payload(customer_auth_client, db, customer_user):
    # Act
    response = customer_auth_client.post('/api/v1/orders', json={})

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

def test_register_user_success(client, db):
    # Arrange
    register_data = {
        'email': 'newuser@example.com',
        'password': 'strongpassword'
    }

    # Act
    response = client.post('/api/v1/auth/register', json=register_data)

    # Assert
    assert response.status_code == 201
    assert response.json['msg'] == 'User registered successfully'
    assert 'user_id' in response.json

    user = db.session.scalar(db.select(User).filter_by(email='newuser@example.com'))
    assert user is not None
    assert user.check_password('strongpassword')
    assert user.role == 'customer'

def test_register_user_existing_email(client, db, customer_user):
    # Arrange (customer_user fixture already creates a user)
    register_data = {
        'email': customer_user.email, # Use existing email
        'password': 'anotherpassword'
    }

    # Act
    response = client.post('/api/v1/auth/register', json=register_data)

    # Assert
    assert response.status_code == 409
    assert response.json['msg'] == 'User with that email already exists'

def test_register_user_missing_fields(client, db):
    # Arrange - missing password
    register_data_missing_password = {
        'email': 'missingpass@example.com'
    }
    # Arrange - missing email
    register_data_missing_email = {
        'password': 'somepassword'
    }

    # Act 1 - missing password
    response_missing_password = client.post('/api/v1/auth/register', json=register_data_missing_password)
    # Assert 1
    assert response_missing_password.status_code == 400
    assert response_missing_password.json['msg'] == 'Missing email or password'

    # Act 2 - missing email
    response_missing_email = client.post('/api/v1/auth/register', json=register_data_missing_email)
    # Assert 2
    assert response_missing_email.status_code == 400
    assert response_missing_email.json['msg'] == 'Missing email or password'

def test_register_user_invalid_email(client, db):
    # Arrange
    register_data = {
        'email': 'invalid-email',
        'password': 'somepassword'
    }

    # Act
    response = client.post('/api/v1/auth/register', json=register_data)

    # Assert
    assert response.status_code == 400
    assert response.json['msg'] == 'Invalid email format'

def test_register_user_short_password(client, db):
    # Arrange
    register_data = {
        'email': 'shortpass@example.com',
        'password': 'short' # less than 6 characters
    }

    # Act
    response = client.post('/api/v1/auth/register', json=register_data)

    # Assert
    assert response.status_code == 400
    assert response.json['msg'] == 'Password must be at least 6 characters long'

# --- Helper to create menu items and orders for tests ---
def create_order_for_test(db, user_id, menu_item_specs, order_number_suffix="001", commit=True):
    order_number = f"CUST-ORD-{uuid.uuid4()}-{order_number_suffix}" # Ensure unique order number
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
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return order, menu_item_specs

# --- Tests for GET /api/v1/orders (Customer Order List) ---

def test_get_customer_orders_no_token(client):
    response = client.get('/api/v1/orders')
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.json['msg']

def test_get_customer_orders_empty(customer_auth_client):
    response = customer_auth_client.get('/api/v1/orders')
    assert response.status_code == 200
    assert response.json == []

def test_get_customer_orders_with_data(customer_auth_client, db, customer_user):
    # Arrange: Create orders for the customer
    order1, _ = create_order_for_test(db, customer_user.user_id, [{'name': "Item A", 'price': Decimal('10.00'), 'stock_level': 10, 'quantity': 1}], "ORDER1")
    order2, _ = create_order_for_test(db, customer_user.user_id, [{'name': "Item B", 'price': Decimal('5.00'), 'stock_level': 5, 'quantity': 2}], "ORDER2")
    
    # Act
    response = customer_auth_client.get('/api/v1/orders')
    
    # Assert
    assert response.status_code == 200
    data = response.json
    assert len(data) == 2
    
    order_ids = [order_data['order_id'] for order_data in data]
    assert str(order1.order_id) in order_ids
    assert str(order2.order_id) in order_ids

    # Check content of one order
    retrieved_order1 = next(item for item in data if item["order_id"] == str(order1.order_id))
    assert retrieved_order1['order_number'] == order1.order_number
    assert retrieved_order1['total_amount'] == str(order1.total_amount)
    assert len(retrieved_order1['items']) == 1
    assert retrieved_order1['items'][0]['name'] == "Item A"

def test_get_customer_orders_filters_by_user(customer_auth_client, db, customer_user):
    # Arrange: Create an order for the authenticated customer
    order_for_current_user, _ = create_order_for_test(db, customer_user.user_id, [{'name': "Current User Item", 'price': Decimal('10.00'), 'stock_level': 10}])
    
    # Create another user and an order for them (should not be visible)
    other_user_id = uuid.uuid4()
    other_user = User(user_id=other_user_id, email=f'other_user_{other_user_id}@example.com', role='customer')
    other_user.set_password('otherpassword')
    db.session.add(other_user)
    db.session.flush()
    order_for_other_user, _ = create_order_for_test(db, other_user.user_id, [{'name': "Other User Item", 'price': Decimal('20.00'), 'stock_level': 20}])
    db.session.commit()

    # Act
    response = customer_auth_client.get('/api/v1/orders')

    # Assert
    assert response.status_code == 200
    data = response.json
    assert len(data) == 1 # Only the current user's order should be returned
    assert data[0]['order_id'] == str(order_for_current_user.order_id)