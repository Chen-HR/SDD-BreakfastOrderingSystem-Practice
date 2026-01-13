from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    # 使用 SQLite 作為開發資料庫
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breakfast.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from app import models  # Import models here to register them with SQLAlchemy and Flask-Migrate
    
    api = Api(app)
    from app import api as api_module
    api_module.init_app(api)
    
    return app

