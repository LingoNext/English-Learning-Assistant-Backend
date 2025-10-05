## RESTful API 標準規格

### 表格1：API 端點規格表

| 資源路徑 | 操作名稱 | HTTP方法 | 請求參數 | 回應 data | 狀態碼 | 備註 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `/auth/login/` | 用戶登入 | POST | email, password | refresh_token、access_token | 200, 400, 401 | - |
| `token/refresh/` | 重新整理 Token | POST | refresh_token | new_token | 200, 400, 401 | - |
| `token/verify/` | 驗證 Token | POST | access_token | - | 200, 400, 401 | - |
| `/auth/verification/send/` | 發送驗證碼 | POST | email | - | 200, 400 | verification_code 傳送至用戶電子郵件 |
| `/auth/registration/confirm/` | 註冊確認 | POST | email, password, verification_code, name | - | 201, 400, 409 | - |
| `/auth/password/reset/confirm/` | 密碼重設 | POST | email, password, verification_code | - | 200, 400, 401 | - |
| `/auth/delete_account/` | 刪除帳號 | POST | email, password | - | 204, 400, 401 | 需攜帶 access_token |
| `/auth/user/` | 取得用戶資料 | GET | - | email, name, level | 200, 401 | 需攜帶 access_token |
| `/auth/user/` | 更新用戶資料 | PUT | new_name, level | - | 200, 400, 401 | 需攜帶 access_token |
| `/api/chat/` | 發送聊天訊息 | POST | message | message_object (含分析) | 200, 400, 401, 500 | 需攜帶 access_token，返回 AI 回覆及語言分析 |
| `/api/history/` | 取得聊天歷史 | GET | limit, offset | messages_array | 200, 401 | 需攜帶 access_token，支援分頁 |
| `/api/message/{id}/` | 取得特定訊息 | GET | - | message_object | 200, 401, 404 | 需攜帶 access_token，用於輪詢檢查訊息狀態 |
| `/llm/infer/` | LLM 推理服務 | POST | message_id, user_id, text, user_level | reply, grammar_errors, vocab_difficulty, misc | 200, 400, 500 | 內部服務 API，由 Django 後端呼叫 |

### 表格2：資料欄位規格表

#### 用戶身份驗證相關 User (AbstractUser 擴展)
- 因為 django-rest-framework-simplejwt 已經定義好 token 的欄位，所以這邊不重複定義。
- 使用 Django 內建的 AbstractUser 作為基礎，擴展用戶資料。
- 驗證碼的欄位不存資料庫，是存在快取中 (cache)，所以也不列在這邊。

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| username   | string         | 是       | -     | 用戶名稱（繼承自 AbstractUser） |
| email      | string (email) | 是       | -     | 用戶電子郵件                  |
| password   | string         | 是       | -     | 用戶密碼，需加密存儲           |
| first_name | string         | 否       | ""    | 用戶名字（繼承自 AbstractUser） |
| last_name  | string         | 否       | ""    | 用戶姓氏（繼承自 AbstractUser） |
| level      | string         | 否       | "A2"  | CEFR 英語程度等級（A1, A2, B1, B2, C1, C2） |
| is_active  | boolean        | 否       | True  | 用戶帳號是否啟用             |
| is_staff   | boolean        | 否       | False | 用戶是否為管理員             |
| is_superuser | boolean      | 否       | False | 用戶是否為超級管理員          |
| date_joined | datetime      | 否       | -     | 帳號註冊時間（繼承自 AbstractUser） |
| last_login | datetime       | 否       | -     | 最後登入時間（繼承自 AbstractUser） |
| created_at | datetime       | 否       | -     | 帳號建立時間（自動生成）       |

#### 聊天訊息相關 Message

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| id         | integer        | 是       | -     | 訊息唯一識別碼（主鍵）         |
| user       | ForeignKey     | 是       | -     | 關聯到 User 模型的外鍵      |
| role       | string         | 是       | -     | 訊息角色，選項：'user'、'ai'  |
| content    | text           | 是       | -     | 訊息內容文字               |
| metadata   | JSONField      | 否       | {}    | 額外的中繼資料（如來源裝置等）   |
| created_at | datetime       | 否       | -     | 訊息建立時間（自動生成）       |

#### 語言分析相關 Analysis

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| id             | integer        | 是       | -     | 分析唯一識別碼（主鍵）         |
| message        | OneToOneField  | 是       | -     | 關聯到 Message 模型的一對一外鍵 |
| grammar_errors | JSONField      | 否       | []    | 文法錯誤分析結果陣列           |
| vocab_difficulty | JSONField    | 否       | []    | 詞彙難度分析結果陣列           |
| misc           | JSONField      | 否       | {}    | 其他分析資料（信心分數等）      |
| created_at     | datetime       | 否       | -     | 分析建立時間（自動生成）       |

#### JSON 欄位結構說明

**grammar_errors** 陣列元素結構：
```json
{
  "start": 4,                    // 錯誤開始位置
  "end": 6,                      // 錯誤結束位置
  "word": "go",                  // 錯誤單詞
  "suggestion": "went",          // 建議修正
  "rule": "past tense",          // 語法規則
  "explanation": "..."           // 錯誤說明
}
```

**vocab_difficulty** 陣列元素結構：
```json
{
  "word": "yesterday",           // 單詞
  "level": "A2",                 // CEFR 難度等級
  "synonyms": ["the day before"], // 同義詞
  "example": "..."               // 使用範例
}
```

#### 背景任務處理相關 (可選)

如果使用 Celery + Redis 進行背景處理，可能需要以下額外欄位：

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| status     | string         | 否       | "completed" | 訊息處理狀態：'generating'、'completed'、'failed' |
| task_id    | string         | 否       | null    | Celery 任務 ID（用於追蹤背景處理） |

