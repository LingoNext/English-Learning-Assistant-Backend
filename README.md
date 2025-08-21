## RESTful API 標準規格

### 表格1：API 端點規格表

| 資源路徑 | 操作名稱 | HTTP方法 | 請求參數 | 回應 | 常見狀態碼 | 備註 |
|---------|---------|----------|---------|------|--------|------|
| `/auth/login/` | 用戶登入 | POST | email, password | LoginResponse | 200, 400, 401 | Email + Password 驗證 |
| `/auth/verification/send/` | 發送驗證碼 | POST | email | - | 200, 400 | 六位數驗證碼發送至郵件，需防刷 |
| `/auth/registration/confirm/` | 註冊確認 | POST | email, password, name, verification_code | RegistrationResponse | 201, 400, 409 | 註冊密碼最少 8 字元，含大小寫與數字 |
| `/auth/password/reset/confirm/` | 密碼重設 | POST | email, verification_code, new_password | PasswordResetComplete | 200, 400, 401 | 需先呼叫 `/auth/verification/send/` 取得驗證碼 |
| `/auth/user/` | 取得用戶資料 | GET | - | UserProfile | 200, 401 | - |
| `/auth/user/` | 更新用戶資料 | PUT/PATCH | name | UserProfile | 200, 400, 401 | - |
| `/stories` | 創建故事，返回 ai 回應 | POST | content, creationMode, emotionData, audioFile(僅限voice) | LearningRecord | 201, 400, 401 | 若 creationMode=voice，audioFile 必填，否則回傳 400。API 必須使用 multipart/form-data |
| `/stories` | 取得故事清單 | GET | - | StoryContent | 200, 401 | - |
| `/ai/conversation/{storyId}/messages` | AI 對話（訊息） | POST | message, context | ConversationResponse | 200, 400, 401, 404 | - |
| `/ai/conversation/{storyId}/next-question` | AI 提供下一題引導 | POST | - | NextQuestionResponse | 200, 404, 401 | - |
| `/ai/conversation/{storyId}/change-question` | 使用者更換問題 | POST | - | ChangeQuestionResponse | 200, 400, 404, 401 | - |

### 表格2：資料欄位規格表

#### 用戶相關

- UserProfile

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| id | uuid | UUID (API: string, DB: uuid) | 用戶唯一識別碼 |
| email | varchar(254) | email format (API: string, DB: varchar(254)) | 用戶電子郵件地址 |
| name | varchar(20) | 1-20 characters (API: string, DB: varchar(20)) | 用戶顯示名稱 |
| createdAt | timestamptz / string | ISO 8601 datetime (API: string, DB: timestamptz) | 帳號建立時間 |

#### 身份驗證相關

- LoginResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| key | varchar(128) | Token format (API: string) | 身份驗證 Token，建議 DB 欄位 varchar(128) |
| user | object / UserProfile | UserProfile | 用戶基本資料 |

- RegistrationResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| message | text | text (API: string) | 註冊結果訊息 |

- VerificationResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| message | text | text (API: string) | 驗證結果訊息 |

- PasswordResetResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| message | text | text (API: string) | 密碼重設郵件發送結果 |

- PasswordChangeResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| message | text | text (API: string) | 密碼更改結果訊息 |

#### 故事相關

- StoryContent

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| id | uuid | UUID (API: string, DB: uuid) | 故事唯一識別碼 |
| content | varchar(500) / text | 1-500 characters (API: string, DB: varchar(500) or text) | 故事內容 |
| creationMode | enum('text','voice','image') / varchar(10) | enum: "text", "voice", "image" | 創作模式（建議 DB 使用 enum 或 varchar(10)） |
| emotionScore | smallint | 1-5 (API: integer, DB: smallint/tinyint) | 情緒分數 |
| audioFile | varchar(255) / string | 音訊檔案路徑 (API: string, DB: varchar(255)) | 語音故事的音訊檔案路徑（若 creationMode 為 voice） |
| createdAt | timestamptz / string | ISO 8601 datetime (API: string, DB: timestamptz) | 創作時間 |

- LearningRecord

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| id | uuid | UUID (API: string, DB: uuid) | 學習記錄唯一識別碼 |
| storyId | uuid | UUID (API: string, DB: uuid) | 關聯故事ID |
| grammarScore | smallint | 1-5 (API: integer, DB: smallint) | 文法分數 |
| vocabularyScore | smallint | 1-5 (API: integer, DB: smallint) | 詞彙分數 |
| pronunciationScore | smallint | 0-5 (API: integer, DB: smallint) | 發音分數(僅限於語音故事，無則為 0) |
| emotionAnalysis | jsonb / json | EmotionData (API: object, DB: jsonb) | 情緒 |
| feedback | text | text (API: string, DB: text) | AI 回饋內容 |
| suggestions | text[] / jsonb | Array<string> (API: array) | 改善建議（DB: text[] 或 jsonb） |
| createdAt | timestamptz / string | ISO 8601 datetime (API: string, DB: timestamptz) | 記錄建立時間 |

