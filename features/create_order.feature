Feature: Order Creation Process

  Scenario: Successful order creation with valid user and sufficient stock
    Given a user "test_customer" with email "customer@example.com" and password "secure_pass" exists
    And a menu item "Pizza" with price 12.50 and stock 10 exists
    And a menu item "Coke" with price 2.00 and stock 5 exists
    When the user "test_customer" tries to create an order with:
      | item_name | quantity |
      | Pizza     | 1        |
      | Coke      | 2        |
    Then the order should be created successfully
    And the order total should be 16.50
    And the stock for "Pizza" should be 9
    And the stock for "Coke" should be 3

  Scenario: Order creation fails due to insufficient stock
    Given a user "stock_customer" with email "stock@example.com" and password "secure_pass" exists
    And a menu item "Burger" with price 8.00 and stock 5 exists
    When the user "stock_customer" tries to create an order with:
      | item_name | quantity |
      | Burger    | 6        |
    Then the order creation should fail with message "Not enough stock for Burger"
    And the stock for "Burger" should be 5

  Scenario: Order creation fails for a non-existent user
    Given a menu item "Salad" with price 7.00 and stock 5 exists
    When a non-existent user "non_existent" tries to create an order with:
      | item_name | quantity |
      | Salad     | 1        |
    Then the order creation should fail with message "User with ID .* not found"

  Scenario: Order creation fails for a non-existent menu item
    Given a user "item_customer" with email "item@example.com" and password "secure_pass" exists
    And a menu item "Soup" with price 4.00 and stock 5 exists
    When the user "item_customer" tries to create an order with:
      | item_name | quantity |
      | Soup      | 1        |
      | NonExistentItem | 1  |
    Then the order creation should fail with message "MenuItem with ID .* not found"
