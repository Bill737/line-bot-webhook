import unittest

from voice_text import prepare_voice_text


class VoiceTextTests(unittest.TestCase):
    def test_removes_urls_and_source_section_from_spoken_text(self):
        prepared = prepare_voice_text("答案在這裡。\n\n參考來源：\n- 官方：https://example.com/page")
        self.assertNotIn("https://", prepared)
        self.assertNotIn("參考來源", prepared)
        self.assertIn("答案在這裡", prepared)

    def test_requests_clear_mandarin_delivery_and_sentence_pauses(self):
        prepared = prepare_voice_text("第一句。第二句！")
        self.assertTrue(prepared.startswith("[clear Mandarin pronunciation"))
        self.assertIn("[short pause]", prepared)
        self.assertIn("moderate pace", prepared)


if __name__ == "__main__":
    unittest.main()
