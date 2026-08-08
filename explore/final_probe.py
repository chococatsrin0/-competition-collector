"""探索脚本：最后检查——公告正文是否有 resourceId；候选活动 API"""
import json
import re
import urllib.request

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Content-Type": "application/json",
}
BASE = "https://www.binance.com"
CODE = "93cc46505d6b46c9be248138b836cb7c"


def get(path: str) -> tuple[int, str]:
    req = urllib.request.Request(BASE + path, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", -1), str(e)


def post(path: str, body: dict) -> tuple[int, str]:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers=HEADERS,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", -1), str(e)


# 1. 公告正文是否包含 resourceId 或 Main-Reward
status, text = get(f"/bapi/composite/v1/public/cms/article/detail/query?articleCode={CODE}")
data = json.loads(text).get("data") or {}
body = data.get("body") or ""
print("=== 公告正文关键字检查 ===")
for kw in ["1000168", "Main-Reward", "resourceId", "resource_id"]:
    print(f" {kw}: {kw in body}")

# 2. 候选活动 API
print("\n=== 候选活动 API 探测 ===")
cands = [
    ("GET", "/bapi/growth/v1/friendly/growth-paas/activity-group/queryByCode?code=spot-altcoin-festival-wave-MMT"),
    ("GET", "/bapi/growth/v1/friendly/growth-paas/activity-group/info?code=spot-altcoin-festival-wave-MMT"),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity-group/queryByCode", {"activityGroupCode": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity-group/info", {"activityGroupCode": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity/queryByCode", {"activityGroupCode": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity-group/detail", {"activityGroupCode": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity-group/query", {"activityGroupCode": "spot-altcoin-festival-wave-MMT"}),
    ("GET", "/bapi/growth/v1/friendly/growth-paas/activity-group/query?code=spot-altcoin-festival-wave-MMT"),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/trading-competition-activity/query", {"activityGroupCode": "spot-altcoin-festival-wave-MMT"}),
    ("GET", "/bapi/growth/v1/friendly/growth-paas/trading-competition-activity/query?activityGroupCode=spot-altcoin-festival-wave-MMT"),
]

for item in cands:
    method, path = item[0], item[1]
    body = item[2] if len(item) > 2 else None
    st, resp = get(path) if method == "GET" else post(path, body or {})
    shown = resp[:300].replace("\n", " ")
    print(f"[{method}] {st} {path}\n    {shown}\n")

# 3. 活动页 WAF 拦截确定性检查
print("=== 活动页 urllib 状态 ===")
for i in range(3):
    st, resp = get("/activity/trading-competition/spot-altcoin-festival-wave-MMT")
    head = resp[:80].replace("\n", " ")
    print(f" 第{i+1}次: {st}, 长度 {len(resp)}, 开头: {head}")
