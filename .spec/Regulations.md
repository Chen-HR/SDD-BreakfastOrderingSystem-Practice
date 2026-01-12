# 專案規範：早餐店網路訂餐管理系統

## 版本資訊

- **版本**: 1.0
- **創建日期**: 2025-12-14
- **最後更新**: 2026-01-13

---

## 1. 使用者體驗與設計原則 (UX/UI)

### 1.1 移動優先 (Mobile-First) [必須遵守]

**原則**: 所有界面設計必須以行動裝置體驗為主要考量。

**具體要求**:

- 所有頁面必須在螢幕寬度 320px-428px 之間完全可用
- 觸控目標最小尺寸為 44x44 像素（符合 iOS Human Interface Guidelines）
- 所有文字在移動裝置上可讀性良好（最小字體 14px）
- 表單輸入必須針對移動鍵盤優化（正確的 input type）

**測試標準**:

- 所有功能必須通過 Chrome DevTools Mobile 模擬測試
- Lighthouse Mobile Score 必須 ≥ 90 分

### 1.2 視覺品質 (Visual Quality) [必須遵守]

**原則**: 菜單項目必須使用高品質圖片展示，提高用戶購買意願。

**具體要求**:

- 菜單圖片最低解析度: 800x600 像素
- 圖片格式: WebP（優先）或 JPEG（後備）
- 圖片壓縮: 必須小於 200KB，同時保持視覺品質
- 所有圖片必須提供 alt 文字（無障礙性）

### 1.3 極簡化操作 (Minimum Action) [必須遵守]

**原則**: 任何核心流程所需的步驟必須少於 3 個。

**具體要求**:

- 從進入 App 到完成點餐: ≤ 3 次點擊
- 結帳流程: 選擇餐點 → 確認訂單 → 選擇支付（3 步驟）
- 重複訂購: 1 次點擊（從歷史記錄）

**測試標準**:

- 使用者測試中，80% 的測試者能在 30 秒內完成首次點餐

---

## 2. 程式碼質量與測試標準 (Code Quality & Testing)

### 2.1 TDD 遵守 (TDD Adherence) [必須遵守]

**原則**: 所有業務邏輯和 API 服務必須先定義測試，再編寫實現。

**具體要求**:

- 每個新功能必須先撰寫單元測試（Red Phase）
- 測試覆蓋率必須 ≥ 90%（使用 pytest-cov 測量）
- 所有 API 端點必須有對應的整合測試
- BDD 驗收測試必須使用 Gherkin 語法撰寫

**禁止行為**:

- ❌ 先寫程式碼，再補測試
- ❌ 跳過測試階段直接實作
- ❌ 使用 `pytest.skip()` 跳過失敗的測試

**測試框架**:

- 單元測試: pytest
- BDD 測試: behave (Gherkin)
- 前端測試: Jest + React Testing Library

### 2.2 類型安全與風格 (Type Safety) [強烈建議]

**原則**: 使用嚴格的類型檢查減少運行時錯誤。

**具體要求**:

- Python 後端: 使用 Type Hints（PEP 484）
- TypeScript 前端: 啟用 `strict` 模式
- 所有公開函數必須標註參數和返回值類型
- 使用 mypy (Python) 和 tsc (TypeScript) 進行靜態類型檢查

---

## 3. 性能與可靠性約束 (Performance and Reliability)

### 3.1 關鍵 API 延遲 (Critical API Latency) [必須遵守]

**原則**: 涉及訂單創建、支付或狀態更新的 API，響應時間必須 < 1500ms。

**具體要求**:

- **關鍵端點** (P95 延遲 < 1500ms):
  - `POST /api/orders` (創建訂單)
  - `PUT /api/orders/{id}/status` (更新狀態)
  - `POST /api/payments` (支付處理)

- **一般端點** (P95 延遲 < 3000ms):
  - `GET /api/menu` (獲取菜單)
  - `GET /api/orders/{id}` (查詢訂單)

**監控與測試**:

- 使用 Apache Bench 或 Locust 進行負載測試
- 在 CI/CD 中自動執行性能回歸測試

### 3.2 錯誤處理 (Error Handling) [必須遵守]

**原則**: 所有後端服務必須實現強健的錯誤處理機制。

**標準化錯誤格式** (JSON):

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "人類可讀的錯誤訊息",
    "details": {
      "field": "具體的錯誤細節"
    },
    "timestamp": "ISO8601_TIMESTAMP"
  }
}
```

---

## 4. 安全與合規性 (Security and Compliance)

### 4.1 支付安全 (Payment Security) [必須遵守]

**原則**: 所有支付流程必須使用業界標準加密和安全協定。

**具體要求**:

- 所有 API 端點必須使用 HTTPS (TLS 1.3)
- 支付資料傳輸必須加密
- **禁止儲存**:
  - ❌ 完整信用卡號碼
  - ❌ CVV 安全碼
  - ❌ 信用卡到期日（除非經過 tokenization）

**認證機制**:

- 使用 OAuth 2.0 + JWT 進行用戶認證
- Token 有效期: 1 小時（存取）/ 7 天（更新）
- 密碼必須使用 bcrypt 雜湊（cost factor ≥ 12）

### 4.2 API 文檔 (API Documentation) [必須遵守]

**原則**: 所有 RESTful API 端點必須生成規範的 OpenAPI/Swagger 文檔。

**具體要求**:

- 使用 OpenAPI 3.0 規範
- 每個端點必須包含詳細描述、請求參數、響應格式
- API 文檔必須可透過 `/api/docs` 訪問

---

## 5. 版本控制與發布流程 (Version Control)

### 5.1 CI/CD 流程 [必須遵守]

**自動化檢查** (每次 Pull Request):

1. 單元測試 (pytest)
2. BDD 測試 (behave)
3. 程式碼風格檢查 (flake8, black)
4. 類型檢查 (mypy)
5. 安全漏洞掃描 (bandit)
6. 性能測試（關鍵端點）

---

## 簽署與生效

本規範自 2025-12-14 起生效，適用於「早餐店網路訂餐管理系統」專案的所有開發活動。
