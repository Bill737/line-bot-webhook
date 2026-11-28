"""Best-effort free music generation through a public Hugging Face Space.

ACE-Step can generate vocal songs and lyrics, but the public Space is shared
ZeroGPU infrastructure. This adapter therefore treats capacity errors as a
normal unavailable result and never blocks the LINE text reply.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import requests

logger = logging.getLogger("line_bot.free_music")

ACE_STEP_SPACE = "ACE-Step/Ace-Step-v1.5"
ACE_STEP_HOST = "https://ace-step-ace-step-v1-5.hf.space"
MUSICGEN_HOST = "https://facebook-musicgen.hf.space"
FREE_MUSIC_TIMEOUT_SECONDS = max(30, min(300, int(os.getenv("FREE_MUSIC_TIMEOUT_SECONDS", "180"))))


def build_ace_step_request(song_request: str, length_seconds: int = 30) -> dict[str, Any]:
    """Build the current ACE-Step Gradio positional request.

    The Space exposes a positional ``generation_wrapper`` endpoint. Keeping
    the list in one function makes endpoint changes easy to review.
    """
    length_seconds = max(10, min(120, int(length_seconds)))
    prompt = (
        "Original Chinese vocal song, cheerful and mischievous, playful female vocals, "
        "clear Mandarin pronunciation, bright Chinese pop with light traditional instruments. "
        f"Original theme: {song_request[:500]}"
    )
    lyrics = "[Verse]\n俏皮地唱出今天的小故事\n[Chorus]\n嘿嘿，風把煩惱吹走啦"
    # After the four simple-mode controls, these positions mirror the current
    # Space example payload: captions, lyrics, BPM, key, meter, language,
    # inference settings, audio duration, batch settings, and output controls.
    data: list[Any] = [
        "acestep-v15-turbo", "simple", prompt, "zh",
        prompt, lyrics, 110, "C major", "4/4", "zh", 8, 7, True, "-1",
        None, length_seconds, 1, None, 0, -1, "text2music", 0.85, 1.0,
        1.0, 0.95, "", "text2music", True, 0, 0, 1.0, "ode", "", "mp3",
        0.0, True, 1.0, 0, 0.0, "", True, True, True, True, 0.01, 3,
        "vocals", ["vocals"], True,
    ]
    return {"endpoint": "/call/generation_wrapper", "data": data}


def extract_audio_url(value: Any) -> str | None:
    """Find an audio URL in Gradio's nested result structure."""
    if isinstance(value, dict):
        for key in ("url", "path"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.startswith(("https://", "http://")):
                if re.search(r"\.(mp3|wav|flac|ogg)(?:\?|$)", candidate, re.I) or key == "url":
                    return candidate
        for child in value.values():
            found = extract_audio_url(child)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for child in value:
            found = extract_audio_url(child)
            if found:
                return found
    return None


def _headers(hf_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {hf_token}"} if hf_token else {}


def _wait_for_result(response: requests.Response, host: str, hf_token: str) -> Any:
    body = response.json()
    event_id = body.get("event_id")
    if not event_id:
        raise RuntimeError("Hugging Face did not return an event id")
    stream = requests.get(
        f"{host}/call/generation_wrapper/{event_id}",
        headers=_headers(hf_token),
        stream=True,
        timeout=FREE_MUSIC_TIMEOUT_SECONDS,
    )
    stream.raise_for_status()
    for raw_line in stream.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data:"):
            continue
        payload = json.loads(raw_line[5:].strip())
        if payload.get("msg") == "process_completed":
            if payload.get("success") is False:
                raise RuntimeError(str(payload.get("output") or "generation failed"))
            return payload.get("output")
    raise RuntimeError("Hugging Face generation ended without a result")


def _generate_musicgen_fallback(song_request: str, hf_token: str) -> tuple[bytes, int] | None:
    """Use MusicGen as an instrumental-only fallback when ACE-Step is unavailable."""
    response = requests.post(
        f"{MUSICGEN_HOST}/run/predict_batched",
        headers={**_headers(hf_token), "Content-Type": "application/json"},
        json={"texts": f"Original instrumental accompaniment for: {song_request[:500]}", "melodies": None},
        timeout=30,
    )
    response.raise_for_status()
    audio_url = extract_audio_url(response.json())
    if not audio_url:
        return None
    audio = requests.get(audio_url, timeout=60)
    audio.raise_for_status()
    return (audio.content, 10000) if audio.content else None


def generate_free_song(song_request: str, length_seconds: int = 30) -> tuple[bytes, int] | None:
    """Generate and download an original vocal song, returning MP3 bytes."""
    host = os.getenv("FREE_MUSIC_HOST", ACE_STEP_HOST).rstrip("/")
    hf_token = os.getenv("HF_TOKEN", "").strip()
    request = build_ace_step_request(song_request, length_seconds)
    try:
        response = requests.post(
            f"{host}{request['endpoint']}",
            headers={**_headers(hf_token), "Content-Type": "application/json"},
            json={"data": request["data"]},
            timeout=30,
        )
        response.raise_for_status()
        output = _wait_for_result(response, host, hf_token)
        audio_url = extract_audio_url(output)
        if not audio_url:
            raise RuntimeError("Hugging Face result did not contain audio")
        audio = requests.get(audio_url, timeout=60)
        audio.raise_for_status()
        if not audio.content:
            raise RuntimeError("Hugging Face returned empty audio")
        return audio.content, length_seconds * 1000
    except (requests.RequestException, RuntimeError, ValueError, json.JSONDecodeError) as error:
        logger.warning("ACE-Step unavailable; trying instrumental fallback: type=%s", type(error).__name__)
        try:
            return _generate_musicgen_fallback(song_request, hf_token)
        except (requests.RequestException, RuntimeError, ValueError, json.JSONDecodeError) as fallback_error:
            logger.warning("Free music fallback unavailable: type=%s", type(fallback_error).__name__)
            return None

