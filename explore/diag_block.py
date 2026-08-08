"""探索脚本：诊断详情页 HTML 被拦截的原因"""
import urllib.request
import urllib.error

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

url = "https://www.binance.com/zh-CN/support/announcement/detail/93cc46505d6b46c9be248138b836cb7c"
try:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        print("状态:", resp.status)
        print("最终 URL:", resp.geturl())
        print("头:", dict(resp.headers))
        print("长度:", len(raw))
        print("内容前 300:", raw[:300])
except urllib.error.HTTPError as e:
    raw = e.read()
    print("HTTPError:", e.code)
    print("头:", dict(e.headers))
    print("长度:", len(raw))
    print("内容前 500:", raw[:500])
except Exception as e:
    print("异常:", type(e).__name__, e)
