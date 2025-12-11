## RESTful API 標準規格

### 表格1：API 端點規格表

|              資源路徑               | 操作名稱 | HTTP方法 | 請求參數 |          回應 data           | 狀態碼 |              備註 |
|:-------------------------------:|:-:|:-:|::|:--------------------------:|:-:|:---------------:|
|         `/auth/login/`          | 用戶登入 | POST | email, password | refresh_token、access_token | 200, 400, 401 |               - |
|        `token/refresh/`         | 重新整理 Token | POST | refresh_token |         new_token          | 200, 400, 401 |               - |
|         `token/verify/`         | 驗證 Token | POST | access_token |             -              | 200, 400, 401 |               - |
|   `/auth/verification/send/`    | 發送驗證碼 | POST | email |             -              | 200, 400 |  verification_code 傳送至用戶電子郵件 |
|  `/auth/registration/confirm/`  | 註冊確認 | POST | email, password, verification_code, name |             -              | 201, 400, 409 |               - |
| `/auth/password/reset/confirm/` | 密碼重設 | POST | email, password, verification_code |             -              | 200, 400, 401 |               - |
|     `/auth/delete_account/`     | 永久刪除帳號 | POST | password |             -              | 204, 400, 401 |       需攜帶 access_token |
|          `/auth/user/`          | 取得用戶資料 | GET | - |        email, name         | 200, 401 |       需攜帶 access_token |
|          `/auth/user/`          | 更新用戶資料 | PUT | new_name |             -              | 200, 400, 401 |       需攜帶 access_token |
|      `/api/conversations/`      | 取得對話列表 | GET | - |    conversations_array     | 200, 401 |       需攜帶 access_token |
|      `/api/conversations/`      | 建立新對話 | POST | - |    conversation_object     | 201, 400, 401 |       需攜帶 access_token |
|   `/api/conversations/`    | 取得特定對話 | GET | id |    conversation_object     | 200, 401, 404 |       需攜帶 access_token |
|   `/api/conversations/`    | 刪除對話 | DELETE | id |             -              | 204, 401, 404 |  需攜帶 access_token，同時刪除所有相關訊息 |
| `/api/conversations/msg/`  | 發送聊天訊息 | POST | id |      message_object        | 200, 400, 401, 404, 500 |需攜帶 access_token |

### 表格2：資料欄位規格表
- 一個 User 可以有多個 Conversation
- 一個 Conversation 內可以有多個 Message
- Message 只能屬於一個 Conversation（ForeignKey）
#### 用戶身份驗證相關 User (AbstractUser 擴展)
- 因為 django-rest-framework-simplejwt 已經定義好 token 的欄位，所以這邊不重複定義。
- 使用 Django 內建的 AbstractUser 作為基礎，擴展用戶資料。
- 驗證碼的欄位不存資料庫，是存在快取中 (cache)，所以也不列在這邊。

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 |            說明            |
|:-:|:-:|:-:|:-:|:------------------------:|
| username   | string         | 是       | -     |   名稱（繼承自 AbstractUser）   |
| email      | string (email) | 是       | -     |           電子郵件           |
| password   | string         | 是       | -     |         密碼，需加密存儲         |
| first_name | string         | 否       | ""    |   名字（繼承自 AbstractUser）   |
| last_name  | string         | 否       | ""    |   姓氏（繼承自 AbstractUser）   |
| is_active  | boolean        | 否       | True  |          帳號是否啟用          |
| is_staff   | boolean        | 否       | False |          是否為管理員          |
| is_superuser | boolean      | 否       | False |         是否為超級管理員         |
| date_joined | datetime      | 否       | -     | 帳號註冊時間（繼承自 AbstractUser） |
| last_login | datetime       | 否       | -     | 最後登入時間（繼承自 AbstractUser） |
| created_at | datetime       | 否       | -     |       帳號建立時間（自動生成）       |

#### 對話管理相關 Conversation

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 |       說明       |
|:-:|:-:|:-:|:-:|:--------------:|
| id         | integer        | 是       | -     |       主鍵       |
| user       | ForeignKey     | 是       | -     | 關聯到 User 模型的外鍵 |
| created_at | datetime       | 否       | -     |  對話建立時間（自動生成）  |
| updated_at | datetime       | 否       | -     | 對話最後更新時間（自動更新） |
| is_active  | boolean        | 否       | True  |  對話是否啟用（軟刪除）   |

#### 聊天訊息相關 Message

|         欄位名稱          |    資料型別    | 是否必填 | 預設值 |                    說明                    |
|:---------------------:|:-:|:-:|:-:|:----------------------------------------:|
|          id           |  integer   | 是       |  -  |                    主鍵                    |
|     conversation      | ForeignKey | 是       |  -  |          關聯到 Conversation 模型的外鍵          |
|        content        |    text    | 是       |  -  |                  訊息內容文字                  |
|      ai_response      |    text    | 否       |  -  |              AI 回覆內容文字（若有）               |
|        status         |   string   | 否       |  -  | 訊息處理狀態：'generating'、'completed'、'failed' |
|      created_at       |  datetime  | 否       |  -  |               訊息建立時間（自動生成）               |
#### LLM 推理請求/回應格式

**推理請求格式 (InferRequest)**：
```json
{
  "message_id": 123,
  "user_id": 456,
  "content": "how to improve my english writing?"
}
```

**推理回應格式 (InferResponse)**：
```json
{
  "status": "200",
  "message": "AI response generated successfully",
  "data": {
    "message_id": 123,
    "user_id": 456,
    "ai_response": "Here are some effective ways to improve your English writing:\n\n1. **Read regularly**: Reading books, articles, and well-written content helps you absorb proper grammar, vocabulary, and sentence structures naturally.\n\n2. **Practice daily**: Set aside time each day for writing practice. Start with short paragraphs and gradually work up to longer pieces.\n\n3. **Learn grammar rules**: Understanding basic grammar rules like verb tenses, subject-verb agreement, and punctuation will make your writing clearer.\n\n4. **Expand your vocabulary**: Learn new words and phrases regularly. Use a dictionary and thesaurus to find more precise words.\n\n5. **Get feedback**: Share your writing with native speakers, teachers, or use writing assistance tools to identify areas for improvement.\n\n6. **Write about topics you enjoy**: This keeps you motivated and makes the practice more enjoyable.\n\n7. **Edit and revise**: Always review your work. Check for grammar mistakes, unclear sentences, and improve the flow of your ideas.\n\nRemember, improvement takes time and consistent practice. Don't be discouraged by mistakes – they're part of the learning process!",
    "created_at": "2025-12-11T10:30:00Z"
  }
}
```

**錯誤回應格式 (Error Response)**：
```json
{
  "status": "500",
  "message": "Failed to generate AI response",
  "content_type": "application/json; charset=utf-8"
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


