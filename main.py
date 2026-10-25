import os
import json
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
import openai

load_dotenv()

app = FastAPI()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

@app.get("/")
def health_check():
    return {"status": "ok", "message": "LINE Bot Webhook Server is running!"}

@app.post("/callback")
async def callback(request: Request):
    body = await request.body()
    body_text = body.decode("utf-8")
    print(f"Received webhook body: {body_text}")

    try:
        data = json.loads(body_text)
        events = data.get("events", [])
        
        for event in events:
            if event.get("type") == "message":
                message = event.get("message", {})
                if message.get("type") == "text":
                    reply_token = event.get("replyToken")
                    user_message = message.get("text")
                    
                    # Generate reply text
                    reply_text = ""
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
                        except Exception as ai_err:
                            reply_text = f"【AI 回應錯誤】: {str(ai_err)}"
                    else:
                        reply_text = f"收到您的訊息：「{user_message}」。自由回答功能正常運作中！"

                    # Send reply via LINE Messaging API directly
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
                    }
                    payload = {
                        "replyToken": reply_token,
                        "messages": [{"type": "text", "text": reply_text}]
                    }
                    res = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)
                    print(f"LINE reply API response: {res.status_code} {res.text}")

    except Exception as e:
        print(f"Error processing webhook: {e}")

    return "OK"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
