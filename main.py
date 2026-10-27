import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from google import genai
from google.genai import types

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("line_bot")

app = FastAPI()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
# `apikey` is supported for compatibility with the existing Render environment.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("apikey", "")


def verify_signature(body: bytes, signature: str) -> bool:
    if not LINE_CHANNEL_SECRET or not signature:
        return False
    digest = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, signature)


def create_reply(user_message: str) -> str:
    if not GEMINI_API_KEY:
        return f"收到你的訊息：「{user_message}」。目前 AI 尚未設定，請稍後再試。"

    client = genai.Client(api_key=GEMINI_API_KEY)
    primary_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.8-flash")
    models = [primary_model]
    if fallback_model != primary_model:
        models.append(fallback_model)

    for model_index, model in enumerate(models):
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction="你是友善、有幫助的 LINE 助理，請使用自然的繁體中文回答。",
                        max_output_tokens=2048,
                    ),
                )
                answer = (response.text or "").strip()
                return answer[:5000] or "我暫時想不到合適的回答，請再試一次。"
            except Exception as error:
                # Retry temporary errors briefly, and fall back to another model on overload.
                status_code = getattr(error, "code", None)
                if status_code in {429, 500, 502, 503, 504} and attempt == 0:
                    delay = 1.5
                    logger.warning(
                        "Gemini temporary error: status=%s; retrying in %.1fs",
                        status_code,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                if status_code in {502, 503, 504} and model_index + 1 < len(models):
                    logger.warning(
                        "Gemini model unavailable: status=%s; trying fallback model",
                        status_code,
                    )
                    break
                logger.error(
                    "Gemini request failed: type=%s status=%s",
                    type(error).__name__,
                    status_code,
                )
                return "抱歉，AI 服務暫時無法回答，請稍後再試。"

    return "抱歉，AI 服務暫時無法回答，請稍後再試。"


def process_events(events: list[dict[str, Any]]) -> None:
    if not LINE_CHANNEL_ACCESS_TOKEN:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN is not configured")
        return

    for event in events:
        message = event.get("message") or {}
        reply_token = event.get("replyToken")
        if event.get("type") != "message" or message.get("type") != "text" or not reply_token:
            continue

        reply_text = create_reply(message.get("text", ""))
        try:
            response = requests.post(
                "https://api.line.me/v2/bot/message/reply",
                headers={
                    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": reply_text}],
                },
                timeout=10,
            )
            if response.ok:
                logger.info("LINE reply sent successfully")
            else:
                # Do not log response bodies; they may contain user or request data.
                logger.error("LINE reply failed with HTTP %s", response.status_code)
        except requests.RequestException:
            logger.exception("LINE reply request failed")


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "LINE Bot Webhook Server is running",
        "ai_enabled": bool(GEMINI_API_KEY),
        "ai_provider": "gemini",
        "line_reply_configured": bool(LINE_CHANNEL_ACCESS_TOKEN),
        "webhook_signature_configured": bool(LINE_CHANNEL_SECRET),
    }


@app.post("/callback")
async def callback(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    if not verify_signature(body, signature):
        logger.warning("Rejected LINE webhook with invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = payload.get("events", [])
    if events:
        background_tasks.add_task(process_events, events)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
