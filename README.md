# LINE Bot Webhook (Cloudflare Tunnel)

此專案是為 LINE Bot 設計的 FastAPI Webhook 伺服器，已對接您的 Cloudflare Tunnel 內網穿透回調網址：
`https://ton-regional-accomplish-cod.trycloudflare.com/callback`

## 功能特色
- **Webhook 接收**：處理來自 LINE Platform 的 `POST /callback` 請求，自動驗證簽章 (`X-Line-Signature`)。
- **自由回答（AI 整合）**：支援整合 OpenAI API 進行智慧對話與自由回答；若未設定 OpenAI Key，則會自動回覆預設確認訊息。
- **快速部署**：完整支援 GitHub 託管與部署。

---

## 設定步驟 (Setup)

1. **設定 LINE Developer Console**
   - 進入 [LINE Developers Console](https://developers.line.biz/)
   - 在您的 Channel 設定中，將 **Webhook URL** 設定為：
     `https://ton-regional-accomplish-cod.trycloudflare.com/callback`
   - 啟用 **Use webhook**。

2. **環境變數設定 (.env)**
   複製 `.env.example` 為 `.env` 並填入您的憑證：
   ```env
   LINE_CHANNEL_ACCESS_TOKEN=您的ChannelAccessAccessToken
   LINE_CHANNEL_SECRET=您的ChannelSecret
   OPENAI_API_KEY=您的OpenAIAPIKey (選填，用於自由回答)
   ```

3. **安裝與運行**
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
