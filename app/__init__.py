from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from marshmallow import ValidationError # Import ValidationError

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()

def create_app():
    app = Flask(__name__)
    # 使用 SQLite 作為開發資料庫
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breakfast.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret-jwt-key'  # Change this in production!
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # Centralized Error Handling
    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(err):
        return jsonify(err.messages), 400

    @app.errorhandler(Exception)
    def handle_general_exception(e):
        # Log the exception for debugging purposes
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"message": "An unexpected error occurred."}), 500
    
    from app import models  # Import models here to register them with SQLAlchemy and Flask-Migrate
    
    api = Api(app)
    from app import api as api_module
    api_module.init_app(api)
    
    return app

