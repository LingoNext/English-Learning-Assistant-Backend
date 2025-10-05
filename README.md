## RESTful API 標準規格

### 表格1：API 端點規格表

| 資源路徑 | 操作名稱 | HTTP方法 | 請求參數 | 回應 data | 狀態碼 | 備註 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `/auth/login/` | 用戶登入 | POST | email, password | refresh_token、access_token | 200, 400, 401 | - |
| `token/refresh/` | 重新整理 Token | POST | refresh_token | new_token | 200, 400, 401 | - |
| `token/verify/` | 驗證 Token | POST | access_token | - | 200, 400, 401 | -  |
| `/auth/verification/send/` | 發送驗證碼 | POST | email | - | 200, 400 | verification_code 傳送至用戶電子郵件 |
| `/auth/registration/confirm/` | 註冊確認 | POST | email, password, verification_code, name | - | 201, 400, 409 | - |
| `/auth/password/reset/confirm/` | 密碼重設 | POST | email, password, verification_code | - | 200, 400, 401 | - |
| `/auth/delete_account/` | 永久刪除帳號 | POST | password | - | 204, 400, 401 | 需攜帶 access_token |
| `/auth/user/` | 取得用戶資料 | GET | - | email, name | 200, 401 | 需攜帶 access_token |
| `/auth/user/` | 更新用戶資料 | PUT | new_name | - | 200, 400, 401 | 需攜帶 access_token |
| `/api/conversations/` | 取得對話列表 | GET | - | conversations_array | 200, 401 | 需攜帶 access_token |
| `/api/conversations/` | 建立新對話 | POST | - | conversation_object | 201, 400, 401 | 需攜帶 access_token |
| `/api/conversations/{id}/` | 取得特定對話 | GET | - | conversation_object | 200, 401, 404 | 需攜帶 access_token |
| `/api/conversations/{id}/` | 更新對話資料 | PUT | - | - | 200, 400, 401, 404 | 需攜帶 access_token |
| `/api/conversations/{id}/` | 刪除對話 | DELETE | - | - | 204, 401, 404 | 需攜帶 access_token，同時刪除所有相關訊息 |
| `/api/conversations/{id}/messages/` | 取得對話訊息 | GET | limit, offset | messages_array | 200, 401, 404 | 需攜帶 access_token |
| `/api/conversations/{id}/chat/` | 發送聊天訊息 | POST | message | message_object (含分析) | 200, 400, 401, 404, 500 | 需攜帶 access_token，返回 AI 回覆及語言分析 |
| `/llm/infer/` | LLM 推理服務 | POST | message_id, user_id, text | reply, grammar_errors, vocab_difficulty, misc | 200, 400, 500 | 內部服務 API，由 Django 後端呼叫 |

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
| is_active  | boolean        | 否       | True  | 用戶帳號是否啟用             |
| is_staff   | boolean        | 否       | False | 用戶是否為管理員             |
| is_superuser | boolean      | 否       | False | 用戶是否為超級管理員          |
| date_joined | datetime      | 否       | -     | 帳號註冊時間（繼承自 AbstractUser） |
| last_login | datetime       | 否       | -     | 最後登入時間（繼承自 AbstractUser） |
| created_at | datetime       | 否       | -     | 帳號建立時間（自動生成）       |

#### 對話管理相關 Conversation

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| id         | integer        | 是       | -     | 對話唯一識別碼（主鍵）         |
| user       | ForeignKey     | 是       | -     | 關聯到 User 模型的外鍵      |
| created_at | datetime       | 否       | -     | 對話建立時間（自動生成）       |
| updated_at | datetime       | 否       | -     | 對話最後更新時間（自動更新）   |
| is_active  | boolean        | 否       | True  | 對話是否啟用（軟刪除）       |

#### 聊天訊息相關 Message

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| id           | integer        | 是       | -     | 訊息唯一識別碼（主鍵）         |
| conversation | ForeignKey     | 是       | -     | 關聯到 Conversation 模型的外鍵 |
| user         | ForeignKey     | 是       | -     | 關聯到 User 模型的外鍵      |
| role         | string         | 是       | -     | 訊息角色，選項：'user'、'ai'  |
| content      | text           | 是       | -     | 訊息內容文字               |
| metadata     | JSONField      | 否       | {}    | 額外的中繼資料（如來源裝置等）   |
| created_at   | datetime       | 否       | -     | 訊息建立時間（自動生成）       |

#### 語言分析相關 Analysis

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|:-:|:-:|:-:|:-:|:-:|
| id             | integer        | 是       | -     | 分析唯一識別碼（主鍵）         |
| message        | OneToOneField  | 是       | -     | 關聯到 Message 模型的一對一外鍵 |
| grammar_errors | JSONField      | 否       | []    | 文法錯誤分析結果陣列           |
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
  "text": "I go to school yesterday"
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

### 1. 在對話中發送訊息 API

**Request:**
```http
POST /api/conversations/3/chat/
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
    "conversation": 3,
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
- 後端先回應前端，但實際工作繼續在背景執行
```json
{
  "status": "success",
  "message": "Message queued for processing",
  "data": {
    "id": 456,
    "conversation": 3,
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

### 2. 取得對話訊息歷史 API

**Request:**
```http
GET /api/conversations/3/messages/?limit=20&offset=0
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation messages retrieved successfully",
  "data": [
    {
      "id": 455,
      "conversation": 3,
      "user": 123,
      "role": "user",
      "content": "I go to school yesterday",
      "metadata": {},
      "created_at": "2025-10-05T10:29:00Z",
      "analysis": null
    },
    {
      "id": 456,
      "conversation": 3,
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

### 4. 對話管理 API

#### 4.1 取得對話列表

**Request:**
```http
GET /api/conversations/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversations retrieved successfully",
  "data": [
    {
      "id": 1,
      "user": 123,
      "created_at": "2025-10-05T09:00:00Z",
      "updated_at": "2025-10-05T10:30:00Z",
      "is_active": true,
      "message_count": 8,
      "last_message_preview": "That's great! I went to school yesterday too..."
    },
    {
      "id": 2,
      "user": 123,
      "created_at": "2025-10-04T14:20:00Z",
      "updated_at": "2025-10-04T15:45:00Z",
      "is_active": true,
      "message_count": 12,
      "last_message_preview": "What places would you recommend..."
    }
  ]
}
```

#### 4.2 建立新對話

**Request:**
```http
POST /api/conversations/
Authorization: Bearer <access_token>
Content-Type: application/json

{}
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation created successfully",
  "data": {
    "id": 3,
    "user": 123,
    "created_at": "2025-10-05T11:00:00Z",
    "updated_at": "2025-10-05T11:00:00Z",
    "is_active": true
  }
}
```

#### 4.3 在特定對話中發送訊息

**Request:**
```http
POST /api/conversations/3/chat/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "Hello, I want to practice English today"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Message sent successfully",
  "data": {
    "id": 789,
    "conversation": 3,
    "user": 123,
    "role": "ai",
    "content": "Hello! That's wonderful. What topic would you like to practice today?",
    "metadata": {},
    "created_at": "2025-10-05T11:05:00Z",
    "analysis": {
      "grammar_errors": [],
      "vocab_difficulty": [
        {
          "word": "practice",
          "level": "A2",
          "synonyms": ["exercise", "rehearse"],
          "example": "I need to practice speaking English every day."
        }
      ],
      "misc": {
        "confidence": 0.98,
        "processing_time": 0.8
      },
      "created_at": "2025-10-05T11:05:00Z"
    }
  }
}
```



