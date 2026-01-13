from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    # 使用 SQLite 作為開發資料庫
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///breakfast.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    
    from app import models  # Import models here to register them with SQLAlchemy and Flask-Migrate
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app