#### LLM 推理請求/回應格式

**推理請求格式 (InferRequest)**：
```json
{
  "message_id": 123,
  "user_id": 456,
  "text": "I go to school yesterday",
  "user_level": "A2"
}
```

**推理回應格式 (InferResponse)**：
```json
{
  "reply": "That's great! I went to school yesterday too. What did you learn?",
  "grammar_errors": [
    {
      "start": 2,
      "end": 4,
      "word": "go",
      "suggestion": "went",
      "rule": "past tense",
      "explanation": "Use 'went' for past actions, not 'go'"
    }
  ],
  "vocab_difficulty": [
    {
      "word": "yesterday",
      "level": "A2",
      "synonyms": ["the day before"],
      "example": "I played football yesterday afternoon."
    }
  ],
  "misc": {
    "confidence": 0.95,
    "processing_time": 1.2
  }
}
```

## 備註

1. **身份驗證**: 使用 Simple JWT，登入後驗證請求標頭中包含 `Authorization: Bearer <your-token>`。
2. **時間格式**: 所有時間欄位均使用 ISO 8601 格式 (例: `2025-08-08T10:30:00Z`)以利資料一致性與排序，但前端可以根據需要轉換為其他格式（如 yyyy/mm/dd）。
3. **字元編碼**: 所有文字內容使用 UTF-8 編碼，不然前端 flutter 收到 Response 的 message 有中文會變成亂碼。
4. **內容類型**: 所有請求和回應均使用 `application/json` 格式，除語音 `multipart/form-data`。
5. **電子郵件驗證**: 系統會寄送一次性驗證碼至用戶電子郵件，使用者需在註冊或重設密碼時提供此驗證碼。
6. **Token 生命週期**: Access Token 會在 1 小時後過期，Refresh Token 會在 7 天後過期。登出時前端丟棄 Token 就好。
7. **請求速率限制**: 為防止濫用，系統對每個用戶的請求頻率進行限制(未來擴充，可以不做)。
8. **Response 格式**: 所有 API 的回應均使用統一的格式，包含 `status`、`message` 和 `data` 三個欄位。
9. **LLM 推理**: 系統支援同步和非同步兩種模式，非同步模式使用 WebSocket 或輪詢機制更新訊息狀態。
10. **背景處理**: 可使用 Celery + Redis 進行 LLM 推理的背景處理，提升使用者體驗。
11. **錯誤處理**: LLM 服務不可用時，系統會返回預設回覆並在 `misc.error` 欄位記錄錯誤資訊。

## Request/Response 範例

### 1. 發送聊天訊息 API

**Request:**
```http
POST /api/chat/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "I go to school yesterday"
}
```

**Response (同步模式):**
```json
{
  "status": "success",
  "message": "Message processed successfully",
  "data": {
    "id": 456,
    "user": 123,
    "role": "ai",
    "content": "That's great! I went to school yesterday too. What did you learn?",
    "metadata": {},
    "created_at": "2025-10-05T10:30:00Z",
    "analysis": {
      "grammar_errors": [
        {
          "start": 2,
          "end": 4,
          "word": "go",
          "suggestion": "went",
          "rule": "past tense",
          "explanation": "Use 'went' for past actions, not 'go'"
        }
      ],
      "vocab_difficulty": [
        {
          "word": "yesterday",
          "level": "A2",
          "synonyms": ["the day before"],
          "example": "I played football yesterday afternoon."
        }
      ],
      "misc": {
        "confidence": 0.95,
        "processing_time": 1.2
      },
      "created_at": "2025-10-05T10:30:00Z"
    }
  }
}
```

**Response (非同步模式 - 立即返回):**
```json
{
  "status": "success",
  "message": "Message queued for processing",
  "data": {
    "id": 456,
    "user": 123,
    "role": "ai",
    "content": "",
    "metadata": {
      "status": "generating",
      "task_id": "celery-task-uuid-123"
    },
    "created_at": "2025-10-05T10:30:00Z",
    "analysis": null
  }
}
```

### 2. 取得聊天歷史 API

**Request:**
```http
GET /api/history/?limit=20&offset=0
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "History retrieved successfully",
  "data": [
    {
      "id": 455,
      "user": 123,
      "role": "user",
      "content": "I go to school yesterday",
      "metadata": {},
      "created_at": "2025-10-05T10:29:00Z",
      "analysis": null
    },
    {
      "id": 456,
      "user": 123,
      "role": "ai",
      "content": "That's great! I went to school yesterday too. What did you learn?",
      "metadata": {},
      "created_at": "2025-10-05T10:30:00Z",
      "analysis": {
        "grammar_errors": [...],
        "vocab_difficulty": [...],
        "misc": {...},
        "created_at": "2025-10-05T10:30:00Z"
      }
    }
  ]
}
```

### 3. LLM 推理服務 API (內部服務)

**Request:**
```http
POST /llm/infer/
Content-Type: application/json

{
  "message_id": 455,
  "user_id": 123,
  "text": "I go to school yesterday",
  "user_level": "A2"
}
```

**Response:**
```json
{
  "reply": "That's great! I went to school yesterday too. What did you learn?",
  "grammar_errors": [
    {
      "start": 2,
      "end": 4,
      "word": "go",
      "suggestion": "went",
      "rule": "past tense",
      "explanation": "Use 'went' for past actions, not 'go'"
    }
  ],
  "vocab_difficulty": [
    {
      "word": "yesterday",
      "level": "A2",
      "synonyms": ["the day before"],
      "example": "I played football yesterday afternoon."
    }
  ],
  "misc": {
    "confidence": 0.95,
    "processing_time": 1.2
  }
}
```

