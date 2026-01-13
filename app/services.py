from app.models import MenuItem, Order, OrderItem
from app import db

class OrderService:
    @staticmethod
    def check_stock(item_id, quantity):
        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            raise ValueError(f"MenuItem with ID {item_id} not found.")
        if menu_item.stock < quantity:
            return False, f"Not enough stock for {menu_item.name}. Available: {menu_item.stock}, Requested: {quantity}"
        return True, None

    @staticmethod
    def calculate_order_total(items_data):
        total_amount = 0.0
        for item_data in items_data:
            item_id = item_data['item_id']
            quantity = item_data['quantity']
            menu_item = db.session.get(MenuItem, item_id)
            if not menu_item:
                raise ValueError(f"MenuItem with ID {item_id} not found for total calculation.")
            total_amount += menu_item.price * quantity
        return total_amount

    @staticmethod
    def create_order(user_id, items_data):
        # First, perform stock checks for all items
        for item_data in items_data:
            item_id = item_data['item_id']
            quantity = item_data['quantity']
            in_stock, message = OrderService.check_stock(item_id, quantity)
            if not in_stock:
                raise ValueError(message)
        
        # Calculate total amount
        total_amount = OrderService.calculate_order_total(items_data)

        # Create the order
        order = Order(user_id=user_id)
        db.session.add(order)
        db.session.flush() # Flush to get the order.id for order items

        # Create order items and update stock
        for item_data in items_data:
            item_id = item_data['item_id']
            quantity = item_data['quantity']
            menu_item = db.session.get(MenuItem, item_id) # Re-fetch to be safe
            
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_id,
                quantity=quantity,
                price=menu_item.price # Store price at time of order
            )
            db.session.add(order_item)
            
            # Decrease stock
            menu_item.stock -= quantity
            db.session.add(menu_item) # Mark for update

        db.session.commit()
        return order, total_amount