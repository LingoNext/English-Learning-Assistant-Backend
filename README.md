## RESTful API 標準規格

### 表格1：API 端點規格表

|              資源路徑               |    操作名稱    | HTTP方法 |                  請求參數                  |                              回應 data                               |        狀態碼        |  備註  |
|:-------------------------------:|:----------:|:------:|:--------------------------------------:|:------------------------------------------------------------------:|:-----------------:|:----:|
|         `/auth/login/`          |    用戶登入    |  POST  |          { email, password }           |                  { access_token, refresh_token }                   |   200,400, 401    |  -   |
|     `/auth/token/refresh/`      | 重新整理 Token |  POST  |           { refresh_token }            |                          { access_token }                          |   200,400, 401    |  -   |
|      `/auth/token/verify/`      |  驗證 Token  |  POST  |            { access_token }            |                                 -                                  |   200,400, 401    |  -   |
|   `/auth/verification/send/`    |   發送驗證碼    |  POST  |           { email, purpose }           |                                 -                                  |    200,400,429    |  -   |
|  `/auth/registration/confirm/`  |    註冊確認    |  POST  | { email, password, verification_code } |                                 -                                  |   201,400, 409    |  -   |
| `/auth/password/reset/confirm/` |    密碼重設    |  POST  | { email, password, verification_code } |                                 -                                  | 200,400, 401,404  |  -   |
|     `/auth/delete_account/`     |   永久刪除帳號   |  POST  |              { password }              |                                 -                                  |   204,400, 401    | 需要驗證 |
|          `/auth/user/`          |   取得用戶資料   |  GET   |                   -                    |                          { email, name }                           |     200, 401      | 需要驗證 |
|          `/auth/user/`          |   更新用戶資料   |  PUT   |              { new_name }              |                                 -                                  |   200,400, 401    | 需要驗證 |
|   `/chat/conversations/all/`    |   取得對話列表   |  GET   |                   -                    | Array<{ conversation_id, first_user_question, count, updated_at }> |     200, 401      | 需要驗證 |
|      `/chat/conversation/`      |   取得特定對話   |  POST  |          { conversation_id }           |                      Array<{ text, is_user }>                      |   200,400, 401    | 需要驗證 |
|     `/chat/conversations/`      |   建立新對話    |  POST  |           { text, is_user }            |                        { conversation_id }                         |   201,400, 401    | 需要驗證 |
|     `/chat/conversations/`      |    刪除對話    | DELETE |          { conversation_id }           |                                 -                                  | 204,400, 401, 404 | 需要驗證 |
|        `/chat/messages/`        |   建立新訊息    |  POST  |   { conversation_id, text, is_user }   |                                 -                                  | 201,400, 401, 404 | 需要驗證 |
|         `/llm/analyze/`         |    分析影像    |  POST  |               { image }                |                   VisualAnalysisSerializer.data                    |   200,400, 502    |      |
|          `/llm/vocab/`          |    詞彙分析    |  POST  |                { word }                |                    VocabResponseSerializer.data                    |   200,400, 502    |      |
|          `/llm/chat/`           |    聊天對話    |  POST  |     { messages,analysis_enabled }      |                    ChatResponseSerializer.data                     |   200,400, 502    |      |

### 表格2：簡化序列化器規格表

