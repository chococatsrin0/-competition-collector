"""测试：定时任务计算"""

import unittest
from datetime import datetime, timezone

from src.config import BEIJING_TZ
from src.scheduler import next_run


class TestScheduler(unittest.TestCase):
    def test_next_run_before_30(self):
        now = datetime(2026, 8, 8, 14, 10, tzinfo=BEIJING_TZ)
        nxt = next_run(now, minute=30)
        self.assertEqual(nxt.astimezone(BEIJING_TZ).strftime("%H:%M"), "14:30")

    def test_next_run_after_30(self):
        now = datetime(2026, 8, 8, 14, 40, tzinfo=BEIJING_TZ)
        nxt = next_run(now, minute=30)
        self.assertEqual(nxt.astimezone(BEIJING_TZ).strftime("%H:%M"), "15:30")

    def test_next_run_exact(self):
        now = datetime(2026, 8, 8, 14, 30, 0, tzinfo=BEIJING_TZ)
        nxt = next_run(now, minute=30)
        self.assertEqual(nxt.astimezone(BEIJING_TZ).strftime("%H:%M"), "15:30")

    def test_utc_input(self):
        # 北京时间 2026-08-08 14:30 对应 UTC 06:30
        now = datetime(2026, 8, 8, 6, 10, tzinfo=timezone.utc)
        nxt = next_run(now, minute=30)
        self.assertEqual(nxt.astimezone(BEIJING_TZ).strftime("%H:%M"), "14:30")


if __name__ == "__main__":
    unittest.main()