#### AI 對話相關

- ConversationResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| id | uuid | UUID (API: string, DB: uuid) | 對話唯一識別碼 |
| response | text | text (API: string, DB: text) | AI 回應內容 |
| conversationId | uuid | UUID (API: string, DB: uuid) | 對話會話 ID |
| suggestions | text[] / jsonb | Array<string> (API: array) | 建議回應選項（DB: text[] 或 jsonb） |
| timestamp | timestamptz / string | ISO 8601 datetime (API: string, DB: timestamptz) | 回應時間 |

- NextQuestionResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| id | uuid | UUID (API: string, DB: uuid) | 問題唯一識別碼 |
| newQuestion | text | text (API: string, DB: text) | AI 提供的下一個引導問題 |
| timestamp | timestamptz / string | ISO 8601 datetime (API: string, DB: timestamptz) | 回應時間 |

- ChangeQuestionResponse

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| id | uuid | UUID (API: string, DB: uuid) | 問題唯一識別碼 |
| replacedQuestion | text | text (API: string, DB: text) | 被更換的原本問題 |
| newQuestion | text | text (API: string, DB: text) | AI 提供的新問題 |
| timestamp | timestamptz / string | ISO 8601 datetime (API: string, DB: timestamptz) | 回應時間 |

### 通用資料結構

| 欄位名稱 | 型別 | 格式 | 說明 |
|---------|------|------|-----|
| status | integer | HTTP 狀態碼 (e.g., 200) | 可表示請求結果 |
| message | varchar(1024) / text | 字串 (API: string) | 可提供額外資訊 |
| content_type | varchar(64) | 固定 'application/json; charset=utf-8' | 可支援繁體中文 |

---

### HTTP 狀態碼說明

| 狀態碼 | 說明 | 使用場景 |
|--------|------|---------|
| 200 | OK | 請求成功 |
| 201 | Created | 資源創建成功 |
| 400 | Bad Request | 請求格式錯誤或參數無效 |
| 401 | Unauthorized | 未授權 |
| 403 | Forbidden | 禁止存取 |
| 404 | Not Found | 資源不存在 |
| 409 | Conflict | 資源衝突（如電子郵件已存在） |
| 500 | Internal Server Error | 伺服器內部錯誤 |

### 常見錯誤類型

| 錯誤代碼 | 說明 | HTTP狀態碼 |
|---------|------|-----------|
| ValidationError | 使用者送出的資料格式錯誤或缺少必要欄位 | 400 |
| InvalidCredentials | 登入憑證無效，請檢查電子郵件和密碼 | 401 |
| Unauthorized | 未授權存取，Token 無效或已過期 | 401 |
| EmailExists | 電子郵件已存在 | 409 |
| InvalidCode | 驗證碼無效 | 400 |
| CodeExpired | 驗證碼過期 | 400 |
| TaskNotFound | 任務不存在 | 404 |
| StoryNotFound | 故事不存在 | 404 |

## 備註

1. **身份驗證**: 使用 Django Token Authentication，登入後的操作請求標頭中應包含 `Authorization: Token <your-token>`。
2. **時間格式**: 所有時間欄位均使用 ISO 8601 格式 (例: `2025-08-08T10:30:00Z`)以利資料一致性與排序，但前端可以根據需要轉換為其他格式（如 yyyy/mm/dd）。
3. **字元編碼**: 所有文字內容使用 UTF-8 編碼，不然中文變成亂碼。
4. **版本控制**: API 版本透過 URL 路徑指定 (`/api/v1/`)。
5. **內容類型**: 所有請求和回應均使用 `application/json` 格式。
6. **電子郵件驗證**: 系統會寄送一次性驗證碼至用戶電子郵件，使用者需在註冊或重設密碼時提供此驗證碼。
7. **Token 生命週期**: Token 不會過期，除非手動登出。登出時前端丟棄 Token 就好。

## API 詳細定義與 Request/Response 範例

### 使用上的共通 Header
- Content-Type: application/json (除了語音使用的是 multipart/form-data)
- Authorization: Token <your-token> (需要認證的 API)

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
	"key": "0123456789abcdef0123456789abcdef01234567",
	"user": {
		"id": "a1b2c3d4-e5f6-7890-ab12-cd34ef56gh78",
		"email": "user@example.com",
		"name": "使用者",
		"createdAt": "2025-08-21T10:30:00Z"
	}
}
```

### 2) /auth/verification/send/ — POST
- 描述：發送驗證碼（註冊/重設密碼）
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
	"verification_code": "123456"
}
```
- 成功 Response (201):
```json
{
	"message": "註冊完成",
	"user": {
		"id": "uuid",
		"email": "user@example.com",
		"name": "使用者",
		"createdAt": "2025-08-21T10:30:00Z"
	}
}
```

