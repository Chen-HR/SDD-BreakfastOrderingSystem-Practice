from flask import request, jsonify
from src.models import User
from src.extensions import db
from flask_jwt_extended import create_access_token
from datetime import timedelta
from flask_restx import Namespace, Resource, fields

auth_ns = Namespace('auth', description='Authentication operations')

# Models for request and response
user_auth_model = auth_ns.model('UserAuth', {
    'email': fields.String(required=True, description='User email'),
    'password': fields.String(required=True, description='User password', min_length=6),
})

login_success_model = auth_ns.model('LoginSuccess', {
    'access_token': fields.String(required=True, description='JWT access token'),
})

register_success_model = auth_ns.model('RegisterSuccess', {
    'msg': fields.String(required=True, description='Success message'),
    'user_id': fields.String(required=True, description='UUID of the registered user'),
})

@auth_ns.route('/login')
class UserLogin(Resource):
    @auth_ns.doc(description='Log in a user and return a JWT access token')
    @auth_ns.expect(user_auth_model, validate=True)
    @auth_ns.response(200, 'Login successful', login_success_model)
    @auth_ns.response(401, 'Bad email or password')
    def post(self):
        '''User Login'''
        email = request.json.get('email')
        password = request.json.get('password')

        user = db.session.scalar(db.select(User).filter_by(email=email))

        if user and user.check_password(password):
            access_token = create_access_token(identity=str(user.user_id), expires_delta=timedelta(hours=1))
            return {'access_token': access_token}, 200
        else:
            auth_ns.abort(401, message='Bad email or password')

@auth_ns.route('/register')
class UserRegister(Resource):
    @auth_ns.doc(description='Register a new user')
    @auth_ns.expect(user_auth_model, validate=True)
    @auth_ns.response(201, 'User registered successfully', register_success_model)
    @auth_ns.response(400, 'Missing email or password / Invalid email format / Password too short')
    @auth_ns.response(409, 'User with that email already exists')
    def post(self):
        '''User Registration'''
        email = request.json.get('email')
        password = request.json.get('password')

        if not email or not password:
            auth_ns.abort(400, message='Missing email or password')

        # Basic email format validation
        if "@" not in email or "." not in email:
            auth_ns.abort(400, message='Invalid email format')

        # Basic password strength check
        if len(password) < 6:
            auth_ns.abort(400, message='Password must be at least 6 characters long')

        existing_user = db.session.scalar(db.select(User).filter_by(email=email))
        if existing_user:
            auth_ns.abort(409, message='User with that email already exists')

        new_user = User(email=email, role='customer')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return {'msg': 'User registered successfully', 'user_id': str(new_user.user_id)}, 201
