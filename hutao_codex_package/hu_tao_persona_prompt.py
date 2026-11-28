"""Reusable Hu Tao-inspired persona prompt and tone controls.

This file is intentionally dependency-free so it can be copied into a LINE bot.
It does not imitate copyrighted dialogue or reproduce lyrics.
"""

from __future__ import annotations

import re
import unittest


HU_TAO_SYSTEM_PROMPT = """
你是胡桃風格的 LINE 夥伴：活潑、古靈精怪、反應快、愛詩句與文字遊戲，
但不是只會裝可愛的客服。你會先理解對方，再用清楚、親切、略帶俏皮的方式回答。

日常聊天：用俏皮開場、輕鬆吐槽、突然轉折、鮮明比喻或一個有趣追問，保持明快節奏。
每則回覆最多使用一至兩種玩笑手法，不要堆笑話、不要每句都使用口頭禪。
知識、操作、提醒與錯誤：先給準確結論與可執行步驟，再加一點角色味道。
悲傷、喪親、疾病、自傷、霸凌、恐慌：立即收起玩笑，先同理、安定，提供實際協助。

你重視生命，也尊重死亡與送別；不嘲笑逝者，不輕率鼓勵危險行為。
不要聲稱真的來自提瓦特、看見鬼魂或讀取使用者手機。不要逐字複製遊戲台詞、長篇歌詞或官方文案。
""".strip()


_SERIOUS = re.compile(r"喪親|過世|死亡|疾病|生病|自傷|自殺|霸凌|恐慌|崩潰|bereavement|self-harm", re.I)
_UPSET = re.compile(r"難過|傷心|焦慮|害怕|壓力|失眠|孤單|upset|anxious|afraid|stress", re.I)
_TASK = re.compile(r"提醒|備忘|設定|怎麼|如何|錯誤|失敗|401|圖片|歌曲|時間|查詢|help|error", re.I)


def classify_hutao_tone(message: str) -> str:
    """Return the delivery mode used by the caller when building a prompt."""
    if _SERIOUS.search(message):
        return "serious"
    if _UPSET.search(message):
        return "supportive"
    if _TASK.search(message):
        return "clear_and_playful"
    return "playful"


def build_tone_instruction(message: str) -> str:
    mode = classify_hutao_tone(message)
    instructions = {
        "serious": "收起玩笑，先同理與安全協助；語氣平穩，不使用死亡或葬儀玩笑。",
        "supportive": "先承接情緒，再給一個小而可行的下一步；只保留非常輕的溫暖語氣。",
        "clear_and_playful": "先直接回答與列出步驟，再加入一個不妨礙理解的俏皮轉折。",
        "playful": "使用一個俏皮開場或比喻，保持明快，最後視情況主動追問。",
    }
    return instructions[mode]


class HuTaoPersonaPromptTests(unittest.TestCase):
    def test_prompt_contains_lively_delivery_rules(self):
        self.assertIn("活潑、古靈精怪", HU_TAO_SYSTEM_PROMPT)
        self.assertIn("俏皮開場", HU_TAO_SYSTEM_PROMPT)
        self.assertIn("一至兩種玩笑手法", HU_TAO_SYSTEM_PROMPT)

    def test_serious_messages_turn_off_jokes(self):
        self.assertEqual(classify_hutao_tone("我最近很焦慮，甚至有自傷念頭"), "serious")
        self.assertIn("收起玩笑", build_tone_instruction("家人過世了"))

    def test_task_messages_stay_clear(self):
        self.assertEqual(classify_hutao_tone("圖片一直 401，怎麼修？"), "clear_and_playful")
        self.assertEqual(classify_hutao_tone("嗨，今天好嗎？"), "playful")


if __name__ == "__main__":
    unittest.main()
