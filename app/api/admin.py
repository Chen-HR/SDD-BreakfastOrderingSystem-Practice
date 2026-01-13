from flask import request
from flask_restful import Resource
from app import db
from app.models import Order, User # Assuming User model is needed for filtering by user
from datetime import datetime

class AdminOrdersResource(Resource):
    def get(self):
        query = Order.query

        # Filtering
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date') # YYYY-MM-DD
        end_date = request.args.get('end_date')     # YYYY-MM-DD

        if user_id:
            query = query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        if start_date:
            query = query.filter(Order.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            # Add one day to include orders from the end_date
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Order.created_at < end_date_obj + timedelta(days=1))

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

        # Serialize orders
        # For simplicity, we'll return a basic dictionary. In a real app, use Marshmallow or similar.
        result = []
        for order in orders.items:
            order_items_data = []
            for item in order.items:
                order_items_data.append({
                    'item_id': item.menu_item_id,
                    'quantity': item.quantity,
                    'price_at_order': item.price,
                    'item_name': item.menu_item.name # Assuming menu_item relationship is loaded
                })

            result.append({
                'id': order.id,
                'user_id': order.user_id,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'items': order_items_data
            })
        
        return {
            'orders': result,
            'total_pages': orders.pages,
            'current_page': orders.page,
            'total_items': orders.total
        }, 200

from datetime import timedelta # Import timedelta for end_date filtering

class OrderStatusResource(Resource):
    def put(self, order_id):
        data = request.get_json()
        new_status = data.get('status')

        if not new_status:
            return {'message': 'Status is required'}, 400
        
        order = db.session.get(Order, order_id)
        if not order:
            return {'message': 'Order not found'}, 404
        
        # Basic status transition validation (can be more sophisticated with a state machine library)
        valid_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['completed', 'cancelled'],
            'completed': [], # Cannot change once completed
            'cancelled': []  # Cannot change once cancelled
        }

        if new_status not in valid_transitions.get(order.status, []):
            if new_status == order.status:
                return {'message': f'Order is already {order.status}. No change needed.'}, 200
            return {'message': f'Invalid status transition from {order.status} to {new_status}'}, 400
        
        order.status = new_status
        db.session.commit()
        
        return {'message': f'Order {order.id} status updated to {new_status}'}, 200