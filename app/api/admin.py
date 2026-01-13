from flask import request
from flask_restful import Resource
from app import db, ma
from app.models import Order, User # Assuming User model is needed for filtering by user
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas import OrderSchema
from marshmallow import Schema, fields, validate, ValidationError

class OrderStatusUpdateSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(['pending', 'processing', 'completed', 'cancelled']))

class AdminOrdersResource(Resource):
    @jwt_required()
    def get(self):
        # TODO: Implement role-based access control here (e.g., check if get_jwt_identity() is an admin)
        current_user_id = get_jwt_identity() # Can be used for admin checks

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

        order_schema = OrderSchema(many=True) # Use many=True for a list of orders
        
        return {
            'orders': order_schema.dump(orders.items),
            'total_pages': orders.pages,
            'current_page': orders.page,
            'total_items': orders.total
        }, 200


class OrderStatusResource(Resource):
    @jwt_required()
    def put(self, order_id):
        # TODO: Implement role-based access control here (e.g., check if get_jwt_identity() is an admin)
        current_user_id = get_jwt_identity() # Can be used for admin checks

        try:
            data = OrderStatusUpdateSchema().load(request.get_json())
        except ValidationError as err:
            return {"message": err.messages}, 400

        new_status = data['status']
        
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