# LINE Bot Webhook

此專案是部署於 Render 的 LINE Messaging API Webhook。Render 服務網址：
`https://line-bot-webhook-thi0.onrender.com`

## 功能特色
- **Webhook 接收**：處理來自 LINE Platform 的 `POST /callback` 請求，驗證 LINE 簽章 (`X-Line-Signature`)。
- **自由回答（AI 整合）**：設定 Gemini API Key 後使用 Gemini 回答；未設定時回覆提示訊息。
- **角色口吻**：預設以《原神》胡桃的活潑俏皮風格回答，背景設定可在 Render 用 `BOT_SYSTEM_INSTRUCTION` 覆寫。
- **個人長期記憶與好感度**：依 LINE 使用者分開保存精簡記憶摘要、互動次數與熟悉程度；回覆後更新，不保存完整聊天紀錄。傳送「忘記我」、「清除記憶」或「重置記憶」可清除該使用者的記憶與好感度。
- **記事與 UTC+8 提醒**：傳「記事 <內容>」記下記事、「記事列表」查看、「記事刪除 編號」刪除。傳「提醒 2026-11-05 09:30 記得帶傘」建立提醒；時間採 Asia/Taipei（UTC+8）。用「提醒列表」查看、「提醒取消 編號」取消。
- **離線補送提醒**：GitHub Actions 每五分鐘呼叫受金鑰保護的 `/reminders/dispatch`；Render 休眠時由輪詢喚醒，到期或逾期提醒會在下一次成功輪詢時補送。排程有數分鐘延遲，不保證精確到分鐘。
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
   設定後重新部署服務。一般回覆預設使用較快的 `gemini-3.5-flash-lite`，可用 `GEMINI_FAST_MODEL` 更改；遇到暫時性服務錯誤時，依序改試 `GEMINI_MODEL`（預設 `gemini-3.6-flash`）與 `GEMINI_FALLBACK_MODEL`（預設 `gemini-3.8-flash`）。

   **要讓記事、提醒與長期記憶跨 Render 休眠、重啟及重新部署保留，必須在 Render 設定免費 PostgreSQL 服務的 `DATABASE_URL`。** 本程式支援 PostgreSQL（例如 Neon 免費方案）；沒有 `DATABASE_URL` 時會退回本機 SQLite，而 Render 免費執行個體的本機資料會在重啟、重新部署或休眠後遺失。只需保存精簡記憶摘要，不保存完整聊天紀錄。建立提醒不會改變任何 LINE 對話內容送往 Gemini 的方式。

   請在 GitHub Actions repository secrets 設定既有的 `PUSH_API_KEY`，排程 workflow 才能執行。提醒會用相同已設定金鑰呼叫 Render，不需另設新金鑰。GitHub schedule 使用 UTC，但提醒時間存為 Asia/Taipei（UTC+8）。

   主動推送需另外在 Render Environment 設定至少 32 字元的隨機 `PUSH_API_KEY`；未設定時 `/push` 會停用。呼叫時使用 `Authorization: Bearer <PUSH_API_KEY>`，JSON 欄位為 `to`（LINE user/group/room ID）與 `text`（最多 20,000 字元）。不要把此金鑰貼在聊天或寫進程式碼。

   ```bash
   curl -X POST https://line-bot-webhook-thi0.onrender.com/push \
     -H "Authorization: Bearer $PUSH_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"to":"LINE_USER_ID","text":"第一句。第二句。第三句。"}'
   ```

   開啟服務首頁可查看 `ai_enabled`、`line_reply_configured` 與 `webhook_signature_configured` 狀態；只顯示是否有設定，不會顯示任何憑證內容。

3. **安裝與運行**
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
