"""测试：排行榜采集"""

import json
import os
import unittest
from datetime import datetime
from unittest import mock

from src.config import BEIJING_TZ
from src.leaderboard import collect_leaderboard, fetch_leaderboard_page

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestLeaderboard(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIXTURES, "leaderboard_page.json"), encoding="utf-8") as f:
            self.page_data = json.load(f)

    def test_fetch_page(self):
        with mock.patch("src.leaderboard.post_json", return_value=self.page_data):
            page = fetch_leaderboard_page(100016875)
        self.assertEqual(page["total"], 2)
        self.assertEqual(len(page["data"]), 2)

    def test_collect_rows(self):
        with mock.patch("src.leaderboard.post_json", return_value=self.page_data):
            rows = collect_leaderboard(100016875, collected_at=datetime(2026, 8, 8, 14, 30, tzinfo=BEIJING_TZ))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].rank, 1)
        self.assertEqual(rows[0].user_name, "关山飞渡")
        self.assertEqual(rows[0].trading_volume_usd, 38254101.76539)
        d = rows[0].to_csv_dict()
        self.assertEqual(d["排名"], 1)
        self.assertIn("2026-08-08", d["采集时间"])


if __name__ == "__main__":
    unittest.main()
