from flask import jsonify, request
from src.models import Order, User, MenuItem, OrderItem
from src.extensions import db
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
import uuid
import traceback
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from flask_restx import Namespace, Resource, fields # Import necessary classes

# Create Namespaces
admin_ns = Namespace('admin', description='Admin related operations')
customer_ns = Namespace('customer', description='Customer related operations')


# Helper for admin authentication - adapted for flask_restx
def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = db.session.get(User, uuid.UUID(current_user_id))
        if not user or user.role != 'admin':
            admin_ns.abort(403, message='Administration rights required') # Use abort for consistent error handling
        return f(*args, **kwargs)
    return decorated_function

# Models for Admin API
order_item_model = admin_ns.model('OrderItem', {
    'item_id': fields.String(readOnly=True, description='The unique identifier of an order item'),
    'menu_item_id': fields.String(required=True, description='The unique identifier of the menu item'),
    'name': fields.String(required=True, description='Name of the menu item'),
    'quantity': fields.Integer(required=True, description='Quantity of the menu item'),
    'unit_price': fields.String(required=True, description='Unit price of the menu item'),
    'subtotal': fields.String(required=True, description='Subtotal for the order item'),
})

order_model = admin_ns.model('Order', {
    'order_id': fields.String(readOnly=True, description='The unique identifier of an order'),
    'user_id': fields.String(required=True, description='The unique identifier of the user who placed the order'),
    'order_number': fields.String(required=True, description='The human-readable order number'),
    'total_amount': fields.String(required=True, description='Total amount of the order'),
    'status': fields.String(required=True, description='Current status of the order (e.g., pending, in_progress)'),
    'delivery_address': fields.String(description='Delivery address for the order'),
    'created_at': fields.DateTime(readOnly=True, description='Timestamp when the order was created'),
    'items': fields.List(fields.Nested(order_item_model), description='List of items in the order'),
})

order_status_update_model = admin_ns.model('OrderStatusUpdate', {
    'status': fields.String(required=True, description='New status for the order (pending, in_progress, ready_for_delivery, delivered, cancelled)'),
})

@admin_ns.route('/orders')
class AdminOrders(Resource):
    @admin_ns.doc(security='jwt', description='Get a list of all orders with filtering options (admin only)')
    @admin_ns.marshal_list_with(order_model)
    @admin_required
    def get(self):
        '''List all orders'''
        orders = db.session.query(Order).options(joinedload(Order.items).joinedload(OrderItem.menu_item)).order_by(desc(Order.created_at)).all()
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
        return orders_data, 200

@admin_ns.route('/orders/<uuid:order_id>/status')
@admin_ns.param('order_id', 'The Order identifier')
class AdminOrderStatus(Resource):
    @admin_ns.doc(security='jwt', description='Update the status of an order (admin only)')
    @admin_ns.expect(order_status_update_model, validate=True)
    @admin_ns.response(200, 'Order status updated successfully', order_model) # Use order_model for response as well, or define a simpler status update response model
    @admin_ns.response(400, 'Validation Error')
    @admin_ns.response(404, 'Order not found')
    @admin_required
    def put(self, order_id):
        '''Update an order's status'''
        data = request.get_json()
        new_status = data.get('status')

        order = db.session.get(Order, order_id)

        if not order:
            admin_ns.abort(404, message='Order not found')
        
        valid_statuses = [status for status in Order.status.type.enums]
        if new_status not in valid_statuses:
            admin_ns.abort(400, message=f'Invalid status: {new_status}. Valid statuses are: {", ".join(valid_statuses)}')

        order.status = new_status
        db.session.commit()

        # Re-fetch order to ensure all linked data is fresh for marshaling
        updated_order = db.session.query(Order).options(joinedload(Order.items).joinedload(OrderItem.menu_item)).filter_by(order_id=order.order_id).first()

        return updated_order, 200 # flask-restx will marshal this with order_model

