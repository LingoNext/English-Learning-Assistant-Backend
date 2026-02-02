## RESTful API 標準規格

### 表格1：API 端點規格表

|              資源路徑               |    操作名稱    | HTTP方法 |                請求參數                |                                       回應 data                                       |        狀態碼         |        備註        |
|:-------------------------------:|:----------:|:------:|:----------------------------------:|:-----------------------------------------------------------------------------------:|:------------------:|:----------------:|
|         `/auth/login/`          |    用戶登入    |  POST  |          email, password           |                             access_token、refresh_token                              |   200, 400, 401    |        -         |
|     `/auth/token/refresh/`      | 重新整理 Token |  POST  |           refresh_token            |                                    access_token                                     |   200, 400, 401    |        -         |
|      `/auth/token/verify/`      |  驗證 Token  |  POST  |            access_token            |                                          -                                          |   200, 400, 401    |        -         |
|   `/auth/verification/send/`    |   發送驗證碼    |  POST  |           email, purpose           |                                          -                                          |    200, 400,429    |        -         |
|  `/auth/registration/confirm/`  |    註冊確認    |  POST  | email, password, verification_code |                                          -                                          |   201, 400, 409    |        -         |
| `/auth/password/reset/confirm/` |    密碼重設    |  POST  | email, password, verification_code |                                          -                                          | 200, 400, 401,404  |        -         |
|     `/auth/delete_account/`     |   永久刪除帳號   |  POST  |              password              |                                          -                                          |   204, 400, 401    | 需攜帶 access_token |
|          `/auth/user/`          |   取得用戶資料   |  GET   |                 -                  |                                     email, name                                     |      200, 401      | 需攜帶 access_token |
|          `/auth/user/`          |   更新用戶資料   |  PUT   |              new_name              |                                          -                                          |   200, 400, 401    | 需攜帶 access_token |
|   `/chat/conversations/all/`    |   取得對話列表   |  GET   |                 -                  | Array<{ conversation_id: number, first_user_question: string,updated_at:datetime }> |      200, 401      | 需攜帶 access_token |
|     `/chat/conversations/`      |   取得特定對話   |  GET   |          conversation_id           |                         Array<{text:string,is_user:bool }>                          |      200, 401      | 需攜帶 access_token |
|     `/chat/conversations/`      |   建立新對話    |  POST  |           text, is_user            |                                          -                                          |   201, 400, 401    | 需攜帶 access_token |
|     `/chat/conversations/`      |    刪除對話    | DELETE |          conversation_id           |                                          -                                          |   204, 401, 404    | 需攜帶 access_token |
|        `/chat/messages/`        |   建立新訊息    |  POST  |   conversation_id, text, is_user   |                                          -                                          | 201, 400, 401, 404 | 需攜帶 access_token |
> status 500 為伺服器錯誤，通常不會特別列在表格中，但在實作時仍需處理此類錯誤情況

### 另外實作的 API 端點規格表

> AR 功能相關的 API，待補充

### 表格2：資料欄位規格表

- 一個 User 可以有多個 Conversation
- 一個 Conversation 內可以有多個 Message
- Message 只能屬於一個 Conversation
- POST `/chat/conversations/` 同時建立第一則 Message
- first_user_question 為 Conversation 對應第一個 Message 的前 20 個字元

#### 用戶身份驗證相關 User (AbstractUser 擴展)

- 因為 django-rest-framework-simplejwt 已經定義好 token 的欄位，所以這邊不重複定義。
- 使用 Django 內建的 AbstractUser 作為基礎，擴展用戶資料。
- 驗證碼的欄位不存資料庫，是存在快取中 (cache)，所以也不列在這邊。

