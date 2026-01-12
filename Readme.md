# 早餐店網路訂餐管理系統 (Breakfast Ordering System)

## 專案概述

這是一個為忙碌的都市白領設計的早餐線上訂餐管理系統。目標是提供快速、便捷的早餐訂購體驗，並為餐廳管理員提供高效的訂單管理功能。

## Features

### 顧客端

*   **菜單瀏覽與購物車**: 快速瀏覽菜單，將餐點加入購物車，查看總價。
*   **訂單結帳與支付**: 支援多種支付方式（信用卡、Apple Pay、LINE Pay、現金支付），處理支付成功與失敗情況。
*   **訂單追蹤**: 即時追蹤訂單狀態，接收狀態變更通知，處理訂單延遲。
*   **用戶認證**: 註冊、登入功能 (JWT)。

### 管理員端

*   **訂單管理後台**: 清晰查看所有待處理訂單。
*   **訂單狀態更新**: 接受訂單、標記為待配送、取消訂單。

## 技術棧 (Technology Stack)

### 後端 (Backend)

*   **Python**: 3.x
*   **Flask**: 3.0+
*   **Flask-SQLAlchemy**: ORM
*   **Flask-Migrate**: 資料庫遷移
*   **Flask-JWT-Extended**: JWT 認證
*   **Flask-RESTx**: 構建 RESTful API 與自動生成 OpenAPI (Swagger) 文檔
*   **uv**: 套件管理器

### 資料庫 (Database)

*   **開發環境**: SQLite
*   **生產環境**: PostgreSQL

### 測試 (Testing)

*   **pytest**: 單元測試與整合測試
*   **behave**: BDD (行為驅動開發) 測試 (Gherkin 語法)

### 前端 (Frontend)

*   **Next.js**: 14+ (支援 SSR/SSG, SEO 友善, 移動優先)
*   **Redux Toolkit**: 狀態管理

## 本地開發環境設置 (Local Development Setup)

1.  **複製專案 (Clone the repository)**:
    ```bash
    git clone https://github.com/your-repo/SDD-BreakfastOrderingSystem-Practice.git
    cd SDD-BreakfastOrderingSystem-Practice
    ```

2.  **建立與啟用虛擬環境 (Create and activate virtual environment)**:
    我們使用 `uv` 作為套件管理器。
    ```bash
    uv venv
    .\.venv\Scripts\Activate.ps1 # For PowerShell
    # source ./.venv/bin/activate # For Bash/Zsh
    ```

3.  **安裝依賴 (Install dependencies)**:
    ```bash
    uv pip install -r requirements.txt # Or uv pip install -e .
    ```
    (Note: Assuming a `requirements.txt` will be generated or `-e .` is used for installable package. For now, `uv pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-restx python-dotenv` might be needed if no `requirements.txt` is present.)

4.  **設定環境變數 (Configure environment variables)**:
    創建 `.env` 文件在專案根目錄，並添加必要的配置。
    ```
    FLASK_APP=main.py
    FLASK_ENV=development
    SECRET_KEY=your_super_secret_key_here
    DATABASE_URL=sqlite:///instance/project.db
    JWT_SECRET_KEY=your_jwt_secret_key_here
    ```

5.  **資料庫遷移 (Database Migrations)**:
    初始化資料庫並應用遷移。
    ```bash
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

## 運行應用程式 (Running the Application)

### 後端 (Backend)

確保虛擬環境已啟用。
```bash
flask run
```
應用程式將會在 `http://127.0.0.1:5000` 運行。

### 前端 (Frontend)

(前端開發說明將在前端專案完成後補充)

## API 文件 (API Documentation)

後端 API 文件由 Flask-RESTx 自動生成，並遵循 OpenAPI 3.0 規範。
運行後端應用程式後，可透過以下網址訪問：
`http://127.0.0.1:5000/api/v1/api/docs`

## 測試 (Testing)

### 單元測試與整合測試

```bash
pytest
```

### BDD (行為驅動開發) 測試

```bash
behave features/
```

## 資料庫遷移 (Database Migrations)

當資料庫模型 (在 `src/models.py`) 發生變更時，請按照以下步驟生成並應用新的遷移：

1.  **生成遷移腳本**:
    ```bash
    flask db migrate -m "Your descriptive message for the changes"
    ```
2.  **應用遷移**:
    ```bash
    flask db upgrade
    ```

---
