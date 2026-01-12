from flask import Blueprint, request, jsonify
from src.models import User
from src.extensions import db
from flask_jwt_extended import create_access_token
from datetime import timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    user = db.session.scalar(db.select(User).filter_by(email=email))

    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.user_id), expires_delta=timedelta(hours=1))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad email or password"}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    if not "@" in email or "." not in email: # Basic email format validation
        return jsonify({"msg": "Invalid email format"}), 400

    if len(password) < 6: # Basic password strength check
        return jsonify({"msg": "Password must be at least 6 characters long"}), 400

    existing_user = db.session.scalar(db.select(User).filter_by(email=email))
    if existing_user:
        return jsonify({"msg": "User with that email already exists"}), 409

    new_user = User(email=email, role='customer')
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User registered successfully", "user_id": str(new_user.user_id)}), 201
