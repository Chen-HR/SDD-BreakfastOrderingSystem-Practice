# 部署文件：早餐店網路訂餐管理系統

## 1. 概述

本文件將提供早餐店網路訂餐管理系統後端應用程式的部署指南。前端應用程式 (Next.js) 的部署將由 Vercel 負責。後端將部署到通用的雲端平台（例如 AWS EC2/ECS, Google Cloud Run/App Engine 或 Heroku），並使用 PostgreSQL 作為生產資料庫。

## 2. 前置準備

*   選定的雲端平台帳戶 (例如 AWS, GCP, Heroku)。
*   Docker 及 Docker Compose (用於本地測試部署)。
*   Git。
*   Python 環境與 uv。

## 3. 資料庫設定 (PostgreSQL)

在您選定的雲端平台上建立一個 PostgreSQL 資料庫實例。記下以下連接資訊：

*   資料庫名稱 (DB Name)
*   使用者名稱 (DB User)
*   密碼 (DB Password)
*   主機 (DB Host)
*   埠號 (DB Port)

這些資訊將用於配置後端應用程式的 `DATABASE_URL`。

## 4. 後端部署 (Flask Application)

以下以容器化部署 (Docker) 為例。您也可以根據雲端平台的特性選擇其他部署方式 (例如直接部署 Python 應用)。

### 4.1 建構 Docker 映像檔

在專案根目錄下，使用以下命令建構 Docker 映像檔：

```bash
docker build -t breakfast-ordering-backend:latest .
```

### 4.2 推送映像檔至容器註冊服務

將建構好的映像檔推送到您雲端平台提供的容器註冊服務 (例如 AWS ECR, Google Container Registry)。

```bash
# 登入您的容器註冊服務
# docker push your-registry/breakfast-ordering-backend:latest
```

### 4.3 部署服務

根據您選擇的雲端平台，建立一個服務來運行後端容器：

*   **AWS ECS/EKS**: 建立一個 ECS Task Definition 和 Service，指向您的容器映像檔。
*   **Google Cloud Run**: 將映像檔部署到 Cloud Run 服務。
*   **Heroku**: 使用 Heroku Container Registry。

確保將服務配置為監聽 Port 5000。

## 5. 環境變數配置

在雲端平台的環境配置中，設定以下必要的環境變數：

*   `FLASK_APP=main.py`
*   `FLASK_ENV=production`
*   `SECRET_KEY=your_strong_flask_secret_key` (請務必生成一個強大的密鑰)
*   `JWT_SECRET_KEY=your_strong_jwt_secret_key` (請務必生成一個強大的密鑰)
*   `DATABASE_URL=postgresql://user:password@host:port/db_name` (使用步驟 3 中 PostgreSQL 的連接資訊)

## 6. 運行資料庫遷移

在部署應用程式後，需要手動或透過 CI/CD 流程執行資料庫遷移。這通常在應用程式服務啟動前或作為啟動程序的一部分執行。

```bash
# 範例：在部署的容器中執行
docker exec <backend_container_id> flask db upgrade
```
或者，如果您的雲端平台提供運行一次性任務的功能，則使用該功能。

## 7. 監控與日誌

配置雲端平台的監控和日誌服務，以追蹤應用程式的性能和錯誤。確保 Flask 應用程式的日誌輸出被正確捕獲和儲存。

## 8. CI/CD 整合

建議設定 CI/CD 管道，自動化測試、建構映像檔、推送映像檔和部署的流程。

---
