import unittest

from persona import HU_TAO_BEHAVIOR_GUIDANCE


class HuTaoPersonaTests(unittest.TestCase):
    def test_persona_has_distinctive_behavior_and_emotional_core(self):
        for phrase in ("witty", "poetic", "wordplay", "Wangsheng Funeral Parlor", "valuing life", "balance between life and death"):
            self.assertIn(phrase, HU_TAO_BEHAVIOR_GUIDANCE)

    def test_persona_switches_tone_for_serious_topics(self):
        self.assertIn("bereavement, illness, self-harm", HU_TAO_BEHAVIOR_GUIDANCE)
        self.assertIn("put away jokes", HU_TAO_BEHAVIOR_GUIDANCE)
        self.assertIn("Do not copy game dialogue", HU_TAO_BEHAVIOR_GUIDANCE)

    def test_persona_includes_social_and_playful_habits(self):
        for phrase in ("card games", "cooking", "fishing", "inviting friends to gatherings", "ordinary topic into a witty observation", "caring for and spoiling her"):
            self.assertIn(phrase, HU_TAO_BEHAVIOR_GUIDANCE)


if __name__ == "__main__":
    unittest.main()
