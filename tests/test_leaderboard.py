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
        # 页面级 updatedTime 优先：应取 data 顶层的 updatedTime
        from datetime import datetime as dt

        self.assertEqual(
            rows[0].system_updated_at,
            dt.fromtimestamp(1786620000, tz=BEIJING_TZ),
        )
        self.assertEqual(rows[1].system_updated_at, rows[0].system_updated_at)
        # 参与人数 / 总交易量来自 data 顶层
        self.assertEqual(rows[0].eligible_user_count, 2)
        self.assertEqual(rows[0].eligible_trading_volume, 123.45)
        d = rows[0].to_csv_dict()
        self.assertEqual(d["排名"], 1)
        self.assertIn("2026-08-08", d["采集时间"])
        self.assertEqual(d["参与人数"], 2)
        self.assertEqual(d["总交易量USD"], "123.45")
        # 系统更新时间列应使用接口时间，而非采集时间
        expected_str = rows[0].system_updated_at.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S %z")
        self.assertEqual(d["系统更新时间"], expected_str)
        self.assertNotEqual(d["系统更新时间"], d["采集时间"])

    def test_row_level_updated_time_fallback(self):
        # 无 data 顶层 updatedTime 时，回退使用行级 updatedTime
        page = json.loads(json.dumps(self.page_data))
        page["data"].pop("updatedTime")
        page["data"]["resourceSummaryList"]["data"][0]["updatedTime"] = 1786700000000
        with mock.patch("src.leaderboard.post_json", return_value=page):
            rows = collect_leaderboard(100016875, collected_at=datetime(2026, 8, 8, 14, 30, tzinfo=BEIJING_TZ))
        # 行级 updatedTime = 1786700000000，应被解析
        self.assertIsNotNone(rows[0].system_updated_at)
        self.assertEqual(rows[0].system_updated_at.timestamp(), 1786700000)

    def test_override_system_updated_time(self):
        override = datetime(2026, 8, 8, 22, 59, 59, tzinfo=BEIJING_TZ)
        with mock.patch("src.leaderboard.post_json", return_value=self.page_data):
            rows = collect_leaderboard(
                100016875,
                collected_at=datetime(2026, 8, 8, 14, 30, tzinfo=BEIJING_TZ),
                system_updated_at_override=override,
            )
        self.assertEqual(rows[0].system_updated_at, override)
        self.assertEqual(rows[1].system_updated_at, override)


if __name__ == "__main__":
    unittest.main()
