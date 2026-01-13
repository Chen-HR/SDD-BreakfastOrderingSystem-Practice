import pytest
from app import db
from app.models import User, MenuItem, Order, OrderItem
from datetime import datetime, timedelta

@pytest.fixture
def seed_admin_api_data(app):
    with app.app_context():
        # Clear data
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(MenuItem).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Users
        user1 = User(username='testuser1', email='test1@example.com')
        user1.set_password('password')
        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password('password')
        db.session.add_all([user1, user2])
        db.session.flush()

        # Menu Items
        item1 = MenuItem(name='Coffee', description='Hot Coffee', price=2.50, stock=10)
        item2 = MenuItem(name='Sandwich', description='Club Sandwich', price=5.00, stock=5)
        db.session.add_all([item1, item2])
        db.session.flush()

        # Orders
        order1 = Order(user_id=user1.id, status='pending', created_at=datetime.utcnow() - timedelta(days=2))
        order2 = Order(user_id=user1.id, status='processing', created_at=datetime.utcnow() - timedelta(days=1))
        order3 = Order(user_id=user2.id, status='completed', created_at=datetime.utcnow())
        db.session.add_all([order1, order2, order3])
        db.session.flush()

        # Order Items
        order_item1 = OrderItem(order_id=order1.id, menu_item_id=item1.id, quantity=2, price=item1.price)
        order_item2 = OrderItem(order_id=order1.id, menu_item_id=item2.id, quantity=1, price=item2.price)
        order_item3 = OrderItem(order_id=order2.id, menu_item_id=item1.id, quantity=1, price=item1.price)
        db.session.add_all([order_item1, order_item2, order_item3])
        db.session.commit()

        # Refresh objects to ensure they are bound to the session
        db.session.refresh(user1)
        db.session.refresh(user2)
        db.session.refresh(item1)
        db.session.refresh(item2)
        db.session.refresh(order1)
        db.session.refresh(order2)
        db.session.refresh(order3)

        return {
            'user1_id': user1.id,
            'user2_id': user2.id,
            'item1_id': item1.id,
            'item2_id': item2.id,
            'order1_id': order1.id,
            'order2_id': order2.id,
            'order3_id': order3.id,
        }

def test_get_admin_orders_all(client, seed_admin_api_data):
    response = client.get('/api/v1/admin/orders')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_items'] == 3
    assert len(data['orders']) == 3

def test_get_admin_orders_filter_by_user(client, seed_admin_api_data):
    user1_id = seed_admin_api_data['user1_id']
    response = client.get(f'/api/v1/admin/orders?user_id={user1_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_items'] == 2
    assert len(data['orders']) == 2
    for order in data['orders']:
        assert order['user_id'] == user1_id

def test_get_admin_orders_filter_by_status(client, seed_admin_api_data):
    response = client.get('/api/v1/admin/orders?status=pending')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_items'] == 1
    assert data['orders'][0]['status'] == 'pending'

def test_get_admin_orders_filter_by_date(client, app, seed_admin_api_data):
    with app.app_context():
        today = datetime.utcnow().strftime('%Y-%m-%d')
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Orders created today or yesterday
        response = client.get(f'/api/v1/admin/orders?start_date={yesterday}&end_date={today}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_items'] == 2 # order2 and order3

def test_get_admin_orders_pagination(client, seed_admin_api_data):
    response = client.get('/api/v1/admin/orders?page=1&per_page=1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_items'] == 3
    assert data['current_page'] == 1
    assert len(data['orders']) == 1

# --- Order Status Update API Tests (Task 11) ---

def test_update_order_status_success(client, seed_admin_api_data):
    order1_id = seed_admin_api_data['order1_id'] # status is 'pending'
    response = client.put(f'/api/v1/orders/{order1_id}/status', json={'status': 'processing'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'status updated to processing' in data['message']

    with client.application.app_context():
        order = db.session.get(Order, order1_id)
        assert order.status == 'processing'

def test_update_order_status_invalid_transition(client, seed_admin_api_data):
    order3_id = seed_admin_api_data['order3_id'] # status is 'completed'
    response = client.put(f'/api/v1/orders/{order3_id}/status', json={'status': 'pending'})
    assert response.status_code == 400
    data = response.get_json()
    assert 'Invalid status transition' in data['message']

    with client.application.app_context():
        order = db.session.get(Order, order3_id)
        assert order.status == 'completed' # Should not have changed

def test_update_order_status_order_not_found(client):
    response = client.put('/api/v1/orders/999/status', json={'status': 'processing'})
    assert response.status_code == 404
    data = response.get_json()
    assert 'Order not found' in data['message']

def test_update_order_status_no_status_provided(client, seed_admin_api_data):
    order1_id = seed_admin_api_data['order1_id']
    response = client.put(f'/api/v1/orders/{order1_id}/status', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'Status is required' in data['message']

def test_update_order_status_no_change_needed(client, seed_admin_api_data):
    order1_id = seed_admin_api_data['order1_id'] # pending
    response = client.put(f'/api/v1/orders/{order1_id}/status', json={'status': 'pending'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'No change needed' in data['message']
    with client.application.app_context():
        order = db.session.get(Order, order1_id)
        assert order.status == 'pending' # Should remain pending
