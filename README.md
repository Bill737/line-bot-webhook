# LINE Bot Webhook

此專案是部署於 Render 的 LINE Messaging API Webhook。Render 服務網址：
`https://line-bot-webhook-thi0.onrender.com`

## 功能特色
- **Webhook 接收**：處理來自 LINE Platform 的 `POST /callback` 請求，驗證 LINE 簽章 (`X-Line-Signature`)。
- **自由回答（AI 整合）**：設定 Gemini API Key 後使用 Gemini 回答；未設定時回覆提示訊息。
- **圖片理解**：使用者傳送圖片時，透過 LINE message ID 下載圖片並交給 Gemini 分析；支援 JPEG、PNG、WebP、GIF，最多 20 MB。LINE 下載遇到暫時性錯誤會自動重試，失敗時回覆 HTTP 狀態供排查。圖片檔不會寫入資料庫；對話記憶只保存「傳送圖片」提示與文字回覆。
- **貼圖辨識與情緒表達**：收到貼圖時以 LINE webhook 提供的關鍵字、訊息貼圖文字和資源類型判讀；LINE 不提供貼圖圖像，未提供關鍵字時不會假裝看見貼圖。回覆會選擇傳送一則 Messaging API 支援的貼圖，或在文字後加一個顏文字，不會兩者同時使用；嚴肅議題不加裝飾。
- **即時天氣與關心提醒**：詢問天氣、溫度、降雨或是否帶傘時，使用 Open-Meteo 查詢目前狀況及今天／明天／後天預報；可辨識台灣縣市和常見國際城市，未寫地點時預設金門，依降雨、體感溫度與風勢給出帶傘、補水或添衣提醒，回覆標示資料來源。使用免費非商業 API，不需新增金鑰；資料會快取 10 分鐘。
- **角色口吻**：預設以《原神》胡桃的活潑俏皮風格回答，背景設定可在 Render 用 `BOT_SYSTEM_INSTRUCTION` 覆寫。
- **分層聊天記憶**：依 LINE 使用者分開儲存成功對話的文字；近七天原文用於延續聊天，超過七天會在下一次成功互動時濃縮合併進繁體中文長期摘要，摘要成功後才刪除舊原文。傳「記憶框架」查看記憶層、摘要、記事數和儲存方式；傳「最近聊天」查看最多十則近七天對話。圖片只保存「傳送圖片」提示，不保存圖片本身。傳「忘記我」、「清除記憶」或「重置記憶」會清除對話、摘要、記事、提醒與好感度。
- **語音回覆**：文字回覆後會另外傳一則 MP3 語音，預設透過 Fish Audio 使用指定的 `reference_id` 聲線與 `s2.1-pro-free` API 模型；每則回覆只選一種情緒語氣（敏感或難過內容柔和沉穩、疑問句好奇俏皮、驚嘆句明快俏皮、正向句溫暖愉快，其他內容溫暖俏皮），避免同一段語音內反覆切換音色。依逗號或分號加最多三處短停頓提示，句尾則沿用標點的自然停頓，避免語速顯得斷續。另有 Gemini TTS 模式可選。Fish API key 與聲線 ID 僅由 Render 環境變數讀取，不寫入程式碼或日誌。語音音檔只暫存在服務記憶體 15 分鐘；TTS 或音檔傳送失敗時仍保留文字回覆。可用 Render 環境變數 `VOICE_REPLY_ENABLED=false` 關閉或 `PUBLIC_BASE_URL` 指定 HTTPS 公開網址。
- **記事與 UTC+8 提醒**：傳「記事 <內容>」記下記事、「記事列表」查看、「記事刪除 編號」刪除。傳「提醒 2026-11-05 09:30 記得帶傘」建立提醒；列表顯示台灣年月日、星期與時間。到期提醒最多保留 10 分鐘供排程派送，逾期超過 10 分鐘會在每次聊天、查看列表或派送輪詢時清除；成功送達和取消後也會刪除。
- **台灣時間回答**：使用 IANA `Asia/Taipei` 時區。傳「現在幾點」或「現在時間」會由程式直接回覆即時台灣日期與時間；一般對話也會在送往 AI 前加入最新台灣時間，供日期與相對時間判讀。Render 首頁與 `/time` 端點會同時顯示 UTC、台灣時間及 UTC+8 差值，供核對伺服器時間轉換。
- **離線補送提醒**：GitHub Actions 每五分鐘呼叫受金鑰保護的 `/reminders/dispatch`；Render 休眠時由輪詢喚醒，到期提醒會在 10 分鐘寬限內由下一次輪詢補送。排程有數分鐘延遲，不保證精確到分鐘；超過寬限的提醒會刪除，不再補送。
- **完整長回答**：提高回答額度；長文依句子、段落或詞語邊界拆成多個 LINE 氣泡，不直接裁掉尾端內容。
- **主動推送**：受 `PUSH_API_KEY` 保護的 `POST /push` 可推送文字到指定 LINE 對象；文字按句子整理成多個氣泡，每批最多 5 則，長訊息會分批呼叫 LINE Push API。
- **隱私保護**：不在日誌輸出訊息本文、Webhook body、reply token 或憑證。
- **快速部署**：完整支援 GitHub 託管與部署。

