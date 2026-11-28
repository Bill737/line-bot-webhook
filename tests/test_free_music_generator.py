import unittest

from free_music_generator import (
    ACE_STEP_SPACE,
    build_ace_step_request,
    extract_audio_url,
)


class FreeMusicGeneratorTests(unittest.TestCase):
    def test_request_contains_chinese_vocal_lyrics_and_safe_original_direction(self):
        request = build_ace_step_request("溫柔的晚安曲", length_seconds=30)
        self.assertEqual(request["endpoint"], "/call/generation_wrapper")
        self.assertEqual(request["data"][0], "acestep-v15-turbo")
        self.assertIn("zh", request["data"])
        self.assertIn("original", request["data"][2].lower())
        self.assertIn("溫柔的晚安曲", request["data"][2])

    def test_extract_audio_url_accepts_gradio_file_result(self):
        result = {"url": "https://cdn.example/song.mp3", "mime_type": "audio/mpeg"}
        self.assertEqual(extract_audio_url(result), "https://cdn.example/song.mp3")

    def test_provider_space_is_configurable_but_defaults_to_ace_step(self):
        self.assertEqual(ACE_STEP_SPACE, "ACE-Step/Ace-Step-v1.5")


if __name__ == "__main__":
    unittest.main()
