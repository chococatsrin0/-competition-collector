"""探索脚本：从 Python 探测公告详情 API 的所有可能变体"""
import json
import urllib.request

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}
CODE = "93cc46505d6b46c9be248138b836cb7c"
BASE = "https://www.binance.com"

paths = [
    f"/bapi/apex/v1/public/apex/cms/article/detail/query?articleCode={CODE}&type=2",
    f"/bapi/apex/v1/public/apex/cms/article/detail/query?articleCode={CODE}&type=3",
    f"/bapi/apex/v1/public/apex/cms/article/detail/query?articleCode={CODE}&type=1&lang=zh-CN",
    f"/bapi/apex/v1/public/apex/cms/article/detail/query?code={CODE}&type=1&lang=zh-CN",
    f"/bapi/apex/v1/public/apex/cms/article/detail?articleCode={CODE}",
    f"/bapi/apex/v1/public/apex/cms/article/content/query?articleCode={CODE}",
    "/bapi/apex/v1/public/apex/cms/article/catalog/list/query?type=1&catalogId=93&pageNo=1&pageSize=50",
    "/bapi/composite/v1/public/cms/article/catalog/list/query?type=1&catalogId=93&pageNo=1&pageSize=50",
    "/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=93&pageNo=1&pageSize=50",
    "/bapi/composite/v1/public/cms/article/detail/query?articleCode=" + CODE,
]

for path in paths:
    url = BASE + path
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
        print(f"[{resp.status}] {path} -> {body[:400]}")
    except Exception as e:
        code = getattr(e, "code", "?")
        print(f"[{code}] {path} -> {type(e).__name__}: {e}")
    print()
