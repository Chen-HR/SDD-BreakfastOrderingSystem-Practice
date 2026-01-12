from flask import Blueprint, jsonify, request
from src.models import Order, User, MenuItem, OrderItem
from src.extensions import db
from sqlalchemy import desc
from sqlalchemy.orm import joinedload # Import joinedload
from src.services.order_service import create_order, OrderException
import uuid
import traceback # Import traceback
from flask_jwt_extended import jwt_required, get_jwt_identity # Import JWT decorators and functions

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')
customer_bp = Blueprint('customer', __name__, url_prefix='/api/v1')

@admin_bp.route('/orders', methods=['GET'])
def get_admin_orders():
    orders = db.session.query(Order).options(joinedload(Order.items).joinedload(OrderItem.menu_item)).order_by(desc(Order.created_at)).all()
    # TODO: Implement filtering

    orders_data = []
    for order in orders:
        order_items_data = []
        for item in order.items:
            order_items_data.append({
                'item_id': str(item.item_id),
                'menu_item_id': str(item.menu_item_id),
                'name': item.menu_item.name if item.menu_item else 'N/A', # Ensure menu_item is loaded
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

@admin_bp.route('/orders/<uuid:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({'message': 'Status is required'}), 400

    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Validate if the new_status is a valid enum value for Order.status
    valid_statuses = [status for status in Order.status.type.enums]
    if new_status not in valid_statuses:
        return jsonify({'message': f'Invalid status: {new_status}. Valid statuses are: {", ".join(valid_statuses)}'}), 400

    order.status = new_status
    db.session.commit()

    return jsonify({
        'order_id': str(order.order_id),
        'status': order.status,
        'message': 'Order status updated successfully'
    }), 200

@customer_bp.route('/orders', methods=['POST'])
@jwt_required() # Protect this endpoint with JWT
def create_customer_order():
    current_user_id = get_jwt_identity() # Get the user's identity from the JWT
    current_user_uuid = uuid.UUID(current_user_id) # Convert to UUID object
    
    data = request.get_json()
    items = data.get('items')

    if not items:
        return jsonify({'message': 'Items are required to create an order'}), 400

    try:
        new_order = create_order(current_user_uuid, items) # Pass the authenticated user's ID
        db.session.commit()
        return jsonify({
            'order_id': str(new_order.order_id),
            'order_number': new_order.order_number,
            'total_amount': str(new_order.total_amount),
            'status': new_order.status,
            'message': 'Order created successfully'
        }), 201
    except OrderException as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        traceback.print_exc() # Print the full traceback
        return jsonify({'message': 'An unexpected error occurred'}), 500

@customer_bp.route('/menu', methods=['GET'])
def get_menu():
    menu_items = db.session.execute(db.select(MenuItem).filter(MenuItem.stock_level > 0)).scalars().all()
    menu_data = []
    for item in menu_items:
        menu_data.append({
            'item_id': str(item.item_id),
            'name': item.name,
            'price': str(item.price), # Convert Decimal to string for JSON serialization
            'stock_level': item.stock_level,
            'image_url': item.image_url
        })
    return jsonify(menu_data), 200