from src.models import User, Order, MenuItem
import uuid

def test_password_hashing():
    u = User(email='test@example.com', role='customer')
    u.set_password('mysecretpassword')
    assert u.password_hash is not None
    assert u.password_hash != 'mysecretpassword'

def test_password_checking():
    u = User(email='test2@example.com', role='customer')
    u.set_password('supersecret')
    assert u.check_password('supersecret') is True
    assert u.check_password('anotherpassword') is False

def test_order_default_status():
    order = Order(
        user_id=uuid.uuid4(),
        order_number='ORD-20260113-001',
        total_amount=100.00
    )
    assert order.status == 'pending'

def test_order_status_transition():
    order = Order(
        user_id=uuid.uuid4(),
        order_number='ORD-20260113-002',
        total_amount=100.00
    )
    order.status = 'in_progress'
    assert order.status == 'in_progress'
