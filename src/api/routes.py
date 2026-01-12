from flask import Blueprint, jsonify, request
from src.models import Order, User, MenuItem
from src.extensions import db
from sqlalchemy import desc

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

@admin_bp.route('/orders', methods=['GET'])
def get_admin_orders():
    orders = Order.query.order_by(desc(Order.created_at)).all()
    # TODO: Implement filtering

    orders_data = []
    for order in orders:
        order_items_data = []
        for item in order.items:
            order_items_data.append({
                'item_id': str(item.item_id),
                'menu_item_id': str(item.menu_item_id),
                'name': item.menu_item.name if item.menu_item else 'N/A',
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'subtotal': str(item.subtotal)
            })
        
        orders_data.append({
            'order_id': str(order.order_id),
            'user_id': str(order.user_id),
            'order_number': order.order_number,
            'total_amount': str(order.total_amount),
            'status': order.status,
            'delivery_address': order.delivery_address,
            'created_at': order.created_at.isoformat(),
            'items': order_items_data
        })
    return jsonify(orders_data), 200