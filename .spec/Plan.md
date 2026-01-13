# 技術計畫：早餐店網路訂餐管理系統

## 文件資訊

- **版本**: 1.0
- **依據規格**: Spec.md v1.0
- **依據規範**: Regulations.md v1.0

---

## 1. 整體架構

### 1.1 技術棧總覽

| 層級 | 技術 | 版本 | 理由 |
| ------ | ------ | ------ | ------ |
| 前端 | Next.js | 14+ | 支援 SSR/SSG，SEO 友善，移動優先 |
| 狀態管理 | Redux Toolkit | 最新 | 可預測的狀態管理 |
| 後端 | Flask | 3.0+ | 輕量級，靈活，適合 MVP |
| ORM | Flask-SQLAlchemy | 最新 | 與 Flask 深度整合 |
| 資料庫 (Dev) | SQLite | 3.x | 零配置，快速開發 |
| 認證 | JWT | - | 無狀態、適合 REST API |
| 測試 | pytest, behave | 最新 | TDD/BDD 支援 |

---

## 2. 資料庫設計

### 2.1 實體關係圖 (ERD)

- **User**: 儲存顧客與管理員 (One-to-Many -> Orders)
- **MenuItem**: 儲存菜單項目 (One-to-Many -> OrderItems)
- **Order**: 訂單主表 (One-to-Many -> OrderItems)
- **OrderItem**: 訂單明細 (Many-to-Many 關聯表)

### 2.2 詳細資料表定義

#### Table: `users`

| 欄位名稱 | 資料類型 | 說明 |
| --------- | --------- | ------ |
| `user_id` | UUID (PK) | 主鍵 |
| `email` | VARCHAR | 唯一，登入帳號 |
| `password_hash` | VARCHAR | bcrypt 雜湊 |
| `role` | ENUM | `customer` 或 `admin` |
| `created_at` | TIMESTAMP | 註冊時間 |

#### Table: `menu_items`

| 欄位名稱 | 資料類型 | 說明 |
| --------- | --------- | ------ |
| `item_id` | UUID (PK) | 主鍵 |
| `name` | VARCHAR | 餐點名稱 |
| `price` | DECIMAL | 價格 |
| `image_url` | VARCHAR | 圖片 URL |
| `stock_level` | INTEGER | 庫存 |
| `is_available` | BOOLEAN | 是否供應 |

#### Table: `orders`

| 欄位名稱 | 資料類型 | 說明 |
| --------- | --------- | ------ |
| `order_id` | UUID (PK) | 主鍵 |
| `user_id` | UUID (FK) | 關聯用戶 |
| `order_number` | VARCHAR | ORD-YYYYMMDD-XXX |
| `total_amount` | DECIMAL | 總金額 |
| `status` | ENUM | pending, in_progress, ready_for_delivery, delivered, cancelled |
| `delivery_address`| TEXT | 配送地址 |

#### Table: `order_items`

| 欄位名稱 | 資料類型 | 說明 |
| --------- | --------- | ------ |
| `item_id` | UUID (PK) | 主鍵 |
| `order_id` | UUID (FK) | 關聯訂單 |
| `menu_item_id` | UUID (FK) | 關聯菜單 |
| `quantity` | INTEGER | 數量 |
| `unit_price` | DECIMAL | 當時單價 |
| `subtotal` | DECIMAL | 小計 |

---

## 3. API 端點定義

### 3.1 認證相關

- `POST /api/v1/auth/register`: 註冊
- `POST /api/v1/auth/login`: 登入 (返回 JWT)

### 3.2 菜單相關

- `GET /api/v1/menu`: 獲取菜單 (支援 category, available 篩選)

### 3.3 訂單相關

- `POST /api/v1/orders`: 創建訂單 (需 Auth)
- `GET /api/v1/orders/:order_id`: 查詢訂單詳情
- `PUT /api/v1/orders/:order_id/status`: 更新狀態 (僅 Admin)

### 3.4 管理員 API

- `GET /api/v1/admin/orders`: 獲取訂單列表 (支援分頁、篩選)

---

## 4. 測試與部署

### 4.1 測試策略

- **單元測試**: 使用 pytest 測試 Models 與 Services (覆蓋率 > 90%)
- **整合測試**: 測試 API 端點與資料庫交互
- **BDD 測試**: 使用 behave 測試 spec.md 中的場景

### 4.2 部署架構

- **前端**: Next.js (Vercel)
- **後端**: Flask (AWS/GCP/Heroku)
- **資料庫**: PostgreSQL (Prod), SQLite (Dev)
