from behave import fixture, use_fixture
from app import create_app, db
from app.models import User, MenuItem, Order, OrderItem

@fixture
def flask_app(context, timeout=30):
    # This fixture sets up the Flask app and an application context
    # It will run once per test run, and the app context will be pushed/popped per scenario
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # Use in-memory SQLite for testing
    })
    context.app = app
    context.client = app.test_client()
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()

def before_scenario(context, scenario):
    use_fixture(flask_app, context)
    # Clear database for each scenario to ensure isolation
    with context.app.app_context():
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(MenuItem).delete()
        db.session.query(User).delete()
        db.session.commit()
    context.users = {}
    context.menu_items = {}
    context.order_id = None
    context.response = None
    context.response_json = None