|     欄位名稱     |      資料型別      | 是否必填 |  預設值  |            說明            |
|:------------:|:--------------:|:----:|:-----:|:------------------------:|
|    email     | string (email) |  是   |   -   |           電子郵件           |
|   password   |     string     |  是   |   -   |         密碼，需加密存儲         |
|  first_name  |     string     |  是   |  ""   |   名字（繼承自 AbstractUser）   |
|  last_name   |     string     |  否   |  ""   |   姓氏（繼承自 AbstractUser）   |
|  is_active   |    boolean     |  否   | True  |          帳號是否啟用          |
|   is_staff   |    boolean     |  否   | False |          是否為管理員          |
| is_superuser |    boolean     |  否   | False |         是否為超級管理員         |
| date_joined  |    datetime    |  否   |   -   | 帳號註冊時間（繼承自 AbstractUser） |
|  last_login  |    datetime    |  否   |   -   | 最後登入時間（繼承自 AbstractUser） |
|  created_at  |    datetime    |  否   |   -   |       帳號建立時間（自動生成）       |

#### 對話管理相關 Conversation

|        欄位名稱         |    資料型別    | 是否必填 | 預設值 |        說明         |
|:-------------------:|:----------:|:----:|:---:|:-----------------:|
|         id          |  integer   |  是   |  -  |        主鍵         |
|        user         | ForeignKey |  是   |  -  |  關聯到 User 模型的外鍵   |
|     created_at      |  datetime  |  否   |  -  |   對話建立時間（自動生成）    |
|     updated_at      |  datetime  |  否   |  -  |  對話最後更新時間（自動更新）   |
| first_user_question |   string   |  否   |  -  | 用戶第一個問題（序列化時計算得出） |

#### 聊天訊息相關 Message

|     欄位名稱     |    資料型別    | 是否必填 | 預設值 |           說明           |
|:------------:|:----------:|:----:|:---:|:----------------------:|
|      id      |  integer   |  是   |  -  |           主鍵           |
| conversation | ForeignKey |  是   |  -  | 關聯到 Conversation 模型的外鍵 |
|     text     |    text    |  是   |  -  |         訊息內容文字         |
|   is_user    |  boolean   |  是   |  -  |        是否為用戶訊息         |
|  timestamp   |  datetime  |  否   |  -  |      訊息建立時間（自動生成）      |

## 備註

1. **身份驗證**: 使用 Simple JWT，登入後驗證請求標頭中包含 `Authorization: Bearer <token>`
2. **時間格式**: 所有時間欄位均使用 ISO 8601 格式 (例: `2025-08-08T10:30:00Z`)以利資料一致性與排序，但前端可以根據需要轉換為其他格式（如 yyyy/mm/dd）
3. **字元編碼**: 所有文字內容均使用 UTF-8 編碼`charset=utf-8`，不然前端 flutter 收到 Response 的 message 有中文會變成亂碼
4. **內容類型**: 除圖片外，所有請求和回應均使用 `application/json` 格式
5. **電子郵件驗證**: 系統會寄送一次性驗證碼至用戶電子郵件，使用者需在註冊或重設密碼時提供此驗證碼，有效期為五分鐘
6. **Token 生命週期**: Access Token 會在 1 小時後過期，Refresh Token 會在 7 天後過期。登出時前端丟棄兩個 Token 就好
7. **請求速率限制**: 為防止濫用，系統對每個用戶 IP 限制驗證碼`/auth/verification/send/` 10 秒內只能發送 1 次且 1 小時內最多 5 次請求
8. **Response 格式**: 所有 API 的回應均使用統一的格式，包含 `status`(由 HttpResponse 狀態碼決定)、`message` 和 `data`(若需要回傳資料)
9. **錯誤處理**: API 在遇到錯誤時會回傳適當的 HTTP 狀態碼和錯誤訊息，前端應根據狀態碼進行相應處理
10. **跨域資源共享 (CORS)**: API 支援跨域請求，只允許來自特定網域的前端應用程式存取，防止跨站請求偽造 (CSRF) 攻擊
11. **分頁**: 對於可能返回大量資料的端點（如取得對話列表），支援分頁查詢，預設每頁返回 10 筆資料(未來擴充，可以不做)
