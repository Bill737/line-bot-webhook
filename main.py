import os
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

app = FastAPI()

# LINE Bot credentials from environment variables
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Optional OpenAI / LLM configuration for free answering
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

@app.get("/")
def health_check():
    return {"status": "ok", "message": "LINE Bot Webhook Server is running!"}

@app.post("/callback")
async def callback(request: Request):
    # Get X-Line-Signature header value
    signature = request.headers.get("X-Line-Signature", "")

    # Get request body as text
    body = await request.body()
    body_text = body.decode("utf-8")

    # Handle webhook body
    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature. Please check your channel secret/access token.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    reply_text = ""

    # Free answering logic: use OpenAI if key is available, otherwise intelligent echo/response
    if OPENAI_API_KEY:
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful, friendly AI assistant on LINE. Answer freely and naturally in Traditional Chinese."},
                    {"role": "user", "content": user_message}
                ]
            )
            reply_text = response.choices[0].message.content.strip()
        except Exception as e:
            reply_text = f"【AI 回應錯誤】: {str(e)}"
    else:
        # Free answering default fallback
        reply_text = f"收到您的訊息：「{user_message}」。已成功對接到 Cloudflare Tunnel 回調網址！(自由回答功能運作中)"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
