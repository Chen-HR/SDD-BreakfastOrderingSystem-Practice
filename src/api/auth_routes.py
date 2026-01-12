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
    # This is a placeholder for Task 24.
    return jsonify({"msg": "Register not implemented yet"}), 501
