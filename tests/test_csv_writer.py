"""测试：CSV 输出"""

import csv
import os
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from src.config import BEIJING_TZ, CSV_COLUMNS
from src.csv_writer import build_csv_path, write_leaderboard_csv
from src.leaderboard import LeaderboardRow


class TestCsvWriter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.collected_at = datetime(2026, 8, 8, 14, 30, tzinfo=BEIJING_TZ)

    def test_build_path(self):
        self.assertEqual(
            build_csv_path("MMT", self.collected_at),
            os.path.join("data", "leaderboard", "MMT", "202608081430.csv"),
        )

    def test_write_csv(self):
        rows = [
            LeaderboardRow(1, "关山飞渡", 38254101.77, self.collected_at, None),
            LeaderboardRow(2, "VNBACK", 35168694.73, self.collected_at, None),
        ]
        with mock.patch("src.csv_writer.LEADERBOARD_DIR", self.tmp):
            path = write_leaderboard_csv("MMT", rows, collected_at=self.collected_at)
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            self.assertEqual(reader.fieldnames, CSV_COLUMNS)
            content = list(reader)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]["用户名称"], "关山飞渡")
        self.assertEqual(content[0]["排名"], "1")
        self.assertIn("2026-08-08", content[0]["采集时间"])


if __name__ == "__main__":
    unittest.main()
