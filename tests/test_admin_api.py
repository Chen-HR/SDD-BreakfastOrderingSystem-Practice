import pytest
from src.models import User, MenuItem, Order, OrderItem
import uuid
import datetime

def test_get_admin_orders_empty(client, db):
    response = client.get('/api/v1/admin/orders')
    assert response.status_code == 200
    assert response.json == []

def test_get_admin_orders_with_data(client, db):
    # Arrange
    user = User(email='admin@example.com', role='admin')
    user.set_password('password')
    db.session.add(user)
    db.session.commit() # Commit user first to get user_id

    menu_item1 = MenuItem(name="Coffee", price=5.00, stock_level=100)
    menu_item2 = MenuItem(name="Sandwich", price=10.00, stock_level=50)
    db.session.add_all([menu_item1, menu_item2])
    
    order = Order(
        user_id=user.user_id,
        order_number='ORD-001',
        total_amount=15.00,
        delivery_address='123 Main St',
        status='pending'
    )
    order.items.append(OrderItem(
        menu_item_id=menu_item1.item_id,
        quantity=1,
        unit_price=5.00,
        subtotal=5.00
    ))
    order.items.append(OrderItem(
        menu_item_id=menu_item2.item_id,
        quantity=1,
        unit_price=10.00,
        subtotal=10.00
    ))
    db.session.add(order)
    db.session.commit()

    # Act
    response = client.get('/api/v1/admin/orders')

    # Assert
    assert response.status_code == 200
    data = response.json
    assert len(data) == 1
    
    order_data = data[0]
    assert order_data['order_id'] == str(order.order_id)
    assert order_data['order_number'] == 'ORD-001'
    assert order_data['total_amount'] == '15.00' # Decimal serialized to string
    assert order_data['status'] == 'pending'
    assert len(order_data['items']) == 2
    assert order_data['items'][0]['name'] == 'Coffee'
    assert order_data['items'][1]['name'] == 'Sandwich'

def test_update_order_status_success(client, db):
    # Arrange
    user = User(email='test_user@example.com', role='customer')
    user.set_password('password')
    db.session.add(user)
    db.session.commit() # Commit user first

    menu_item = MenuItem(name="Test Item", price=10.00, stock_level=10)
    db.session.add(menu_item)
    order = Order(user_id=user.user_id, order_number='ORD-TEST-001', total_amount=10.00)
    order.items.append(OrderItem(menu_item_id=menu_item.item_id, quantity=1, unit_price=10.00, subtotal=10.00))
    db.session.add(order)
    db.session.commit()

    new_status = 'in_progress'
    
    # Act
    response = client.put(f'/api/v1/admin/orders/{order.order_id}/status', json={'status': new_status})

    # Assert
    assert response.status_code == 200
    assert response.json['status'] == new_status
    updated_order = db.session.get(Order, order.order_id)
    assert updated_order.status == new_status

def test_update_order_status_order_not_found(client, db):
    # Arrange
    non_existent_id = uuid.uuid4()
    new_status = 'delivered'

    # Act
    response = client.put(f'/api/v1/admin/orders/{non_existent_id}/status', json={'status': new_status})

    # Assert
    assert response.status_code == 404
    assert 'Order not found' in response.json['message']

def test_update_order_status_invalid_status(client, db):
    # Arrange
    user = User(email='test_user2@example.com', role='customer')
    user.set_password('password')
    db.session.add(user)
    db.session.commit() # Commit user first

    menu_item = MenuItem(name="Test Item 2", price=5.00, stock_level=5)
    db.session.add(menu_item)
    order = Order(user_id=user.user_id, order_number='ORD-TEST-002', total_amount=5.00)
    db.session.add(order)
    db.session.commit()

    invalid_status = 'invalid_state'

    # Act
    response = client.put(f'/api/v1/admin/orders/{order.order_id}/status', json={'status': invalid_status})

    # Assert
    assert response.status_code == 400
    assert 'Invalid status' in response.json['message']

def test_update_order_status_missing_payload(client, db):
    # Arrange
    user = User(email='test_user3@example.com', role='customer')
    user.set_password('password')
    db.session.add(user)
    db.session.commit() # Commit user first

    menu_item = MenuItem(name="Test Item 3", price=12.00, stock_level=12)
    db.session.add(menu_item)
    order = Order(user_id=user.user_id, order_number='ORD-TEST-003', total_amount=12.00)
    db.session.add(order)
    db.session.commit()

    # Act
    response = client.put(f'/api/v1/admin/orders/{order.order_id}/status', json={})

    # Assert
    assert response.status_code == 400
    assert 'Status is required' in response.json['message']
