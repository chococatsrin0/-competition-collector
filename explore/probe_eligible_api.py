"""探索脚本：在镜像域名上探测返回 eligibleUserCount/updatedTime 的接口"""

import json
import time
import urllib.request

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "lang": "zh-CN",
}
HOST = "www.edhojmmldkl.com"


def post(path: str, body: dict) -> tuple[int, dict, float]:
    url = f"https://{HOST}{path}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace")), time.time() - t0
    except Exception as e:
        return getattr(e, "code", -1), {"error": str(e)}, time.time() - t0


def summarize(obj: dict) -> str:
    try:
        lb = obj["data"]["resourceSummaryList"]
        keys = sorted(k for k in lb if k != "data")
        return f"resourceSummaryList 键: {keys}"
    except Exception:
        return f"data 键: {list(obj.get('data', {}).keys()) if isinstance(obj.get('data'), dict) else type(obj.get('data')).__name__}"


paths_bodies = [
    # 相同接口，payload 变体
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/list", {"resourceId": 100016669, "leaderboardType": "USER", "pageIndex": 1, "pageSize": 10}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/list", {"resourceId": 100016669, "pageIndex": 1, "pageSize": 10}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/list", {"resourceIdList": ["100016669"], "pageIndex": 1, "pageSize": 10}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/list", {"resourceId": 100016669, "leaderboardType": "USER", "pageIndex": 1, "pageSize": 10, "needEligibleUserCount": True}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/list", {"resourceId": 100016669, "leaderboardType": "USER", "pageIndex": 1, "pageSize": 10, "includeSummary": True}),
    # 候选路径
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/eligible", {"resourceId": 100016669}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/eligible/query", {"resourceId": 100016669}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/overview", {"resourceId": 100016669}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/stat", {"resourceId": 100016669}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/summary/info", {"resourceId": 100016669}),
    ("/bapi/growth/v1/friendly/growth-paas/resource/eligible/query", {"resourceId": 100016669}),
    ("/bapi/growth/v1/friendly/growth-paas/activity/summary", {"resourceId": 100016669}),
]

for path, body in paths_bodies:
    status, obj, sec = post(path, body)
    head = json.dumps(obj, ensure_ascii=False)[:400].replace("\n", " ")
    print(f"[{status}] {sec:.1f}s {path} {json.dumps(body, ensure_ascii=False)[:90]}")
    print(f"    {summarize(obj)} | {head}")
    time.sleep(0.5)
