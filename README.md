# LINE Bot Webhook

此專案是部署於 Render 的 LINE Messaging API Webhook。Render 服務網址：
`https://line-bot-webhook-thi0.onrender.com`

## 功能特色
- **Webhook 接收**：處理來自 LINE Platform 的 `POST /callback` 請求，驗證 LINE 簽章 (`X-Line-Signature`)。
- **自由回答（AI 整合）**：設定 Gemini API Key 後使用 Gemini 回答；未設定時回覆提示訊息。
- **角色口吻**：預設以《原神》胡桃的活潑俏皮風格回答，背景設定可在 Render 用 `BOT_SYSTEM_INSTRUCTION` 覆寫。
- **個人長期記憶與好感度**：依 LINE 使用者分開保存精簡記憶摘要、互動次數與熟悉程度；回覆後更新，不保存完整聊天紀錄。傳送「忘記我」、「清除記憶」或「重置記憶」可清除該使用者的記憶與好感度。
- **訊息長度保護**：回答會控制篇幅，並在超出 LINE 單則字元上限時優先於完整句子或詞語邊界收尾。
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
   設定後重新部署服務。`GEMINI_MODEL` 為選填，預設為 `gemini-3.6-flash`；若模型遇到暫時性服務錯誤，會改試 `GEMINI_FALLBACK_MODEL`（預設 `gemini-3.8-flash`）。

   記憶資料庫預設為 `data/hu_tao_memory.sqlite3`，可用 `MEMORY_DB_PATH` 更改。Render 免費執行個體沒有持久磁碟，休眠、重啟或重新部署會清除本機記憶。要跨休眠與部署保留記憶，請使用支援持久儲存的方案並把 `MEMORY_DB_PATH` 指向掛載磁碟，例如 `/var/data/hu_tao_memory.sqlite3`。目前不會自動將聊天內容傳送到其他資料庫服務。

   開啟服務首頁可查看 `ai_enabled`、`line_reply_configured` 與 `webhook_signature_configured` 狀態；只顯示是否有設定，不會顯示任何憑證內容。

3. **安裝與運行**
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
