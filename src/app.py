from flask import Flask
from .config import Config
from src.api.routes import admin_bp
from src.extensions import db, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(admin_bp)

    return app, db, migrate
