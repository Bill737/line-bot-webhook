# LINE Bot Webhook

此專案是部署於 Render 的 LINE Messaging API Webhook。Render 服務網址：
`https://line-bot-webhook-thi0.onrender.com`

## 功能特色
- **Webhook 接收**：處理來自 LINE Platform 的 `POST /callback` 請求，驗證 LINE 簽章 (`X-Line-Signature`)。
- **自由回答（AI 整合）**：設定 OpenAI API Key 後使用 GPT 回答；未設定時回覆提示訊息。
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
   在 Render 服務的 Environment 設定以下變數。LINE Token 和 OpenAI key 是不同憑證，請勿互換：
   ```env
   LINE_CHANNEL_ACCESS_TOKEN=LINE Developers 簽發的 Channel Access Token
   LINE_CHANNEL_SECRET=您的ChannelSecret
   OPENAI_API_KEY=OpenAI API Key
   ```
   設定後重新部署服務。`OPENAI_MODEL` 為選填，預設為 `gpt-4o-mini`。

3. **安裝與運行**
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
