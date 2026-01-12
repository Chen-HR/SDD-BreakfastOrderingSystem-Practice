import pytest
from src.services.order_service import create_order, OrderException
from src.models import User, MenuItem, Order
from src.app import create_app, db as _db
import uuid

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    app, _, _ = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """Function-scroped database fixture."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        _db.session.begin_nested()

        yield _db

        transaction.rollback()
        connection.close()
        _db.session.remove()


def test_create_order_success(db):
    # Arrange
    user = User(email='test@test.com', role='customer')
    user.set_password('password')
    db.session.add(user)

    menu_item = MenuItem(name="Test Burger", price=10.00, stock_level=20)
    db.session.add(menu_item)
    db.session.commit()

    items = [{'item_id': menu_item.item_id, 'quantity': 2}]

    # Act
    order = create_order(user.user_id, items)
    db.session.commit() # Commit the outer transaction to see the changes

    # Assert
    assert order is not None
    assert order.total_amount == 20.00
    assert len(order.items) == 1
    assert order.items[0].quantity == 2
    
    # Re-fetch the menu item to check the updated stock
    updated_menu_item = db.session.get(MenuItem, menu_item.item_id)
    assert updated_menu_item.stock_level == 18

def test_create_order_insufficient_stock(db):
    # Arrange
    user = User(email='test2@test.com', role='customer')
    user.set_password('password')
    db.session.add(user)

    menu_item = MenuItem(name="Test Fries", price=5.00, stock_level=5)
    db.session.add(menu_item)
    db.session.commit()

    items = [{'item_id': menu_item.item_id, 'quantity': 10}]

    # Act & Assert
    with pytest.raises(OrderException, match="Insufficient stock"):
        create_order(user.user_id, items)
    
    assert menu_item.stock_level == 5

def test_create_order_item_not_found(db):
    # Arrange
    user = User(email='test3@test.com', role='customer')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()

    items = [{'item_id': uuid.uuid4(), 'quantity': 1}]

    # Act & Assert
    with pytest.raises(OrderException, match="Menu item not found"):
        create_order(user.user_id, items)
