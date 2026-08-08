"""探索脚本：确认公告列表 API 的中文标题参数"""
import json
import urllib.request

BASE = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query"


def probe(label, extra_headers=None, query=""):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if extra_headers:
        headers.update(extra_headers)
    url = BASE + "?type=1&pageNo=1&pageSize=3&catalogId=93" + query
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", "replace")
        data = json.loads(text)
        arts = data["data"]["catalogs"][0]["articles"]
        print(f"[{label}]")
        for a in arts:
            print("  -", a["title"])
    except Exception as e:
        print(f"[{label}] 失败: {e}")
    print()


probe("默认(仅 UA+Accept-Language)")
probe("header lang=zh-CN", {"lang": "zh-CN"})
probe("query &lang=zh-CN", query="&lang=zh-CN")
probe("cookie bnc-lang=zh-CN", {"Cookie": "bnc-lang=zh-CN; bnc-locale=zh-CN"})
probe("header bnc-lang=zh-CN", {"bnc-lang": "zh-CN", "bnc-locale": "zh-CN"})
