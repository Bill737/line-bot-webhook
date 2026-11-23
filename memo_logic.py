"""Pure validation for AI-proposed personal memo operations."""

import re
from typing import Any


SENSITIVE_PATTERN = re.compile(
    r"密碼|password|api[_ -]?key|token|驗證碼|信用卡|卡號|身分證|身份證|護照|私鑰|secret|病歷|診斷|處方",
    re.I,
)
SMALL_TALK_PATTERN = re.compile(r"^(?:今天天氣不錯|天氣不錯|早安|晚安|哈哈|呵呵|收到|謝謝|掰掰|再見)[！!。.! ]*$")
ALLOWED_ACTIONS = {"add", "update", "archive", "delete"}


def _text(value: Any, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def normalize_auto_memo_operations(payload: Any, existing_notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate model output before it can mutate a user's memo records."""
    if not isinstance(payload, dict) or not isinstance(payload.get("operations"), list):
        return []
    existing_ids = {int(note["id"]) for note in existing_notes if str(note.get("id", "")).isdigit()}
    operations: list[dict[str, Any]] = []
    for raw in payload["operations"][:8]:
        if not isinstance(raw, dict) or raw.get("action") not in ALLOWED_ACTIONS:
            continue
        try:
            confidence = float(raw.get("confidence", 0))
        except (TypeError, ValueError):
            continue
        if confidence < 0.75:
            continue
        action = raw["action"]
        if action in {"update", "archive", "delete"}:
            note_id = raw.get("note_id")
            if not str(note_id).isdigit() or int(note_id) not in existing_ids:
                continue
            operation = {"action": action, "note_id": int(note_id)}
            if action == "update":
                title = _text(raw.get("title"), 120)
                content = _text(raw.get("content"), 2000)
                if not title or not content or SENSITIVE_PATTERN.search(f"{title} {content}"):
                    continue
                operation.update(title=title, content=content)
            operations.append(operation)
            continue

        title = _text(raw.get("title"), 120)
        content = _text(raw.get("content"), 2000)
        if not title or not content or len(content) < 5:
            continue
        if SENSITIVE_PATTERN.search(f"{title} {content}") or SMALL_TALK_PATTERN.fullmatch(content):
            continue
        operations.append({"action": "add", "title": title, "content": content})
    return operations
