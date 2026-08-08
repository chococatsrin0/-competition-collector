"""探索脚本：验证纯 Python 能否直接访问已发现的接口（无浏览器）"""
import json
import re
import ssl
import urllib.request

BASE = "https://www.binance.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Content-Type": "application/json",
}


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def post(url: str, body: dict) -> str:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=HEADERS,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


print("=== 1. 公告列表 API ===")
list_url = BASE + "/bapi/apex/v1/public/apex/cms/article/list/query?type=1&pageNo=1&pageSize=5&catalogId=93"
list_text = get(list_url)
list_json = json.loads(list_text)
articles = list_json["data"]["catalogs"][0]["articles"]
print("code:", list_json.get("code"), "| 文章数:", len(articles))
for a in articles[:5]:
    print(" -", a["title"], "|", a["code"], "|", a["releaseDate"])

print("\n=== 2. 公告详情页 HTML ===")
detail_url = BASE + "/zh-CN/support/announcement/detail/93cc46505d6b46c9be248138b836cb7c"
detail_html = get(detail_url)
print("HTML 长度:", len(detail_html))
links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]{0,40})</a>', detail_html)
for href, text in links:
    if "activity" in href or any(k in text for k in ["立即参与", "立即报名", "Join Now", "立即参加"]):
        print(f" - [{text}] -> {href}")

print("\n=== 3. 活动页 __APP_DATA ===")
act_url = BASE + "/activity/trading-competition/spot-altcoin-festival-wave-MMT"
act_html = get(act_url)
print("HTML 长度:", len(act_html))
m = re.search(r'<script id="__APP_DATA"[^>]*>([\s\S]*?)</script>', act_html)
if m:
    app_data = json.loads(m.group(1))
    routes = app_data["appState"]["loader"]["dataByRouteId"]
    for k, v in routes.items():
        if isinstance(v, dict) and v.get("activityGroup"):
            print("找到活动数据:", k)
            for act in v["activities"]:
                print(" - id:", act["id"], "| uri:", act["globalContent"]["uri"], "| title:", act["i18nContent"]["title"])
            break
else:
    print("未找到 __APP_DATA")

print("\n=== 4. 排行榜 API ===")
lb_url = BASE + "/bapi/growth/v1/friendly/growth-paas/resource/summary/list"
lb_text = post(lb_url, {"resourceId": 100016875, "leaderboardType": "USER", "pageIndex": 1, "pageSize": 100})
lb_json = json.loads(lb_text)
lb_data = lb_json["data"]["resourceSummaryList"]
print("code:", lb_json.get("code"), "| 返回条数:", len(lb_data.get("data", [])))
print("分页字段:", {k: v for k, v in lb_data.items() if k != "data"})
row = lb_data["data"][0]
print("首行:", json.dumps({k: row.get(k) for k in ["sequence", "nickName", "tradingVolume", "updatedTime", "resourceId"]}, ensure_ascii=False))

print("\n=== 5. 主奖池 resourceId 探测（participant list） ===")
part_url = BASE + "/bapi/growth/v1/friendly/growth-paas/resource/summary/participant/list"
part_text = post(part_url, {"resourceIdList": ["100016874", "100016875", "100016877", "100016879"]})
print(part_text[:800])
