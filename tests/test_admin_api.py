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

    menu_item1 = MenuItem(name="Coffee", price=5.00, stock_level=100)
    menu_item2 = MenuItem(name="Sandwich", price=10.00, stock_level=50)
    db.session.add_all([menu_item1, menu_item2])
    db.session.commit()

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
