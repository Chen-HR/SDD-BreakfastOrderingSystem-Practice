from flask import request
from flask_restful import Resource
from app.services import OrderService
from app import db
from app.models import User, MenuItem

class OrderCreationResource(Resource):
    def post(self):
        data = request.get_json()
        user_id = data.get('user_id')
        items_data = data.get('items')

        if not user_id:
            return {'message': 'User ID is required'}, 400
        if not items_data or not isinstance(items_data, list):
            return {'message': 'Items data (list of item_id and quantity) is required'}, 400
        
        user = db.session.get(User, user_id)
        if not user:
            return {'message': f'User with ID {user_id} not found'}, 404

        try:
            order, total_amount = OrderService.create_order(user_id, items_data)
            return {
                'message': 'Order created successfully',
                'order_id': order.id,
                'total_amount': total_amount
            }, 201
        except ValueError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            # Catch any other unexpected errors
            db.session.rollback() # Rollback in case of unexpected errors
            return {'message': f'An unexpected error occurred: {str(e)}'}, 500
