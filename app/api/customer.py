from flask import request
from flask_restful import Resource
from app.services import OrderService
from app import db, ma
from app.models import User, MenuItem
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas import MenuItemSchema, OrderSchema
from marshmallow import Schema, fields, validate, ValidationError

class OrderItemRequestSchema(Schema):
    item_id = fields.Integer(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))

class OrderCreationRequestSchema(Schema):
    items = fields.List(fields.Nested(OrderItemRequestSchema), required=True, validate=validate.Length(min=1))

class OrderCreationResource(Resource):
    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        try:
            data = OrderCreationRequestSchema().load(request.get_json())
        except ValidationError as err:
            return {"message": err.messages}, 400

        items_data = data['items']
        
        user = db.session.get(User, current_user_id)
        if not user:
            # This case should ideally not be reached if JWT is valid and user exists
            return {'message': f'User with ID {current_user_id} not found'}, 404

        try:
            order, total_amount = OrderService.create_order(current_user_id, items_data)
            order_schema = OrderSchema()
            return {
                'message': 'Order created successfully',
                'order': order_schema.dump(order),
                'total_amount': total_amount
            }, 201
        except ValueError as e:
            db.session.rollback() # Rollback in case of business logic errors
            return {'message': str(e)}, 400
        except Exception as e:
            # Catch any other unexpected errors
            db.session.rollback() # Rollback in case of unexpected errors
            return {'message': f'An unexpected error occurred: {str(e)}'}, 500

class MenuResource(Resource):
    @jwt_required()
    def get(self):
        menu_items = MenuItem.query.all()
        menu_schema = MenuItemSchema(many=True) # Use many=True for a list of items
        return {'menu': menu_schema.dump(menu_items)}, 200
