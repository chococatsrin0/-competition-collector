"""测试：公告正文解析与活动链接提取"""

import json
import os
import unittest

from src.activity import extract_join_link, extract_links, normalize_url

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestActivity(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIXTURES, "article_detail_mmt.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.body_tree = json.loads(data["data"]["body"])

    def test_extract_links(self):
        links = extract_links(self.body_tree)
        self.assertEqual(len(links), 2)
        texts = [t for t, _ in links]
        self.assertIn("Join Now", texts)

    def test_extract_join_link(self):
        url = extract_join_link(self.body_tree)
        self.assertEqual(
            url,
            "https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT",
        )

    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("https://www.%suffixOrigin%/activity/x"),
            "https://www.binance.com/activity/x",
        )
        self.assertEqual(
            normalize_url("https://www.binance.com/%locale%/terms"),
            "https://www.binance.com/zh-CN/terms",
        )


if __name__ == "__main__":
    unittest.main()
