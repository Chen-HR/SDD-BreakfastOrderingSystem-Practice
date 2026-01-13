from flask_restful import Api

def init_app(api: Api):
    from .admin import AdminOrdersResource, OrderStatusResource
    from .customer import OrderCreationResource, MenuResource
    from .auth import UserRegister, UserLogin

    api.add_resource(AdminOrdersResource, '/api/v1/admin/orders')
    api.add_resource(OrderStatusResource, '/api/v1/orders/<int:order_id>/status')
    api.add_resource(OrderCreationResource, '/api/v1/orders')
    api.add_resource(MenuResource, '/api/v1/menu')
    api.add_resource(UserRegister, '/api/v1/register')
    api.add_resource(UserLogin, '/api/v1/login')