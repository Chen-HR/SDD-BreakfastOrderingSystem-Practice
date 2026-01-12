import uuid
from sqlalchemy.dialects.postgresql import UUID
from .app import db

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.Enum('customer', 'admin', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    orders = db.relationship('Order', backref='user', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    item_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String)
    stock_level = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

class Order(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id'), nullable=False)
    order_number = db.Column(db.String, nullable=False, unique=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'in_progress', 'ready_for_delivery', 'delivered', 'cancelled', name='order_statuses'), nullable=False, default='pending')
    delivery_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    item_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.order_id'), nullable=False)
    menu_item_id = db.Column(UUID(as_uuid=True), db.ForeignKey('menu_items.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    menu_item = db.relationship('MenuItem')
