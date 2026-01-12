import pytest
from src.app import create_app, db as _db

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    app, _, _ = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """Function-scoped database fixture."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        _db.session.begin_nested()

        yield _db

        transaction.rollback()
        connection.close()
        _db.session.remove()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()