---

## 設定步驟 (Setup)

1. **設定 LINE Developer Console**
   - 進入 [LINE Developers Console](https://developers.line.biz/)
   - 在您的 Channel 設定中，將 **Webhook URL** 設定為：
     `https://line-bot-webhook-thi0.onrender.com/callback`
   - 啟用 **Use webhook**。

2. **Render 環境變數**
   在 Render 服務的 Environment 設定以下變數。LINE Token 和 Gemini key 是不同憑證，請勿互換。程式支援 `GEMINI_API_KEY`；為相容既有 Render 設定，也會讀取舊名稱 `apikey`（請將該變數值換成 Gemini API key）：
   ```env
   LINE_CHANNEL_ACCESS_TOKEN=LINE Developers 簽發的 Channel Access Token
   LINE_CHANNEL_SECRET=您的ChannelSecret
   GEMINI_API_KEY=Google AI Studio API Key
   ```
   若使用 Fish Audio，請在 Render Environment 設定 `VOICE_REPLY_PROVIDER=fish`、`FISH_AUDIO_API_KEY`（Fish API key）、`FISH_AUDIO_REFERENCE_ID`（Fish 音色頁的 model ID），並設 `FISH_AUDIO_MODEL=s2.1-pro-free`。Fish Audio 官方標示此 API 模型無需 API 點數；其他模型可能按字元收費，本專案預設不呼叫其他模型。首頁僅顯示目前語音服務與模型，不會顯示 key 或聲線 ID。若使用 Gemini TTS，請將 `VOICE_REPLY_PROVIDER=gemini`；必要時設定 `GEMINI_TTS_VOICE_ID` 和 `GEMINI_TTS_MODEL`。
   設定後重新部署服務。一般回覆預設使用較快的 `gemini-3.5-flash-lite`，可用 `GEMINI_FAST_MODEL` 更改；遇到暫時性服務錯誤時，依序改試 `GEMINI_MODEL`（預設 `gemini-3.6-flash`）與 `GEMINI_FALLBACK_MODEL`（預設 `gemini-3.8-flash`）。

   **要讓記事、提醒與聊天記憶跨 Render 休眠、重啟及重新部署保留，必須在 Render 設定 PostgreSQL 服務的 `DATABASE_URL`。** 本程式支援 PostgreSQL（例如 Neon）；沒有 `DATABASE_URL` 時會退回本機 SQLite，而 Render 免費執行個體的本機資料可能在重啟、重新部署或休眠後遺失。原始文字僅保留七天；較舊對話會整理成精簡摘要。建立提醒不會改變任何 LINE 對話內容送往 Gemini 的方式。

   請在 GitHub Actions repository secrets 設定既有的 `PUSH_API_KEY`，排程 workflow 才能執行。提醒會用相同已設定金鑰呼叫 Render，不需另設新金鑰。GitHub schedule 使用 UTC，但提醒時間存為 Asia/Taipei（UTC+8）。

   主動推送需另外在 Render Environment 設定至少 32 字元的隨機 `PUSH_API_KEY`；未設定時 `/push` 會停用。呼叫時使用 `Authorization: Bearer <PUSH_API_KEY>`，JSON 欄位為 `to`（LINE user/group/room ID）與 `text`（最多 20,000 字元）。不要把此金鑰貼在聊天或寫進程式碼。

   ```bash
   curl -X POST https://line-bot-webhook-thi0.onrender.com/push \
     -H "Authorization: Bearer $PUSH_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"to":"LINE_USER_ID","text":"第一句。第二句。第三句。"}'
   ```

   開啟服務首頁可查看 `ai_enabled`、`voice_reply_enabled`、`line_reply_configured` 與 `webhook_signature_configured` 狀態；只顯示是否有設定，不會顯示任何憑證內容。語音使用 Gemini TTS 免費層額度；LINE 語音會多占一則官方帳號訊息額度，不要升級付費方案。

3. **安裝與運行**
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
