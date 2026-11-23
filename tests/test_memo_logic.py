import unittest

from memo_logic import normalize_auto_memo_operations


class MemoLogicTests(unittest.TestCase):
    def test_accepts_stable_preference_addition(self):
        operations = normalize_auto_memo_operations(
            {
                "operations": [
                    {
                        "action": "add",
                        "title": "飲食偏好",
                        "content": "喜歡無糖茶",
                        "confidence": 0.95,
                    }
                ]
            },
            [],
        )
        self.assertEqual(operations, [{"action": "add", "title": "飲食偏好", "content": "喜歡無糖茶"}])

    def test_rejects_small_talk_and_sensitive_content(self):
        operations = normalize_auto_memo_operations(
            {
                "operations": [
                    {"action": "add", "title": "聊天", "content": "今天天氣不錯", "confidence": 0.99},
                    {"action": "add", "title": "密碼", "content": "我的密碼是 secret", "confidence": 0.99},
                ]
            },
            [],
        )
        self.assertEqual(operations, [])

    def test_keeps_update_and_delete_targets_for_existing_notes(self):
        existing = [{"id": 7, "title": "居住地", "content": "台中"}]
        operations = normalize_auto_memo_operations(
            {
                "operations": [
                    {"action": "update", "note_id": 7, "title": "居住地", "content": "台北", "confidence": 0.9},
                    {"action": "delete", "note_id": 7, "confidence": 0.9},
                ]
            },
            existing,
        )
        self.assertEqual(
            operations,
            [
                {"action": "update", "note_id": 7, "title": "居住地", "content": "台北"},
                {"action": "delete", "note_id": 7},
            ],
        )

    def test_rejects_unknown_note_ids(self):
        operations = normalize_auto_memo_operations(
            {"operations": [{"action": "delete", "note_id": 999, "confidence": 1.0}]},
            [{"id": 7, "title": "居住地", "content": "台中"}],
        )
        self.assertEqual(operations, [])


if __name__ == "__main__":
    unittest.main()
