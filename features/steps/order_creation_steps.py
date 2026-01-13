from behave import *
from flask import json
from app import db
from app.models import User, MenuItem, Order, OrderItem

@given('a user "{username}" with email "{email}" and password "{password}" exists')
def step_impl(context, username, email, password):
    with context.app.app_context():
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        context.user = user # Store user for later steps
        context.users = getattr(context, 'users', {})
        context.users[username] = user

@given('a menu item "{name}" with price {price:f} and stock {stock:d} exists')
def step_impl(context, name, price, stock):
    with context.app.app_context():
        menu_item = MenuItem(name=name, price=price, stock=stock)
        db.session.add(menu_item)
        db.session.commit()
        db.session.refresh(menu_item)
        context.menu_items = getattr(context, 'menu_items', {})
        context.menu_items[name] = menu_item

@when('the user "{username}" tries to create an order with:')
def step_impl(context, username):
    user = context.users.get(username)
    assert user is not None, f"User {username} not found in context"

    items_data = []
    for row in context.table:
        item_name = row['item_name']
        quantity = int(row['quantity'])
        menu_item = context.menu_items.get(item_name)
        
        if menu_item:
            items_data.append({'item_id': menu_item.id, 'quantity': quantity})
        else:
            items_data.append({'item_id': 99999, 'quantity': quantity})

    request_payload = {
        'user_id': user.id,
        'items': items_data
    }
    context.response = context.client.post('/api/v1/orders', json=request_payload)
    context.response_json = context.response.get_json()

@when('a non-existent user "{username}" tries to create an order with:')
def step_impl(context, username):
    items_data = []
    for row in context.table:
        item_name = row['item_name']
        quantity = int(row['quantity'])
        menu_item = context.menu_items.get(item_name)
        if menu_item:
            items_data.append({'item_id': menu_item.id, 'quantity': quantity})
        else:
            items_data.append({'item_id': 99999, 'quantity': quantity})
            
    request_payload = {
        'user_id': 999, # Non-existent user ID
        'items': items_data
    }
    context.response = context.client.post('/api/v1/orders', json=request_payload)
    context.response_json = context.response.get_json()

@then('the order should be created successfully')
def step_impl(context):
    assert context.response.status_code == 201
    assert 'Order created successfully' in context.response_json['message']
    assert context.response_json['order_id'] is not None
    context.order_id = context.response_json['order_id']

@then('the order total should be {expected_total:f}')
def step_impl(context, expected_total):
    assert context.response_json['total_amount'] == expected_total

@then('the stock for "{item_name}" should be {expected_stock:d}')
def step_impl(context, item_name, expected_stock):
    with context.app.app_context():
        menu_item_from_context = context.menu_items.get(item_name)
        assert menu_item_from_context is not None, f"MenuItem {item_name} not found in context"
        
        # Re-query the menu item to ensure it's attached to the current session
        menu_item = db.session.get(MenuItem, menu_item_from_context.id)
        assert menu_item is not None, f"MenuItem {item_name} not found in database after API call"
        assert menu_item.stock == expected_stock

@then('the order creation should fail with message "{message_pattern}"')
def step_impl(context, message_pattern):
    assert context.response.status_code != 201
    assert context.response_json is not None
    import re
    assert re.search(message_pattern, context.response_json['message']) is not None
