"""Prepare LINE replies for clear voice delivery."""

import re


VOICE_DIRECTION = "[clear Mandarin pronunciation, articulate every word, moderate pace, gentle sentence pauses]"


def prepare_voice_text(text: str) -> str:
    spoken = text.strip()
    spoken = re.split(r"\n\s*參考(?:來源|資料)\s*[：:]", spoken, maxsplit=1)[0]
    spoken = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", spoken)
    spoken = re.sub(r"https?://\S+|www\.\S+", "", spoken)
    spoken = re.sub(r"^\s*[-*•]\s*", "", spoken, flags=re.MULTILINE)
    spoken = re.sub(r"\s+", " ", spoken).strip()
    if not spoken:
        return ""
    spoken = re.sub(r"([。！？!?])\s*", r"\1 [short pause] ", spoken)
    spoken = re.sub(r"\s+", " ", spoken).strip()
    return f"{VOICE_DIRECTION} {spoken}"
