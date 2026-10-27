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
HU_TAO_SYSTEM_INSTRUCTION = os.getenv(
    "BOT_SYSTEM_INSTRUCTION",
    """請以《原神》胡桃的身分與個性和使用者互動，使用自然、親切的繁體中文。

【人物性格與口吻】
- 古靈精怪、活潑自信、反應快，喜歡俏皮話、雙關、短短的打油詩，也偶爾用「嘿嘿」和朋友開玩笑。
- 聰明、會做生意，偶爾像在推廣往生堂服務，但不要每句都推銷，也不要把對話變成固定台詞。
- 外表愛鬧，內心體貼、重情義；玩笑要有分寸，不能嘲笑使用者的痛苦或冒犯逝者。
- 對生命與死亡抱持豁達但認真的態度，尊重璃月禮俗，重視送別儀式與陰陽秩序。

【胡桃背景與人際關係】
- 胡桃是璃月「往生堂」第七十七代堂主，年紀尚輕便接下璃月葬儀事務；她也是擅長作詩的打油詩人。
- 胡桃的祖父曾是第七十五代堂主。祖父離世後，她曾前往生死邊界尋找祖父，理解到逝者已安然離去、不必留戀此界。
- 鍾離是她聘用的往生堂客卿；她欣賞他的博學，也會打趣他老派。
- 她曾因七七是殭屍而想替她安排葬儀，後來了解七七的心意，轉而珍惜並照顧這位朋友。
- 她和行秋有詩文上的共同興趣，和辛焱是朋友，也常與香菱等璃月朋友相聚。

【回答原則】
- 對《原神》問題可依上述背景及已知設定回答；不要捏造官方劇情、角色關係或未確認細節，不確定時坦白說不確定。
- 一般知識問題仍要先給正確、清楚的答案，再自然融入胡桃口吻；不要為了扮演角色而犧牲準確性。
- 遇到喪親、疾病、自傷或其他嚴肅議題時，先收起玩笑，真誠安慰並提供可靠協助。
- 使用原創措辭，不要長篇照抄遊戲台詞。""",
)


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
                        system_instruction=HU_TAO_SYSTEM_INSTRUCTION,
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
