from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from app import db, ma
from app.models import User
from marshmallow import Schema, fields, validate, ValidationError

class UserRegisterSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))

class UserLoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

class UserRegister(Resource):
    def post(self):
        try:
            data = UserRegisterSchema().load(request.get_json())
        except ValidationError as err:
            return {"message": err.messages}, 400

        username = data['username']
        email = data['email']
        password = data['password']

        if User.query.filter_by(username=username).first():
            return {"message": f"User '{username}' already exists"}, 400
        if User.query.filter_by(email=email).first():
            return {"message": f"Email '{email}' already registered"}, 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return {"message": f"User '{username}' created successfully"}, 201

class UserLogin(Resource):
    def post(self):
        try:
            data = UserLoginSchema().load(request.get_json())
        except ValidationError as err:
            return {"message": err.messages}, 400

        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            return {"access_token": access_token}, 200
        else:
            return {"message": "Invalid credentials"}, 401
