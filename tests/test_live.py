"""集成测试（需联网）：按验收标准 TC001-TC004 验证真实接口"""

import json
import os
import unittest

from src.activity import resolve_activity_url
from src.discover import discover_competitions
from src.leaderboard import collect_leaderboard, fetch_leaderboard_page

NETWORK_AVAILABLE = os.environ.get("BINANCE_LIVE_TEST") == "1"


@unittest.skipUnless(NETWORK_AVAILABLE, "设置环境变量 BINANCE_LIVE_TEST=1 运行联网集成测试")
class TestLiveIntegration(unittest.TestCase):
    """TC001-TC004 联网验收"""

    def test_tc001_discover(self):
        comps = discover_competitions()
        self.assertGreater(len(comps), 0)
        for c in comps:
            self.assertTrue(c.article_code)
            self.assertTrue(c.announcement_url)
        print("\n[TC001] 发现交易锦标赛:", [c.title for c in comps[:5]])

    def test_tc002_activity_url(self):
        comps = discover_competitions()
        found = False
        for c in comps:
            url = resolve_activity_url(c)
            if url and "/activity/" in url:
                found = True
                print(f"\n[TC002] {c.title}\n  -> {url}")
                break
        self.assertTrue(found, "未从公告正文解析出活动 URL")

    def test_tc003_main_resource(self):
        # 用探索阶段确定的真实活动页
        from src.resource import extract_activity_meta

        meta = extract_activity_meta(
            "https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT"
        )
        print(f"\n[TC003] resourceId={meta.main_resource_id} token={meta.token} "
              f"start={meta.start_time} end={meta.end_time}")
        self.assertIsNotNone(meta.main_resource_id)
        self.assertEqual(meta.token, "MMT")

    def test_tc004_leaderboard(self):
        page = fetch_leaderboard_page(100016875, page_index=1, page_size=5)
        self.assertGreater(page.get("total", 0), 0)
        rows = collect_leaderboard(100016875)
        self.assertGreater(len(rows), 0)
        print(f"\n[TC004] 共采集 {len(rows)} 行，首行: {rows[0].to_csv_dict()}")


if __name__ == "__main__":
    unittest.main()
