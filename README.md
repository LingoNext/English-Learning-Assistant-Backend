## RESTful API 標準規格
> /auth/ 可行。/ai/conversation 待確認可行性。

### 表格1：API 端點規格表

| 資源路徑 | 操作名稱 | HTTP方法 | 請求參數 | 回應 data | 狀態碼 | 備註 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `/auth/login/` | 用戶登入 | POST | email, password | token | 200, 400, 401 | - |
| `/auth/verification/send/` | 發送驗證碼 | POST | email | - | 200, 400 | - |
| `/auth/registration/confirm/` | 註冊確認 | POST | email, password,code, name,  | - | 201, 400, 409 | - |
| `/auth/password/reset/confirm/` | 密碼重設 | POST | email, password, code | - | 200, 400, 401 | - |
| `/auth/delete_account/` | 刪除帳號 | POST | email, password | - | 204, 400, 401 | 需攜帶 token |
| `/auth/user/` | 取得用戶資料 | GET | - | email, name | 200, 401 | 需攜帶 token |
| `/auth/user/` | 更新用戶資料 | PUT | name | - | 200, 400, 401 | 需攜帶 token |

### 表格2：資料欄位規格表


#### 用戶身份驗證相關

- Verification (自建)

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| id       | uuid         | 是       | 無     | 驗證碼唯一識別碼   |
| email    | varchar(254) | 是       | 無     | 用戶電子郵件地址   |
| code     | varchar(6)   | 是       | 無     | 六位數驗證碼       |
| createdAt| timestamptz  | 是       | now()  | 驗證碼創建時間     |

- auth_user（Django 內建）

| 欄位名稱   | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| id         | int     | 是       | 無     | 使用者唯一識別碼   |
| username   | varchar(150) | 是       | 無     | 帳號              |
| password   | varchar(128) | 是       | 無     | 密碼雜湊值         |
| email      | varchar(254) | 是       | 無     | 電子郵件           |
| name       | varchar(150) | 否       | 無     | 姓名               |
| date_joined| datetime     | 是       | now()  | 建立時間           |

- authtoken_token（安裝 rest_framework.authtoken）

| 欄位名稱 | 資料型別     | 是否必填 | 預設值 | 說明           |
|:-:|:-:|:-:|:-:|:-:|
| key      | varchar(40)| 是       | 無     | Token 值       |
| user_id  | int        | 是       | 無     | 關聯使用者主鍵  |
| created  | datetime   | 是       | now()  | 建立時間       |

#### AI 互動相關

## 備註

1. **身份驗證**: 使用 Django Token Authentication，登入後大多的操作請求標頭中包含 `Authorization: Token <your-token>`。
2. **時間格式**: 所有時間欄位均使用 ISO 8601 格式 (例: `2025-08-08T10:30:00Z`)以利資料一致性與排序，但前端可以根據需要轉換為其他格式（如 yyyy/mm/dd）。
3. **字元編碼**: 所有文字內容使用 UTF-8 編碼，不然前端 flutter 收到 Response 的 message 有中文會變成亂碼。
4. **內容類型**: 所有請求和回應均使用 `application/json` 格式，除語音 `multipart/form-data`。
5. **電子郵件驗證**: 系統會寄送一次性驗證碼至用戶電子郵件，使用者需在註冊或重設密碼時提供此驗證碼。
6. **Token 生命週期**: Token 永不過期。登出時前端丟棄 Token 就好。
7. **請求速率限制**: 為防止濫用，系統對每個用戶的請求頻率進行限制(未來擴充，可以不做)。
8. **Response 格式**: 所有 API 的回應均使用統一的格式，包含 `status`、`message` 和 `data` 三個欄位。

## Request/Response 範例

### 使用上的共通 Header
- Content-Type: application/json (除了語音使用的是 multipart/form-data)

### 1) /auth/login/ — POST
- 描述：取得 Token
- Request 範例:
```json
{
	"email": "user@example.com",
	"password": "Str0ngP@ssw0rd"
}
```
- 成功 Response (200):
```json
{   
    "message": "登入成功，歡迎使用者!",
	"token": "0123456789abcdef0123456789abcdef01234567",
}
```

### 2) /auth/verification/send/ — POST
- 描述：發送驗證碼（註冊/重設密碼），驗證碼會寄送到用戶電子郵件，五分鐘內有效
- Request 範例:
```json
{
	"email": "user@example.com",
}
```
- 成功 Response (200):
```json
{
	"message": "驗證碼已發送至 user@example.com"
}
```

### 3) /auth/registration/confirm/ — POST
- 描述：使用驗證碼完成註冊
- Request 範例:
```json
{
	"email": "user@example.com",
	"password": "Str0ngP@ssw0rd",
	"name": "使用者",
	"code": "123456"
}
```
- 成功 Response (201):
```json
{
	"message": "註冊完成",
}
```

### 4) /auth/password/reset/confirm/ — POST
- 描述：使用驗證碼重設密碼
- Request 範例:
```json
{
	"email": "user@example.com",
	"code": "123456",
	"password": "NewStr0ngP@ss",
}
```
- 成功 Response (200):
```json
{
	"message": "密碼重設成功"
}
```

### 5) /auth/delete_account/ — POST
- 描述：刪除當前用戶帳號。不用驗證碼，直接使用 Token 更方便且安全。
- Headers: Authorization: Token <your-token>
- Request 範例:
```json
{
	"email": "user@example.com",
	"password": "Str0ngP@ssw0rd"
}
```
- 成功 Response (204):
```json
{
	"message": "帳號已刪除"
}
```

### 6) /auth/user/ — GET
- 描述：取得當前用戶資料
- Headers: Authorization: Token <your-token>
- 成功 Response (200):
```json
{
	"email": "user@example.com",
	"name": "使用者",
}
```

### 7) /auth/user/ — POST
- 描述：更新使用者資訊。只能更新名稱，其他資訊不可更改。
- Headers: Authorization: Token <your-token>
- Request 範例:
```json
{
	"name": "新名字"
}
```
- 成功 Response (200):
```json
{
	"message": "使用者資訊已更新",
}
```


