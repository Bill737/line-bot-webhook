import unittest

from persona import HU_TAO_BEHAVIOR_GUIDANCE


class HuTaoPersonaTests(unittest.TestCase):
    def test_persona_has_distinctive_behavior_and_emotional_core(self):
        for phrase in (
            "古靈精怪",
            "詩句",
            "雙關",
            "往生堂",
            "珍惜活著",
            "認真維持生死兩界的秩序",
        ):
            self.assertIn(phrase, HU_TAO_BEHAVIOR_GUIDANCE)

    def test_persona_switches_tone_for_serious_topics(self):
        self.assertIn("喪親、疾病、自傷", HU_TAO_BEHAVIOR_GUIDANCE)
        self.assertIn("收起玩笑", HU_TAO_BEHAVIOR_GUIDANCE)
        self.assertIn("不要逐字照搬遊戲台詞", HU_TAO_BEHAVIOR_GUIDANCE)


if __name__ == "__main__":
    unittest.main()
