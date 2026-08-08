"""探索脚本：解析公告详情正文，找活动链接；并探测活动资源元数据 API"""
import json
import urllib.request
import urllib.parse

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
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", -1), str(e)


def post(path: str, body: dict) -> tuple[int, str]:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode("utf-8"),
        headers=HEADERS,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", -1), str(e)


# 1. 公告正文里找活动链接
status, text = get(f"/bapi/composite/v1/public/cms/article/detail/query?articleCode={CODE}")
print(f"=== 公告详情: {status}")
detail = json.loads(text)
data = detail.get("data") or {}
print("标题:", data.get("title"))
body = data.get("body") or ""

links = []
if body:
    try:
        body_json = json.loads(body)

        def walk(node):
            if isinstance(node, dict):
                node_type = node.get("node")
                if node_type == "link" or (node_type == "element" and node.get("tag") == "a"):
                    links.append((node.get("text"), node.get("href"), node.get("url")))
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(body_json)
    except Exception as e:
        print("正文解析失败:", e)

print("正文中的链接:")
for t, href, url in links:
    print(" -", t, "|", href or url)

# 找「立即参与」相关文本
print("\n正文中包含关键字的片段:")
for kw in ["立即参与", "立即报名", "立即参加", "Join Now", "活动页面", "任务页面"]:
    idx = body.find(kw)
    if idx > -1:
        print(f" [{kw}] ...{body[max(0, idx-200):idx+300]}...")

# 2. 探测活动资源元数据 API
print("\n=== 活动资源元数据 API 探测 ===")
probes = [
    ("GET", "/bapi/growth/v1/friendly/growth-paas/activity-group/detail/query?code=spot-altcoin-festival-wave-MMT", None),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity-group/detail/query", {"code": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity-group/query", {"code": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/activity/query", {"code": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/resource/detail/query", {"code": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/resource/query", {"resourceCode": "spot-altcoin-festival-wave-MMT"}),
    ("POST", "/bapi/growth/v1/friendly/growth-paas/resource/detail/query", {"resourceCode": "spot-altcoin-festival-wave-MMT"}),
]

for method, path, body in probes:
    if method == "GET":
        st, resp_text = get(path)
    else:
        st, resp_text = post(path, body or {})
    print(f"[{method}] {st} {path}\n   {resp_text[:500]}\n")