# Models for Customer API
order_item_request_model = customer_ns.model('OrderItemRequest', {
    'menu_item_id': fields.String(required=True, description='The unique identifier of the menu item'),
    'quantity': fields.Integer(required=True, min=1, description='Quantity of the menu item (minimum 1)'),
})

order_creation_model = customer_ns.model('OrderCreation', {
    'items': fields.List(fields.Nested(order_item_request_model), required=True, description='List of items to order'),
    # Add other fields like delivery_address, delivery_time if they are part of the initial order creation
})

# Re-using order_model from admin_ns for consistency if structure is similar
# If customer view needs less detail, define a specific customer_order_model
customer_order_model = customer_ns.model('CustomerOrder', {
    'order_id': fields.String(readOnly=True, description='The unique identifier of an order'),
    'order_number': fields.String(required=True, description='The human-readable order number'),
    'total_amount': fields.String(required=True, description='Total amount of the order'),
    'status': fields.String(required=True, description='Current status of the order'),
    'created_at': fields.DateTime(readOnly=True, description='Timestamp when the order was created'),
    'items': fields.List(fields.Nested(order_item_model), description='List of items in the order'), # Using order_item_model from admin_ns
})

menu_item_model = customer_ns.model('MenuItem', {
    'item_id': fields.String(readOnly=True, description='The unique identifier of the menu item'),
    'name': fields.String(required=True, description='Name of the menu item'),
    'price': fields.String(required=True, description='Price of the menu item'),
    'stock_level': fields.Integer(required=True, description='Current stock level'),
    'image_url': fields.String(description='URL of the menu item image'),
})

@customer_ns.route('/orders')
class CustomerOrders(Resource):
    @customer_ns.doc(security='jwt', description='Create a new order')
    @customer_ns.expect(order_creation_model, validate=True)
    @customer_ns.response(201, 'Order created successfully', customer_order_model)
    @customer_ns.response(400, 'Invalid input or insufficient stock')
    @jwt_required()
    def post(self):
        '''Create a new customer order'''
        current_user_id = get_jwt_identity()
        current_user_uuid = uuid.UUID(current_user_id)
        
        data = request.get_json()
        items = data.get('items')

        try:
            new_order = create_order(current_user_uuid, items)
            db.session.commit()
            # Re-fetch the order to ensure full data for marshaling
            order_data_for_response = db.session.query(Order).options(joinedload(Order.items).joinedload(OrderItem.menu_item)).filter_by(order_id=new_order.order_id).first()
            return order_data_for_response, 201
        except OrderException as e:
            db.session.rollback()
            customer_ns.abort(400, message=str(e))
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            customer_ns.abort(500, message='An unexpected error occurred')

    @customer_ns.doc(security='jwt', description='Get a list of orders for the authenticated customer')
    @customer_ns.marshal_list_with(customer_order_model)
    @jwt_required()
    def get(self):
        '''List customer orders'''
        current_user_id = get_jwt_identity()
        current_user_uuid = uuid.UUID(current_user_id)

        orders = db.session.query(Order).options(joinedload(Order.items).joinedload(OrderItem.menu_item)).filter_by(user_id=current_user_uuid).order_by(desc(Order.created_at)).all()
        
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
                'delivery_address': order.delivery_address, # This might not be needed for customer view, but keeping for now
                'created_at': order.created_at.isoformat(),
                'items': order_items_data
            })
        return orders_data, 200

@customer_ns.route('/menu')
class Menu(Resource):
    @customer_ns.doc(description='Get the available menu items')
    @customer_ns.marshal_list_with(menu_item_model)
    def get(self):
        '''List all available menu items'''
        menu_items = db.session.execute(db.select(MenuItem).filter(MenuItem.stock_level > 0)).scalars().all()
        
        menu_data = []
        for item in menu_items:
            menu_data.append({
                'item_id': str(item.item_id),
                'name': item.name,
                'price': str(item.price),
                'stock_level': item.stock_level,
                'image_url': item.image_url
            })
        return menu_data, 200