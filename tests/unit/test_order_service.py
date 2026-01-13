import pytest
from app.models import User, MenuItem, Order, OrderItem
from app.services import OrderService
from app import db

@pytest.fixture
def seed_data(app):
    with app.app_context():
        # Clear existing data to ensure a clean state for each test
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(MenuItem).delete()
        db.session.query(User).delete()
        db.session.commit()

        user = User(username='service_user', email='service@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.flush() 

        item1 = MenuItem(name='Coffee', description='Hot Coffee', price=2.50, stock=10)
        item2 = MenuItem(name='Sandwich', description='Club Sandwich', price=5.00, stock=5)
        item3 = MenuItem(name='Juice', description='Orange Juice', price=3.00, stock=0) # Out of stock

        db.session.add_all([item1, item2, item3])
        db.session.commit()
        
        # Refresh objects to ensure they are bound to the session
        db.session.refresh(user)
        db.session.refresh(item1)
        db.session.refresh(item2)
        db.session.refresh(item3)
        
        
        return user, item1.id, item2.id, item3.id

def test_check_stock_sufficient(app, seed_data):
    user_id, item1_id, item2_id, item3_id = seed_data
    with app.app_context():
        item1 = db.session.get(MenuItem, item1_id)
        in_stock, message = OrderService.check_stock(item1.id, 5)
        assert in_stock is True
        assert message is None

def test_check_stock_insufficient(app, seed_data):
    user_id, item1_id, item2_id, item3_id = seed_data
    with app.app_context():
        item2 = db.session.get(MenuItem, item2_id)
        in_stock, message = OrderService.check_stock(item2.id, 10) # Request 10, stock is 5
        assert in_stock is False
        assert "Not enough stock" in message

def test_check_stock_item_not_found(app):
    with app.app_context():
        with pytest.raises(ValueError, match="MenuItem with ID 999 not found."):
            OrderService.check_stock(999, 1)

def test_calculate_order_total(app, seed_data):
    user_id, item1_id, item2_id, item3_id = seed_data
    with app.app_context():
        item1 = db.session.get(MenuItem, item1_id)
        item2 = db.session.get(MenuItem, item2_id)
        items_data = [
            {'item_id': item1.id, 'quantity': 2}, # 2 * 2.50 = 5.00
            {'item_id': item2.id, 'quantity': 1}  # 1 * 5.00 = 5.00
        ]
        total = OrderService.calculate_order_total(items_data)
        assert total == 10.00

def test_calculate_order_total_item_not_found(app):
    with app.app_context():
        items_data = [
            {'item_id': 1, 'quantity': 1},
            {'item_id': 999, 'quantity': 1} # Non-existent item
        ]
        with pytest.raises(ValueError, match="MenuItem with ID 999 not found"):
            OrderService.calculate_order_total(items_data)

def test_create_order_success(app, seed_data):
    user_obj, item1_id, item2_id, item3_id = seed_data
    with app.app_context():
        item1 = db.session.get(MenuItem, item1_id)
        item2 = db.session.get(MenuItem, item2_id)

        initial_stock_item1 = item1.stock
        initial_stock_item2 = item2.stock

        items_data = [
            {'item_id': item1.id, 'quantity': 2},
            {'item_id': item2.id, 'quantity': 1}
        ]
        order, total_amount = OrderService.create_order(user_obj.id, items_data)

        assert order is not None
        assert order.user_id == user_obj.id
        assert order.status == 'pending'
        assert total_amount == 10.00

        # Check order items
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        assert len(order_items) == 2
        
        # Verify stock reduction
        db.session.refresh(item1)
        db.session.refresh(item2)
        assert item1.stock == initial_stock_item1 - 2
        assert item2.stock == initial_stock_item2 - 1

def test_create_order_insufficient_stock(app, seed_data):
    user_obj, item1_id, item2_id, item3_id = seed_data
    with app.app_context():
        item1 = db.session.get(MenuItem, item1_id)
        item2 = db.session.get(MenuItem, item2_id)
        items_data = [
            {'item_id': item1.id, 'quantity': 5},
            {'item_id': item2.id, 'quantity': 10} # Request 10, stock is 5
        ]
        with pytest.raises(ValueError, match="Not enough stock for Sandwich"):
            OrderService.create_order(user_obj.id, items_data)

        # Verify no order was created and stock is unchanged
        assert Order.query.count() == 0
        db.session.refresh(item1)
        db.session.refresh(item2)
        assert item1.stock == 10 # Initial stock
        assert item2.stock == 5 # Initial stock

def test_create_order_item_not_found(app, seed_data):
    user_obj, item1_id, item2_id, item3_id = seed_data
    with app.app_context():
        item1 = db.session.get(MenuItem, item1_id)
        items_data = [
            {'item_id': item1.id, 'quantity': 1},
            {'item_id': 999, 'quantity': 1} # Non-existent item
        ]
        with pytest.raises(ValueError, match="MenuItem with ID 999 not found"):
            OrderService.create_order(user_obj.id, items_data)
        
        # Verify no order was created and stock is unchanged
        assert Order.query.count() == 0
        db.session.refresh(item1)
        assert item1.stock == 10 # Initial stock
