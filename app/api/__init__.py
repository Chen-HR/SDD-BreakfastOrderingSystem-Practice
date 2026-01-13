from flask_restful import Api

def init_app(api: Api):
    from .admin import AdminOrdersResource, OrderStatusResource
    from .customer import OrderCreationResource
    api.add_resource(AdminOrdersResource, '/api/v1/admin/orders')
    api.add_resource(OrderStatusResource, '/api/v1/orders/<int:order_id>/status')
    api.add_resource(OrderCreationResource, '/api/v1/orders')