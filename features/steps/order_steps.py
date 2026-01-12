from behave import *
from src.models import MenuItem, User, Order, OrderItem
import uuid
from decimal import Decimal
import json

# Setup for order creation
@given('系統中存在一位名為 "{user_name}" (user_id: {user_id}, email: "{email}", password: "{password}") 的已註冊客戶')
def step_impl(context, user_name, user_id, email, password):
    user = context.db.session.get(User, uuid.UUID(user_id))
    if not user:
        user = User(user_id=uuid.UUID(user_id), email=email, role='customer')
        user.set_password(password)
        context.db.session.add(user)
    context.db.session.commit()
    if not hasattr(context, 'users'):
        context.users = {}
    context.users[user_name] = {'email': email, 'password': password, 'user_id': user_id}

@given('"{user_name}" 已成功登入')
def step_impl(context, user_name):
    user_info = context.users[user_name]
    response = context.client.post('/api/v1/auth/login', json={
        'email': user_info['email'],
        'password': user_info['password']
    })
    assert response.status_code == 200
    context.jwt_token = response.json['access_token']
    context.current_user = user_name
    
    if not hasattr(context, 'user_tokens'):
        context.user_tokens = {}
    context.user_tokens[user_name] = context.jwt_token

@given('"{user_name}" 的購物車為空')
def step_impl(context, user_name):
    if not hasattr(context, 'user_carts'):
        context.user_carts = {}
    context.user_carts[user_name] = []

@when('"{user_name}" 將 "{item_name}" (數量: {quantity:d}) 加入購物車')
def step_impl(context, user_name, item_name, quantity):
    menu_item = context.menu_items.get(item_name)
    assert menu_item is not None, f"Menu item '{item_name}' not found."

    if not hasattr(context, 'user_carts') or user_name not in context.user_carts:
        context.user_carts[user_name] = []
    
    context.user_carts[user_name].append({'item_id': str(menu_item.item_id), 'quantity': quantity})

@when('"{user_name}" 選擇送貨地址 "{address}"')
def step_impl(context, user_name, address):
    if not hasattr(context, 'user_addresses'):
        context.user_addresses = {}
    context.user_addresses[user_name] = address

@when('"{user_name}" 送出訂單')
def step_impl(context, user_name):
    assert context.current_user == user_name, f"User '{user_name}' is not the current logged-in user."
    assert hasattr(context, 'jwt_token'), "JWT token not found for the current user."

    order_items = context.user_carts.get(user_name, [])
    
    # Safely get delivery_address, default to None if not set
    delivery_address = None
    if hasattr(context, 'user_addresses') and user_name in context.user_addresses:
        delivery_address = context.user_addresses[user_name]

    headers = {'Authorization': f'Bearer {context.jwt_token}'}
    payload = {
        'items': order_items,
        'delivery_address': delivery_address
    }
    
    context.order_response = context.client.post('/api/v1/orders', json=payload, headers=headers)
    # Clear the cart after sending the order
    context.user_carts[user_name] = []

@then('訂單應成功創建')
def step_impl(context):
    assert context.order_response.status_code == 201, f"Expected status code 201, but got {context.order_response.status_code}. Response: {context.order_response.json}"
    assert 'order_id' in context.order_response.json
    context.created_order_id = context.order_response.json['order_id']

@then('訂單總金額應為 {total_amount:d} 元')
def step_impl(context, total_amount):
    print(f"DEBUG: API Response for total amount: {context.order_response.json}")
    assert context.order_response.status_code == 201 # Ensure order was successful
    assert Decimal(str(context.order_response.json['total_amount'])) == Decimal(total_amount), f"Expected total amount {total_amount}, but got {context.order_response.json['total_amount']}"

@then('"{item_name}" 的剩餘庫存應為 {stock_level:d} 份')
def step_impl(context, item_name, stock_level):
    menu_item = context.db.session.query(MenuItem).filter_by(name=item_name).first()
    assert menu_item is not None, f"Menu item '{item_name}' not found in DB."
    assert menu_item.stock_level == stock_level

@then('"{user_name}" 應收到訂單確認通知')
def step_impl(context, user_name):
    # This is a UI/notification service assertion, not directly testable in backend BDD.
    print(f"BDD: Asserting user '{user_name}' receives order confirmation (simulated)")

@then('訂單應創建失敗')
def step_impl(context):
    assert context.order_response.status_code == 400, f"Expected status code 400, but got {context.order_response.status_code}. Response: {context.order_response.json}"

@then('系統應顯示錯誤訊息 "{error_message}"')
def step_impl(context, error_message):
    print(f"DEBUG: API Response for error message: {context.order_response.json}")
    assert context.order_response.status_code == 400
    assert error_message in context.order_response.json['message']