### 4) /auth/password/reset/confirm/ — POST
- 描述：使用驗證碼重設密碼
- Request 範例:
```json
{
	"email": "user@example.com",
	"verification_code": "123456",
	"new_password": "NewStr0ngP@ss",
}
```
- 成功 Response (200):
```json
{
	"message": "密碼重設成功"
}
```

### 5) /auth/user/ — GET
- 描述：取得當前用戶資料
- Headers: Authorization: Token <your-token>
- 成功 Response (200):
```json
{
	"id": "uuid",
	"email": "user@example.com",
	"name": "使用者",
	"createdAt": "2025-08-21T10:30:00Z"
}
```

### 6) /auth/user/ — PUT / PATCH
- 描述：更新使用者資訊

- PATCH Request 範例:
```json
{
	"name": "新名字"
}
```
- 成功 Response (200):
```json
{
	"id": "uuid",
	"email": "user@example.com",
	"name": "新名字",
	"createdAt": "2025-08-21T10:30:00Z"
}
```

### 7) /stories — POST（創建故事）
- 描述：提交新的故事（文字/語音/圖片）
- Content-Type: `multipart/form-data`
- 當 `creationMode` 為 `voice` 時，`audioFile` 為必填欄位，否則回傳 400。
- 其他模式（如 text, image）不需傳 audioFile。

成功 Response (201):
```json
{
	"id": "story-uuid-1",
	"content": "today i learned something new coding,and it was really exciting!",
	"creationMode": "voice",
	"emotionData": 5,
	"analysis": {
		"scores": {
			"grammar": 2,
			"vocabulary": 4,
			"pronunciation": 3
		},
		"keywords": ["coding", "exciting"],
		"suggestions": ["建議多練習基本句型結構，主詞與動詞搭配不夠清楚"],
	},
	"audioFile": "story_voice.wav",
	"createdAt": "2025-08-21T11:00:00Z"
}
```

### 8) /stories — GET（取得故事清單）
- Headers: Authorization: Token <your-token>
- 成功 Response (200):
```json
[
    {
	    "id": "story-uuid-1",
	    "content": "today i learned something new coding,and it was really exciting!",
	    "creationMode": "voice",
	    "emotionData": 5,
        "analysis": {
            "scores": {
                "grammar": 2,
                "vocabulary": 4,
                "pronunciation": 3
            },
            "keywords": ["coding", "exciting"],
            "suggestions": ["建議多練習基本句型結構，主詞與動詞搭配不夠清楚"],
        },
		"audioFile": "story_voice.wav",
	    "createdAt": "2025-08-21T11:00:00Z"
    },
    {
        "id": "story-uuid-2",
        "content": "I spent two days observing the results of the experiment.",
        "creationMode": "text",
        "emotionData": 4,
        "analysis": {
            "scores": {
                "grammar": 5,
                "vocabulary": 5,
                "pronunciation": 0
            },
            "keywords": ["observe", "experiment"],
            "suggestions": ["可以多用一些形容詞"],
        },
        "createdAt": "2025-08-21T11:05:00Z"
    }
]
```

### 9) /ai/conversation/{storyId}/first-question — POST
- 描述：使用者發送訊息，AI 回應並儲存對話
- Request 範例:
```json
{
	"content": "today i learned something new coding,and it was really exciting!"
}
```
- 成功 Response (200):
```json
{
	"response": "It sounds like that time was really tough. First, you could try to...",
	"conversationId": "conversation-uuid-3",
	"timestamp": "2025-08-21T11:05:00Z"
}
```

### 10) /ai/conversation/{storyId}/next-question — POST
- 描述：AI 根據上下文提供下一題引導
- Request 範例:
```json
{ "conversationId": "conversation-uuid-3"}
```
- 成功 Response (200):
```json
{ 	"newQuestion": "what do you think about that?",
	"nextConversationId": "conversation-uuid-4",
	"timestamp": "2025-08-21T11:05:30Z" }
```

### 11) /ai/conversation/{storyId}/change-question — POST
- 描述：使用者請求更換目前引導問題
- Request 範例:
```json
{
	"conversationId": "conversation-uuid-4",
	"currentQuestion": "what do you think about that?",
}
```
- 成功 Response (200):
```json
{
	"newQuestion": "if you could change one thing about that experience, what would it be?",
	"nextConversationId": "conversation-uuid-5",
	"timestamp": "2025-08-21T11:06:00Z"
}
```

