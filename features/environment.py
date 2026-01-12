from src.app import create_app, db as _db

def before_all(context):
    app, _, _ = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    context.app = app
    context.client = app.test_client()
    context.db = _db
    
def before_scenario(context, scenario):
    context.app_context = context.app.app_context()
    context.app_context.push()
    context.db.create_all()
    # Start a transaction for each scenario
    context.connection = context.db.engine.connect()
    context.transaction = context.connection.begin()
    context.db.session.begin_nested() # Start a nested transaction for the session

def after_scenario(context, scenario):
    if hasattr(context, 'transaction') and context.transaction:
        context.transaction.rollback() # Rollback the outer transaction
        context.connection.close()
    context.db.drop_all()
    context.app_context.pop()

def after_all(context):
    pass
