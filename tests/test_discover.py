"""测试：公告发现与关键词过滤"""

import json
import os
import unittest
from datetime import datetime, timedelta
from unittest import mock

from src.discover import Competition, _parse_article_list, discover_competitions, filter_competitions

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestDiscover(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIXTURES, "article_list_zh.json"), encoding="utf-8") as f:
            self.list_data = json.load(f)

    def test_parse_article_list(self):
        articles = _parse_article_list(self.list_data)
        self.assertEqual(len(articles), 4)
        self.assertEqual(articles[1]["title"], "MMT交易量锦标赛：交易瓜分高达2,000,000 MMT奖池")

    def test_filter_competitions(self):
        announcements = [
            Competition(
                title=a["title"],
                article_id=a["id"],
                article_code=a["code"],
                release_date=datetime.fromtimestamp(a["releaseDate"] / 1000),
                announcement_url=f"https://www.binance.com/zh-CN/support/announcement/detail/{a['code']}",
            )
            for a in _parse_article_list(self.list_data)
        ]
        comps = filter_competitions(announcements)
        titles = [c.title for c in comps]
        self.assertIn("MMT交易量锦标赛：交易瓜分高达2,000,000 MMT奖池", titles)
        self.assertIn("BABY交易量锦标赛：交易瓜分高达30,000,000 BABY奖池", titles)
        # 非锦标赛公告不应命中
        self.assertNotIn("币安学院比特币专题页面：八月完成测试赢取BTC奖励！", titles)

    def test_token_hint(self):
        comp = Competition(
            title="MMT交易量锦标赛：交易瓜分高达2,000,000 MMT奖池",
            article_id=1,
            article_code="x",
            release_date=None,
            announcement_url="",
        )
        self.assertIsNotNone(comp.token)

    @mock.patch("src.discover.fetch_announcements")
    def test_recent_window(self, mock_fetch):
        now = datetime.now().astimezone()
        old = now - timedelta(days=30)
        mock_fetch.return_value = [
            Competition(title="AAA交易量锦标赛", article_id=1, article_code="a",
                        release_date=now, announcement_url=""),
            Competition(title="BBB交易量锦标赛", article_id=2, article_code="b",
                        release_date=old, announcement_url=""),
        ]
        comps = discover_competitions(max_age_days=7)
        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[0].title, "AAA交易量锦标赛")


if __name__ == "__main__":
    unittest.main()
