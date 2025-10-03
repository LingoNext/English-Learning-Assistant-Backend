## RESTful API 標準規格
待續
### 表格1：API 端點規格表

| 資源路徑 | 操作名稱 | HTTP方法 | 請求參數 | 回應 data | 狀態碼 | 備註 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `/auth/login/` | 用戶登入 | POST | email, password | refresh_token、access_token | 200, 400, 401 | - |
| `token/refresh/` | 重新整理 Token | POST | refresh_token | new_token | 200, 400, 401 | - |
| `token/verify/` | 驗證 Token | POST | access_token | - | 200, 400, 401 | - |
| `/auth/verification/send/` | 發送驗證碼 | POST | email | - | 200, 400 | 傳送至用戶電子郵件 |
| `/auth/registration/confirm/` | 註冊確認 | POST | email, password,verification_code, name,  | - | 201, 400, 409 | - |
| `/auth/password/reset/confirm/` | 密碼重設 | POST | email, password, code | - | 200, 400, 401 | - |
| `/auth/delete_account/` | 刪除帳號 | POST | email, password | - | 204, 400, 401 | 需攜帶 access_token |
| `/auth/user/` | 取得用戶資料 | GET | - | email, name | 200, 401 | 需攜帶 access_token |
| `/auth/user/` | 更新用戶資料 | PUT | new_name | - | 200, 400, 401 | 需攜帶 access_token |

### 表格2：資料欄位規格表


#### 用戶身份驗證相關

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |

#### 深度對話相關

## 備註

1. **身份驗證**: 使用 Simple JWT，登入後驗證請求標頭中包含 `Authorization: Bearer <your-token>`。
2. **時間格式**: 所有時間欄位均使用 ISO 8601 格式 (例: `2025-08-08T10:30:00Z`)以利資料一致性與排序，但前端可以根據需要轉換為其他格式（如 yyyy/mm/dd）。
3. **字元編碼**: 所有文字內容使用 UTF-8 編碼，不然前端 flutter 收到 Response 的 message 有中文會變成亂碼。
4. **內容類型**: 所有請求和回應均使用 `application/json` 格式，除語音 `multipart/form-data`。
5. **電子郵件驗證**: 系統會寄送一次性驗證碼至用戶電子郵件，使用者需在註冊或重設密碼時提供此驗證碼。
6. **Token 生命週期**: Access Token 會在 1 小時後過期，Refresh Token 會在 7 天後過期。登出時前端丟棄 Token 就好。
7. **請求速率限制**: 為防止濫用，系統對每個用戶的請求頻率進行限制(未來擴充，可以不做)。
8. **Response 格式**: 所有 API 的回應均使用統一的格式，包含 `status`、`message` 和 `data` 三個欄位。

## Request/Response 範例

