from __future__ import annotations

import unittest

from edkg.normalize import collapse_ws, quote_in_text, strip_html


class NormalizeTests(unittest.TestCase):
    def test_collapse_whitespace_keeps_punctuation(self) -> None:
        self.assertEqual(collapse_ws(" 胸痛 \n 伴大汗（脐以上） "), "胸痛伴大汗（脐以上）")

    def test_strip_html_skips_script_and_style(self) -> None:
        text = strip_html(
            "<html><head><style>x{}</style><script>alert(1)</script></head>"
            "<body><p>胸痛 <b>伴</b> 大汗</p></body></html>"
        )
        self.assertIn("胸痛", text)
        self.assertIn("大汗", text)
        self.assertNotIn("alert", text)
        self.assertNotIn("x{}", text)

    def test_quote_in_text_ignores_html_spacing(self) -> None:
        text = strip_html("<p>所有胸痛患者<br/>在首次医疗接触后应在10 min内完成心电图检查</p>")
        self.assertTrue(quote_in_text("所有胸痛患者在首次医疗接触后应在10 min内完成心电图检查", text))
        self.assertFalse(quote_in_text("不存在的引文", text))


if __name__ == "__main__":
    unittest.main()
