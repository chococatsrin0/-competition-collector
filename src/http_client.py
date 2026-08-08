"""HTTP 客户端：urllib 封装 + 重试 + WAF 挑战检测"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import BINANCE_BASE_URL, HEADERS, MAX_RETRIES, REQUEST_TIMEOUT


class ApiError(RuntimeError):
    """接口请求失败"""


class WafChallengeError(ApiError):
    """页面被 AWS WAF JS 挑战拦截，需要真实浏览器抓取"""


def _is_waf_challenge(status: int, headers: dict, body: str) -> bool:
    """识别 AWS WAF challenge 响应"""
    action = headers.get("x-amzn-waf-action", "")
    if action == "challenge" or status == 202 and "awsWaf" in body:
        return True
    return False


def _request(method: str, url: str, body: dict | None = None, headers: dict | None = None) -> tuple[int, str, dict]:
    """发起请求并返回 (状态码, 文本, 响应头)"""
    hdrs = dict(HEADERS)
    if headers:
        hdrs.update(headers)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            text = resp.read().decode("utf-8", "replace")
            return resp.status, text, dict(resp.headers)
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        return e.code, text, dict(e.headers)


def get_json(path_or_url: str, params: dict | None = None, headers: dict | None = None) -> dict:
    """GET JSON 接口"""
    url = _build_url(path_or_url, params)
    last_err: Exception | None = None
    for _ in range(MAX_RETRIES):
        try:
            status, text, resp_headers = _request("GET", url, headers=headers)
            if _is_waf_challenge(status, resp_headers, text):
                raise WafChallengeError(f"页面被 WAF 拦截: {url}")
            data = json.loads(text)
            if data.get("code") not in (None, "000000"):
                raise ApiError(f"接口返回错误码 {data.get('code')}: {data.get('message')}")
            return data
        except (urllib.error.URLError, json.JSONDecodeError, ApiError) as e:
            last_err = e
            time.sleep(1)
    raise ApiError(f"GET 请求失败: {url} -> {last_err}")


def post_json(path_or_url: str, body: dict, headers: dict | None = None) -> dict:
    """POST JSON 接口"""
    url = _build_url(path_or_url)
    last_err: Exception | None = None
    for _ in range(MAX_RETRIES):
        try:
            status, text, resp_headers = _request("POST", url, body, headers)
            if _is_waf_challenge(status, resp_headers, text):
                raise WafChallengeError(f"页面被 WAF 拦截: {url}")
            data = json.loads(text)
            if data.get("code") not in (None, "000000"):
                raise ApiError(f"接口返回错误码 {data.get('code')}: {data.get('message')}")
            return data
        except (urllib.error.URLError, json.JSONDecodeError, ApiError) as e:
            last_err = e
            time.sleep(1)
    raise ApiError(f"POST 请求失败: {url} -> {last_err}")


def fetch_html(path_or_url: str) -> str:
    """抓取页面 HTML；若被 WAF 拦截则尝试浏览器抓取"""
    url = _build_url(path_or_url)
    status, text, resp_headers = _request("GET", url)
    if _is_waf_challenge(status, resp_headers, text):
        return _fetch_via_browser(url)
    if not text:
        raise ApiError(f"页面返回空内容: {url}")
    return text


def _fetch_via_browser(url: str) -> str:
    """使用 Playwright（如已安装）抓取被 WAF 保护的页面"""
    from .browser_fetcher import fetch_html_via_browser

    return fetch_html_via_browser(url)


def _build_url(path_or_url: str, params: dict | None = None) -> str:
    if path_or_url.startswith("http"):
        url = path_or_url
    else:
        url = BINANCE_BASE_URL + path_or_url
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    return url
