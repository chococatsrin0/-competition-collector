"""测试：活动页 __APP_DATA 解析与主奖池选择"""

import json
import os
import unittest
from unittest import mock

from src.resource import (
    extract_activity_meta,
    find_activity_root,
    parse_app_data,
    select_main_pool,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestResource(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIXTURES, "activity_app_data.json"), encoding="utf-8") as f:
            self.app_data = json.load(f)

    def test_parse_app_data(self):
        html = f'<html><script id="__APP_DATA" type="application/json">{json.dumps(self.app_data)}</script></html>'
        parsed = parse_app_data(html)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["appState"]["loader"]["dataByRouteId"]["de25"]["activityGroup"]["id"], 100016874)

    def test_find_activity_root(self):
        root = find_activity_root(self.app_data)
        self.assertIsNotNone(root)
        self.assertEqual(len(root["activities"]), 3)

    def test_select_main_pool(self):
        root = find_activity_root(self.app_data)
        main = select_main_pool(root["activities"])
        self.assertEqual(main["id"], 100016875)
        self.assertEqual(main["i18nContent"]["title"], "主奖池")

    def test_extract_activity_meta(self):
        html = f'<html><script id="__APP_DATA" type="application/json">{json.dumps(self.app_data)}</script></html>'
        with mock.patch("src.resource.fetch_html", return_value=html):
            meta = extract_activity_meta("https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT")
        self.assertEqual(meta.main_resource_id, 100016875)
        self.assertEqual(meta.token, "MMT")
        self.assertEqual(meta.group_code, "spot-altcoin-festival-wave-MMT")
        self.assertEqual(meta.trading_pairs, ["MMT/USDC", "MMT/USDT"])
        self.assertEqual(meta.threshold, 500)
        self.assertEqual(len(meta.prize_tiers), 3)
        self.assertIsNotNone(meta.start_time)
        self.assertIsNotNone(meta.end_time)


if __name__ == "__main__":
    unittest.main()
