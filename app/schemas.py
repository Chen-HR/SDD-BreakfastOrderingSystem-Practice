from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app import ma
from app.models import User, MenuItem, Order, OrderItem

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ('password_hash',) # Never expose password hash

class MenuItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MenuItem
        load_instance = True

class OrderItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = OrderItem
        load_instance = True
        include_fk = True # Include foreign keys if needed for creation

    # Optionally include nested MenuItem data for display
    menu_item = SQLAlchemyAutoSchema.Nested(MenuItemSchema, exclude=('stock', 'image_url'))

class OrderSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True
        include_fk = True # Include user_id

    items = SQLAlchemyAutoSchema.Nested(OrderItemSchema, many=True)
    customer = SQLAlchemyAutoSchema.Nested(UserSchema, only=("id", "username", "email")) # Nested user data

