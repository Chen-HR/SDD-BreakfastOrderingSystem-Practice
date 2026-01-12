Feature: 客戶訂單創建流程

  作為一個已登入的客戶
  我希望能夠將選定的餐點加入購物車
  並成功送出訂單
  以便享用早餐

  Background:
    Given 系統中存在以下菜單項目：
      | item_id | name       | price | stock |
      | 001     | 經典蛋餅   | 35    | 50    |
      | 002     | 冰美式咖啡 | 45    | 30    |
      | 003     | 培根蛋三明治 | 55  | 20    |
    And 系統中存在一位名為 "測試用戶" (user_id: b0d5c0e0-0a0c-4c0d-8c0b-0d0c0a0d0c0b, email: "test@example.com", password: "password123") 的已註冊客戶
    And "測試用戶" 已成功登入
    And "測試用戶" 的購物車為空

  Scenario: 成功送出訂單
    When "測試用戶" 將 "經典蛋餅" (數量: 2) 加入購物車
    And "測試用戶" 將 "冰美式咖啡" (數量: 1) 加入購物車
    And "測試用戶" 選擇送貨地址 "台北市信義區測試路100號"
    And "測試用戶" 送出訂單
    Then 訂單應成功創建
    And 訂單總金額應為 115 元
    And "經典蛋餅" 的剩餘庫存應為 48 份
    And "冰美式咖啡" 的剩餘庫存應為 29 份
    And "測試用戶" 應收到訂單確認通知

  Scenario: 因庫存不足導致訂單送出失敗
    Given "經典蛋餅" 的剩餘庫存為 1 份
    When "測試用戶" 將 "經典蛋餅" (數量: 2) 加入購物車
    And "測試用戶" 選擇送貨地址 "台北市信義區測試路100號"
    And "測試用戶" 送出訂單
    Then 訂單應創建失敗
    And 系統應顯示錯誤訊息 "Insufficient stock for 經典蛋餅. Available: 1, Requested: 2"
    And "經典蛋餅" 的剩餘庫存應為 1 份

  Scenario: 送出空購物車導致訂單失敗
    When "測試用戶" 送出訂單
    Then 訂單應創建失敗
    And 系統應顯示錯誤訊息 "Items are required to create an order"
