import uuid
from sqlalchemy.orm import joinedload
from src.models import Order, OrderItem, MenuItem, User
from src.app import db

class OrderException(Exception):
    pass

def create_order(user_id, items):
    """
    Creates an order, performs stock checking, and calculates the total amount.
    :param user_id: The ID of the user placing the order.
    :param items: A list of dictionaries, each with 'item_id' and 'quantity'.
    :return: The created Order object.
    :raises OrderException: If validation fails.
    """
    if not items:
        raise OrderException("Cannot create an order with no items.")

    # Use a transaction
    with db.session.begin_nested() as transaction:
        total_amount = 0
        new_order = Order(
            user_id=user_id,
            order_number=f"ORD-{uuid.uuid4()}" # A more robust number generation would be needed in production
        )

        order_items = []
        for item_data in items:
            item_id = item_data.get('item_id')
            quantity = item_data.get('quantity')

            if not all([item_id, quantity]):
                raise OrderException("Invalid item data provided.")

            # Lock the row for update
            menu_item = db.session.get(MenuItem, item_id, with_for_update=True)

            if not menu_item:
                raise OrderException(f"Menu item not found: {item_id}")

            if menu_item.stock_level < quantity:
                raise OrderException(f"Insufficient stock for {menu_item.name}. Available: {menu_item.stock_level}, Requested: {quantity}")

            subtotal = menu_item.price * quantity
            total_amount += subtotal
            menu_item.stock_level -= quantity

            order_items.append(OrderItem(
                menu_item_id=menu_item.item_id,
                quantity=quantity,
                unit_price=menu_item.price,
                subtotal=subtotal
            ))

        new_order.total_amount = total_amount
        new_order.items = order_items

        db.session.add(new_order)
    
    # The transaction is committed here if no exception was raised
    return new_order
