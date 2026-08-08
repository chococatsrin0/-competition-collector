"""可选浏览器抓取：用于绕过 AWS WAF JS 挑战（依赖 playwright）"""

from __future__ import annotations

import atexit
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from .http_client import WafChallengeError

_playwright = None
_browser = None
_context = None


def _get_browser():
    """复用浏览器实例，避免每个页面都重新启动 Chromium"""
    global _playwright, _browser, _context
    if _browser is not None:
        return _browser, _context
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise WafChallengeError(
            "页面被 AWS WAF 拦截且未安装 playwright。"
            "请执行 pip install playwright && playwright install chromium"
        ) from e

    _playwright = sync_playwright().start()
    _browser = _playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
    )
    _context = _browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        locale="zh-CN",
        viewport={"width": 1440, "height": 900},
    )
    atexit.register(close_browser)
    return _browser, _context


def close_browser() -> None:
    """关闭浏览器（进程退出时自动调用）"""
    global _playwright, _browser, _context
    if _context is not None:
        try:
            _context.close()
        except Exception:
            pass
        _context = None
    if _browser is not None:
        try:
            _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright is not None:
        try:
            _playwright.stop()
        except Exception:
            pass
        _playwright = None


def fetch_html_via_browser(url: str, wait_ms: int = 8000) -> str:
    """用 Playwright 打开页面并返回渲染后的 HTML"""
    last_html = ""
    for attempt in range(3):
        _, context = _get_browser()
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(wait_ms)
            last_html = page.content()
        finally:
            page.close()
        # WAF 挑战页或空页时重试（重置上下文以清除异常 cookie 状态）
        if "__APP_DATA" in last_html or len(last_html) > 20000:
            return last_html
        close_browser()
    return last_html


def capture_system_updated_time(activity_url: str, host: str) -> datetime | None:
    """在真实页面请求中捕获排行榜接口的页面级 updatedTime。

    官方域名不返回该字段，只有部分网关（第三方镜像）在页面请求时返回。
    通过打开活动页主奖池子页面并监听 resource/summary/list 响应获得。
    """
    parts = urlsplit(activity_url)
    url = urlunsplit((parts.scheme, host, parts.path.rstrip("/") + "/Main-Reward", "", ""))

    _, context = _get_browser()
    page = context.new_page()
    updated: datetime | None = None

    def on_response(res) -> None:
        nonlocal updated
        if "resource/summary/list" not in res.url:
            return
        try:
            obj = res.json()
            lb = obj.get("data", {}).get("resourceSummaryList") or {}
            ms = lb.get("updatedTime")
            if ms:
                from .config import BEIJING_TZ

                updated = datetime.fromtimestamp(int(ms) / 1000, tz=BEIJING_TZ)
        except Exception:
            pass

    page.on("response", on_response)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        if updated is None:
            # 页面未自动请求时，点击主奖池页签触发
            try:
                page.evaluate(
                    """() => {
                        const els = [...document.querySelectorAll('button, [role="tab"], a, div, span')]
                        const el = els.find((e) =>
                            (e.textContent || '').trim().startsWith('主奖池') && e.offsetParent !== null)
                        if (el) el.click()
                    }"""
                )
                page.wait_for_timeout(4000)
            except Exception:
                pass
    finally:
        page.close()
    return updated
