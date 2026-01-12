from flask import Flask
from .config import Config
from src.api.routes import admin_bp, customer_bp
from src.api.auth_routes import auth_bp # Import the new auth blueprint
from src.extensions import db, migrate
from flask_jwt_extended import JWTManager # Import JWTManager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app) # Initialize Flask-JWT-Extended

    app.register_blueprint(admin_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(auth_bp) # Register the auth blueprint

    return app, db, migrate
