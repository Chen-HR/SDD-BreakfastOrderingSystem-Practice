import pytest
from app.models import User, Order
from app import db
from datetime import datetime, timedelta

def test_order_creation_and_status(app):
    with app.app_context():
        user = User(username='order_test_user', email='order_test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        order = Order(user_id=user.id)
        db.session.add(order)
        db.session.commit()

        assert order.id is not None
        assert order.user_id == user.id
        assert order.status == 'pending'  # Default status

def test_order_status_update(app):
    with app.app_context():
        user = User(username='status_test_user', email='status_test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        order = Order(user_id=user.id)
        db.session.add(order)
        db.session.commit()

        # Update status
        order.status = 'processing'
        db.session.commit()
        assert order.status == 'processing'

        order.status = 'completed'
        db.session.commit()
        assert order.status == 'completed'

        order.status = 'cancelled'
        db.session.commit()
        assert order.status == 'cancelled'

def test_order_timestamps(app):
    with app.app_context():
        user = User(username='timestamp_test_user', email='timestamp_test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        # Create an order and check created_at
        order = Order(user_id=user.id)
        db.session.add(order)
        db.session.commit()
        
        assert order.created_at is not None
        assert order.updated_at is not None
        assert abs((datetime.utcnow() - order.created_at).total_seconds()) < 5 # within 5 seconds

        # Update the order and check updated_at
        old_updated_at = order.updated_at
        order.status = 'processing'
        db.session.commit()
        assert order.updated_at > old_updated_at
