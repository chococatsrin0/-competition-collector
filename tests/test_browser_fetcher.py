"""测试：浏览器捕获系统更新时间"""

import unittest
from datetime import datetime
from unittest import mock

from src.browser_fetcher import capture_system_updated_time
from src.config import BEIJING_TZ


class FakeResponse:
    def __init__(self, url, payload):
        self.url = url
        self._payload = payload

    def json(self):
        return self._payload


class FakePage:
    def __init__(self):
        self.handlers = {}
        self.goto_calls = []
        self.auto_response = None

    def on(self, event, fn):
        self.handlers[event] = fn

    def trigger(self, res):
        self.handlers["response"](res)

    def goto(self, url, **kwargs):
        self.goto_calls.append(url)
        if self.auto_response is not None:
            self.handlers["response"](self.auto_response)

    def wait_for_timeout(self, ms):
        pass

    def evaluate(self, js):
        pass

    def close(self):
        pass


class FakeContext:
    def __init__(self):
        self.page = FakePage()

    def new_page(self):
        return self.page


class TestCaptureSystemUpdatedTime(unittest.TestCase):
    def test_capture_from_summary_response(self):
        ctx = FakeContext()
        ctx.page.auto_response = FakeResponse(
            "https://www.edhojmmldkl.com/bapi/growth/v1/friendly/growth-paas/resource/summary/list",
            {
                "code": "000000",
                "data": {
                    "resourceSummaryList": {
                        "pageIndex": 1,
                        "pageSize": 10,
                        "data": [],
                        "total": 4374,
                        "updatedTime": 1786201199000,
                    }
                },
            },
        )
        with mock.patch("src.browser_fetcher._get_browser", return_value=(None, ctx)):
            result = capture_system_updated_time(
                "https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-BABY2",
                "www.edhojmmldkl.com",
            )
        self.assertEqual(result, datetime(2026, 8, 8, 22, 59, 59, tzinfo=BEIJING_TZ))

    def test_url_uses_host_and_main_reward(self):
        ctx = FakeContext()
        with mock.patch("src.browser_fetcher._get_browser", return_value=(None, ctx)):
            capture_system_updated_time(
                "https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-BABY2",
                "www.edhojmmldkl.com",
            )
        self.assertEqual(
            ctx.page.goto_calls,
            ["https://www.edhojmmldkl.com/activity/trading-competition/spot-altcoin-festival-wave-BABY2/Main-Reward"],
        )

    def test_no_updated_time_returns_none(self):
        ctx = FakeContext()
        with mock.patch("src.browser_fetcher._get_browser", return_value=(None, ctx)):
            result = capture_system_updated_time(
                "https://www.binance.com/activity/x",
                "www.edhojmmldkl.com",
            )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
