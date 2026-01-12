from flask import Flask, jsonify
from .config import Config
from src.api.routes import admin_ns, customer_ns # Import Namespaces
from src.api.auth_routes import auth_ns # Import Namespace
from src.extensions import db, migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api # Import Api

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    authorizations = {
        'jwt': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Type in the JWT Token with the 'Bearer ' prefix."
        }
    }

    # Initialize Flask-RESTx Api
    api = Api(app,
              version='1.0',
              title='Breakfast Ordering System API',
              description='API documentation for the Breakfast Ordering System',
              doc='/api/docs', # Serve docs at /api/docs
              prefix='/api/v1', # All API endpoints will be prefixed with /api/v1
              authorizations=authorizations, # Add security definitions
              security='jwt' # Apply JWT security globally by default
             )

    # Register namespaces
    api.add_namespace(admin_ns)
    api.add_namespace(customer_ns)
    api.add_namespace(auth_ns)

    # Register JWT error handlers
    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return jsonify({"msg": "Signature verification failed"}), 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return jsonify({"msg": "Token has expired"}), 401

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return jsonify({"msg": "Token has been revoked"}), 401

    return app, db, migrate