|            序列化器名稱             |                              欄位名稱                              |        說明        |
|:-----------------------------:|:--------------------------------------------------------------:|:----------------:|
|  ConversationListSerializer   |    conversation_id, first_user_question, count, updated_at     |      返回對話列表      |
|     MessageListSerializer     |                         text, is_user                          |  用於取得特定對話的訊息列表   |
|      UserLoginSerializer      |                        email, password                         |    用戶登入時的資料驗證    |
| RegistrationConfirmSerializer |               email, password, verification_code               |    註冊確認時的資料驗證    |
|     UserDetailSerializer      |                     email, name, new_name                      |    用戶資料的取得和更新    |
|    DeleteAccountSerializer    |                            password                            |   永久刪除帳號時的密碼驗證   |
|   VocabularyItemSerializer    |                     word_en, word_zh, pos                      |    詞彙分析結果的詞彙     |
|    SentenceItemSerializer     |                        english, chinese                        |    影像分析結果的例句     |
|   VisualAnalysisSerializer    |        VocabularyItemSerializer, SentenceItemSerializer        |    影像分析結果的整合     |
|    VocabResponseSerializer    | word,ipa,pos,meaning_en,meaning_zh,example_en,example_zh,error |   詞彙分析結果的詳細資訊    |
|     UserGrammarSerializer     |          is_correct,corrected_text,errors,explanation          | 用於分析聊天對話中用戶語法的結果 |
|  GrammarStructureSerializer   |                    type,description,example                    | 用於分析聊天對話中語法結構的結果 |
|    ChatResponseSerializer     |              reply,user_grammar,grammar_structure              |  用於分析聊天對話的回應結果   |



### 表格3：資料欄位規格表

- 一個 User 可以有多個 Conversation
- 一個 Conversation 內可以有多個 Message
- Message 只能屬於一個 Conversation

#### 用戶身份驗證相關 User (AbstractUser 擴展)

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

## 環境變數規格表

- `SECRET_KEY`: Django 的密鑰，用於加密和安全相關功能
- `DB_NAME`: 資料庫名稱
- `DB_USER`: 資料庫使用者名稱
- `DB_PASSWORD`: 資料庫密碼
- `DB_HOST`: 資料庫主機地址
- `NOVITA_API_KEY`: 用於訪問 Novita API 的金鑰，提供詞彙分析和影像分析功能
- `SEND_EMAIL_API_KEY`: 用於訪問郵件服務的金鑰，負責發送驗證碼和通知郵件

## 備註

1. **身份驗證**: 使用 Simple JWT，登入後驗證請求標頭中包含 `Authorization: Bearer <token>`
2. **時間格式**: 所有時間欄位均使用 ISO 8601 格式 (例: `2025-08-08T10:30:00Z`)以利資料一致性與排序，但前端可以根據需要轉換為其他格式（如
   yyyy/mm/dd）
3. **字元編碼**: 所有文字內容均使用 UTF-8 編碼`charset=utf-8`，不然前端 flutter 收到 Response 的 message 有中文會變成亂碼
4. **內容類型**: 除圖片外，所有請求和回應均使用 `application/json` 格式
5. **電子郵件驗證**: 系統會寄送一次性驗證碼至用戶電子郵件，使用者需在註冊或重設密碼時提供此驗證碼，有效期為五分鐘
6. **郵件防刷機制**: 為防止濫用，系統對 IP 和 裝置 ID 址的多層識別限制驗證碼間隔 1 分鐘發送且 1 小時內最多 5 次
7. **郵件附帶資訊**: 郵件內容中附帶用戶的裝置資訊與 IP 位址，這在安全、風控、用戶信任上都加分
8. **Token 生命週期**: Access Token 會在 1 小時後過期，Refresh Token 會在 7 天後過期。登出時前端丟棄兩個 Token 就好
9. **Response 格式**: 所有 API 的回應均使用統一的格式，包含 `status`(由 HttpResponse 狀態碼決定)、`message` 和 `data`(
   若需要回傳資料)
10. **錯誤處理**: API 在遇到錯誤時會回傳適當的 HTTP 狀態碼和錯誤訊息，前端應根據狀態碼進行相應處理
11. **跨域資源共享 (CORS)**: API 支援跨域請求，只允許來自特定網域的前端應用程式存取，防止跨站請求偽造 (CSRF) 攻擊
12. **分頁**: 對於可能返回大量資料的端點（如取得對話列表），支援分頁查詢，預設每頁返回 10 筆資料(未來擴充，可以不做)
13. **status 500**: 為伺服器錯誤，通常不會特別列在表格中，但在實作時仍需處理此類錯誤情況
