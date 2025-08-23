## RESTful API 標準規格
> /auth/ 可行。/stories 和 /ai/conversation 暫定，待確認可行性

### 表格1：API 端點規格表

| 資源路徑 | 操作名稱 | HTTP方法 | 請求參數 | 回應 data | 狀態碼 | 備註 |
|---------|---------|----------|---------|------|--------|------|
| `/auth/login/` | 用戶登入 | POST | email, password | token | 200, 400, 401 | - |
| `/auth/verification/send/` | 發送驗證碼 | POST | email | - | 200, 400 | - |
| `/auth/registration/confirm/` | 註冊確認 | POST | email, password,code, name,  | - | 201, 400, 409 | - |
| `/auth/password/reset/confirm/` | 密碼重設 | POST | email, password, code | - | 200, 400, 401 | - |
| `/auth/delete_account/` | 刪除帳號 | POST | email, password | - | 204, 400, 401 | 需攜帶 token |
| `/auth/user/` | 取得用戶資料 | GET | - | email, name | 200, 401 | 需攜帶 token |
| `/auth/user/` | 更新用戶資料 | PUT | name | - | 200, 400, 401 | 需攜帶 token |
| `/stories` | 創建故事，返回 ai 回應 | POST | context,emotionScore | grammarScore, vocabularyScore, pronunciationScore, keywords, feedback,suggestions | 201, 400, 401 | 需攜帶 token |
| `/stories` | 取得故事清單 | GET | - | StoryContent | 200, 401 | 需攜帶 token |
| `/ai/conversation/messages/first_question` | ai 第一個問題 | POST | storyId | question, ConversationId | 200, 400, 401, 404 | 需攜帶 token |
| `/ai/conversation/next_question` | 回答並提供下一題 | POST | ConversationId, context | suggestions, question, ConversationId | 200, 404, 401 | 需攜帶 token |
| `/ai/conversation/change_question` | 更換問題 | POST | ConversationId | question | 200, 400, 404, 401 | 需攜帶 token |

### 表格2：資料欄位規格表


#### 用戶身份驗證相關

- Verification (自建)

| 欄位名稱 | 資料型別      | 是否必填 | 預設值 | 說明               |
|----------|--------------|----------|--------|--------------------|
| id       | uuid         | 是       | 無     | 驗證碼唯一識別碼   |
| email    | varchar(254) | 是       | 無     | 用戶電子郵件地址   |
|      | varchar(6)   | 是       | 無     | 六位數驗證碼       |
| createdAt| timestamptz  | 是       | now()  | 驗證碼創建時間     |

- auth_user（Django 內建）

| 欄位名稱   | 資料型別      | 是否必填 | 預設值 | 說明               |
|------------|--------------|----------|--------|--------------------|
| id         | int/uuid     | 是       | 無     | 使用者唯一識別碼   |
| username   | varchar(150) | 是       | 無     | 帳號               |
| password   | varchar(128) | 是       | 無     | 密碼雜湊值         |
| email      | varchar(254) | 是       | 無     | 電子郵件           |
| name       | varchar(150) | 否       | 無     | 姓名               |
| date_joined| datetime     | 是       | now()  | 建立時間           |

- authtoken_token（安裝 rest_framework.authtoken）

| 欄位名稱 | 資料型別    | 是否必填 | 預設值 | 說明           |
|----------|------------|----------|--------|----------------|
| key      | varchar(40)| 是       | 無     | Token 值       |
| user_id  | int/uuid   | 是       | 無     | 關聯使用者主鍵 |
| created  | datetime   | 是       | now()  | 建立時間 |



#### 故事/學習記錄

- StoryContent (自建)

| 欄位名稱           | 資料型別         | 是否必填 | 預設值   | 說明                         |
|--------------------|------------------|----------|----------|------------------------------|
| id                 | uuid             | 是       | 無       | 唯一識別碼                   |
| content            | varchar(500)/text| 否       | 無       | 故事內容                     |
| creationMode       | enum/varchar(10) | 否       | "text"   | 創作模式（text/voice/image） |
| emotionScore       | smallint         | 否       | 1        | 情緒分數                     |
| audioFile          | varchar(255)     | 否       | 無       | 語音故事的音訊檔案路徑       |
| grammarScore       | smallint         | 否       | 0        | 文法分數                     |
| vocabularyScore    | smallint         | 否       | 0        | 詞彙分數                     |
| pronunciationScore | smallint         | 否       | 0        | 發音分數                     |
| feedback           | text             | 否       | 無       | AI 回饋內容                  |
| suggestions        | text[]/jsonb     | 否       | 無       | 改善建議                     |
| createdAt          | timestamptz      | 是       | now()    | 建立時間                     |



#### AI 對話相關

- Conversation

