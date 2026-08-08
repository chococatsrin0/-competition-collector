"""测试：采集主流程与「活动结束 + 宽限期后停止」逻辑"""

import unittest
from datetime import datetime, timedelta
from unittest import mock

from src.collector import collect_one, is_expired
from src.config import BEIJING_TZ
from src.discover import Competition
from src.leaderboard import LeaderboardRow
from src.resource import ActivityMeta


def make_comp(title="MMT交易量锦标赛"):
    return Competition(title=title, article_id=1, article_code="abc", release_date=None, announcement_url="")


def make_meta(end_time):
    return ActivityMeta(
        group_id=100016874,
        group_code="spot-altcoin-festival-wave-MMT",
        main_resource_id=100016875,
        token="MMT",
        start_time=None,
        end_time=end_time,
        activity_url="https://www.binance.com/activity/x",
    )


class TestExpired(unittest.TestCase):
    def test_active_within_grace(self):
        now = datetime(2026, 8, 9, 0, 0, tzinfo=BEIJING_TZ)
        # 结束时间 + 3 小时 < now，仍应采集
        end = now - timedelta(hours=3)
        self.assertFalse(is_expired(make_meta(end), now))

    def test_expired_after_grace(self):
        now = datetime(2026, 8, 9, 0, 0, tzinfo=BEIJING_TZ)
        # 结束时间 + 5 小时 < now，应停止
        end = now - timedelta(hours=5)
        self.assertTrue(is_expired(make_meta(end), now))

    def test_no_end_time_never_expired(self):
        now = datetime(2026, 8, 9, 0, 0, tzinfo=BEIJING_TZ)
        self.assertFalse(is_expired(make_meta(None), now))


class TestCollectOne(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 9, 0, 0, tzinfo=BEIJING_TZ)
        self.row = LeaderboardRow(1, "测试用户", 100.0, self.now, None)

    def test_active_collected(self):
        meta = make_meta(self.now + timedelta(hours=1))
        with (
            mock.patch("src.collector.resolve_activity_url", return_value="https://www.binance.com/activity/x"),
            mock.patch("src.collector.extract_activity_meta", return_value=meta),
            mock.patch("src.collector.collect_leaderboard", return_value=[self.row]),
            mock.patch("src.collector.write_leaderboard_csv", return_value="data/leaderboard/MMT/1.csv") as write,
        ):
            path = collect_one(make_comp(), collected_at=self.now)
        self.assertEqual(path, "data/leaderboard/MMT/1.csv")
        write.assert_called_once()

    def test_expired_skipped(self):
        # 结束时间 + 5 小时 < now -> 跳过，不采集不写 CSV
        meta = make_meta(self.now - timedelta(hours=5))
        with (
            mock.patch("src.collector.resolve_activity_url", return_value="https://www.binance.com/activity/x"),
            mock.patch("src.collector.extract_activity_meta", return_value=meta),
            mock.patch("src.collector.collect_leaderboard") as collect,
            mock.patch("src.collector.write_leaderboard_csv") as write,
        ):
            path = collect_one(make_comp(), collected_at=self.now)
        self.assertIsNone(path)
        collect.assert_not_called()
        write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
