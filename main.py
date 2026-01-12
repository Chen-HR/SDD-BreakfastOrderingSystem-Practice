from src.app import create_app, db
from src.models import User, MenuItem, Order, OrderItem

app, db, migrate = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'MenuItem': MenuItem, 'Order': Order, 'OrderItem': OrderItem}

if __name__ == '__main__':
    app.run()