| 欄位名稱        | 資料型別      | 是否必填 | 預設值 | 說明          |
|----------------|--------------|----------|--------|--------------|
| id             | uuid         | 是       | 無     | 唯一識別碼    |
| StoryContentId | uuid         | 是       | 無     | 故事內容 ID   |
| question       | text         | 是       | 無     | AI 問題內容   |
| content        | text         | 否       | 無     | 使用者回答內容 |
| suggestions    | text[]/jsonb | 否       | 無     | AI 建議回應   |
| previousId     | uuid         | 否       | 無     | 前一個對話 ID |
| createdAt      | timestamptz  | 是       | now()  | 回應時間      |

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

### 8) /stories — POST
- 描述：提交新的故事（文字/語音/圖片）
- Content-Type: `multipart/form-data`
- 當 `creationMode` 為 `voice` 時，`audioFile` 為必填欄位，否則回傳 400。
- 其他模式（如 text, image）不需傳 audioFile。
- feedback: LLM 用 context 生成針對使用者故事的用語、文法、發音等方面的回饋
- suggestions: LLM 用 context 生成分別為專業（formal / professional）和生活化（casual / friendly）的句子，並根據上下文提供下一題引導
- Headers: Authorization: Token <your-token>
- Request 範例:
```json
{
	"storyId": "<story-id-1>",
	"content": "today i learned something new coding,and it was really exciting!",
	"creationMode": "voice",
	"emotionData": 5,
	"audioFile": "story_voice.wav"
}
```
成功 Response (201):
```json
{
	"scores": {
		"grammar": 2,
		"vocabulary": 4,
		"pronunciation": 3
	},
	"keywords": ["coding", "exciting"],
	"feedback": ["建議多練習基本句型結構，主詞與動詞搭配不夠清楚"],
	"suggestions": ["Today, I acquired new coding knowledge, and it was a truly rewarding experience.",
	"I picked up something new in coding today, and it was super exciting!"]
}
```

### 9) /stories — GET
- Headers: Authorization: Token <your-token>
- 成功 Response (200):
```json
[
    {
	    "content": "today i learned something new coding,and it was really exciting!",
	    "creationMode": "voice",
	    "emotionData": 5,
        "scores": {
                "grammar": 2,
                "vocabulary": 4,
                "pronunciation": 3
            },
        "keywords": ["coding", "exciting"],
        "feedback": ["建議多練習基本句型結構，主詞與動詞搭配不夠清楚"],
		"suggestions": ["Today, I acquired new coding knowledge, and it was a truly rewarding experience.",
		"I picked up something new in coding today, and it was super exciting!"],
	    "createdAt": "2025-08-21T11:00:00Z"
    },
    {
        "content": "I spent two days observing the results of the experiment.",
        "creationMode": "text",
        "emotionData": 4,
        "scores": {
            "grammar": 5,
            "vocabulary": 5,
            "pronunciation": 0
        },
        "keywords": ["observe", "experiment"],
        "feedback": ["結構正確，但可以多補充觀察的細節或方法，使敘述更完整。"],
		"suggestions": ["I dedicated two days to carefully observing the outcomes of the experiment.",
		"I spent two days just watching how the experiment turned out."],
        "createdAt": "2025-08-21T11:05:00Z"
    }
]
```

### 10) /ai/conversation/first_question — POST
- 描述：使用者發送訊息，LLM 根據故事生成第一個問題
- Headers: Authorization: Token <your-token>
- Request 範例:
```json
{
	"StoryId": "<story-id-1>"
}
```
- 成功 Response (200):
```json
{
	"question": "what do you think about that?",
	"ConversationId": "<conversation-id-1>"
}
```

### 11) /ai/conversation/next_question — POST
- 描述：使用者回答上個問題，LLM 用 context 生成分別為專業（formal / professional）和生活化（casual / friendly）的句子，並產生下一題的問題
- Headers: Authorization: Token <your-token>
- Request 範例:
```json
{ 
	"context": "I feel proud of myself. It makes me want to learn even more coding tomorrow.",
	"ConversationId": "<conversation-id-1>"
}
```
- 成功 Response (200):
```json
{ 	"question": "Awesome! Do you plan to use what you learned in a project?",
	"suggestions": ["I feel proud of myself. Building this learning program makes me want to improve my coding skills even more.","I’m proud of myself! Can’t wait to learn more coding tomorrow."],
	"ConversationId": "<conversation-id-2>"
}
```

### 12) /ai/conversation/change_question — POST
- 描述：使用者請求更換目前引導問題，LLM 根據故事與過去的對話內容生成新的問題
- Headers: Authorization: Token <your-token>
- Request 範例:
```json
{
	"ConversationId": "<conversation-id-2>"
}
```
- 成功 Response (200):
```json
{
	"question": "That’s really cool! What exactly did you learn?",
	"ConversationId": "<conversation-id-2>"
}
```

