"""探索脚本：按用户提供的完整请求头复现，定位 updatedTime 触发条件"""

import json
import time
import urllib.request

USER_HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9",
    "bnc-location": "",
    "bnc-time-zone": "Asia/Shanghai",
    "bnc-uuid": "419ee6bd-203c-40bc-8cce-075fff0828eb",
    "clienttype": "web",
    "content-type": "application/json",
    "cookie": (
        "bnc-uuid=419ee6bd-203c-40bc-8cce-075fff0828eb; "
        "sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219f8a643020445-05815e9aa74ba44-26071951-2073600-19f8a6430211226%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTlmOGE2NDMwMjA0NDUtMDU4MTVlOWFhNzRiYTQ0LTI2MDcxOTUxLTIwNzM2MDAtMTlmOGE2NDMwMjExMjI2In0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%7D; "
        "BNC_FV_KEY=330f2f1784a4a78baedcbb40fefd181d66aac047; "
        "g_state={\"i_l\":0,\"i_ll\":1785070938859,\"i_b\":\"2GlY/6ZhZJlLZVqhot16SX8zh6b/3w9nPJt3MAur/7o\",\"i_e\":{\"enable_itp_optimization\":24},\"i_et\":1785070938859}; "
        "se_gd=lcVVAXQEDTbGBEFUNDgcgZZBUBQ4OBTVVcBdRVkJlRUVAV1NWWcD1; "
        "se_gsd=ZywnLzdxMAAmMCcnNCU7DgAzVVIEAAYDVVhLVFRbW1RSAlNT1; "
        "aws-waf-token=4ffa72ba-0998-4e84-ab2c-8be9565b7129:AQoAlnV5JY2JAAAA:9RpSMf8MwNDTmMlpc7SfGTkx7Wi78OxnEKAMujlg/cXv0+fwD8uMt0NthalmbLCnOoNqF/YkX85qpFwYnuzi/mVIVlILDGRaOJUgMzfltYBQnmIH0+3QsX2ifhtw2OU/zHQ1Hos8uG7o0/I7V0C23UtOF48wqoM7jl3xm5CZMfycvmRf0Q75NHXGBTotnYJ3NAPD1vvctrviwEAix+cTXdhR9iueSPtDGq7IyzDpMj5dZX+3cyZ1Dqsfmrg7NFCBcwIYHuauqSZHgrEw7Q==; "
        "ref=KP94DH21; ref-source=www.edhojmmldkl.com; "
        "registerChannel=GRO-TC-spot-altcoin-festival-wave-BABY2; "
        "BNC_FV_KEY_T=101-Neq2t1yN0WgXA2nPFV89KGIvMB2QAi%2BYskz4KmWztlL%2FmxwCE68CjxiE8%2BDOD4ZPaXAv17FocvICGU5Cuokzmg%3D%3D-%2F2wzqRla2js%2B5bxT5CVjNQ%3D%3D-5e; "
        "BNC_FV_KEY_EXPIRE=1786231288757; theme=dark"
    ),
    "csrftoken": "d41d8cd98f00b204e9800998ecf8427e",
    "device-info": (
        "eyJzY3JlZW5fcmVzb2x1dGlvbiI6IjE5MjAsMTA4MCIsImF2YWlsYWJsZV9zY3JlZW5fcmVzb2x1dGlvbiI6IjE4NzIsMTA4MCIsInN5c3RlbV92ZXJzaW9uIjoiV2luZG93cyAxMCIsImJyYW5kX21vZGVsIjoidW5rbm93biIsInN5c3RlbV9sYW5nIjoiemgtQ04iLCJ0aW1lem9uZSI6IkdNVCswODowMCIsInRpbWV6b25lT2Zmc2V0IjotNDgwLCJ1c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE1MS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwibGlzdF9wbHVnaW4iOiJQREYgVmlld2VyLENocm9tZSBQREYgVmlld2VyLENocm9taXVtIFBERiBWaWV3ZXIsTWljcm9zb2Z0IEVkZ2UgUERGIFZpZXdlcixXZWJLaXQgYnVpbHQtaW4gUERGIiwiY2FudmFzX2NvZGUiOiJhNWI3MmYyMiIsIndlYmdsX3ZlbmRvciI6Ikdvb2dsZSBJbmMuIChNaWNyb3NvZnQpIiwid2ViZ2xfcmVuZGVyZXIiOiJBTkdMRSAoTWljcm9zb2Z0LCBNaWNyb3NvZnQgQmFzaWMgUmVuZGVyIERyaXZlciAoMHgwMDAwMDA4QykgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSkiLCJhdWRpbyI6IjEyNC4wNDM0NzUyNzUxNjA3NCIsInBsYXRmb3JtIjoiV2luMzIiLCJ3ZWJfdGltZXpvbmUiOiJBc2lhL1NoYW5naGFpIiwiZGV2aWNlX25hbWUiOiJDaHJvbWUgVjE1MS4wLjAuMCAoV2luZG93cykiLCJmaW5nZXJwcmludCI6IjJjNTJlZTVlM2Q3MDg3YjRlYjI5ZTI0OTNmZjA0MGZlIiwiZGV2aWNlX2lkIjoiIiwicmVsYXRlZF9kZXZpY2VfaWRzIjoiIn0="
    ),
    "fvideo-id": "330f2f1784a4a78baedcbb40fefd181d66aac047",
    "fvideo-token": "WXxvVBGFjGpV/r8ZPnpKHX30I9ReVVP1Wi/ivehIXaqn5BwxDQDb1TxllvTv3rJe9BLoe2XSciLlALkg7K/W1i1zhBzKFt5COmSojQl+nOUGZwD6p8g/IbU6Qet59I0pCubhEm8oc1WluXPs2L/sdQ/lBJ9gTCnRgNXx14o3xnSnI+4hDmyBpN8d2JmjxFpus=46",
    "lang": "zh-CN",
    "origin": "https://www.edhojmmldkl.com",
    "referer": "https://www.edhojmmldkl.com/zh-CN/activity/trading-competition/spot-altcoin-festival-wave-BABY2/Main-Reward?ref=KP94DH21",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "x-passthrough-token": "",
    "x-trace-id": "30a2eb31-81a3-408f-bc63-fd57a76d155b",
    "x-ui-request-trace": "30a2eb31-81a3-408f-bc63-fd57a76d155b",
}

URL = "https://www.edhojmmldkl.com/bapi/growth/v1/friendly/growth-paas/resource/summary/list"
BODY = {"resourceId": 100016669, "leaderboardType": "USER", "pageIndex": 2, "pageSize": 10}


def call(headers: dict, label: str) -> None:
    req = urllib.request.Request(
        URL,
        data=json.dumps(BODY).encode(),
        headers=headers,
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            obj = json.loads(resp.read().decode("utf-8", "replace"))
        lb = obj.get("data", {}).get("resourceSummaryList") or {}
        keys = sorted(k for k in lb if k != "data")
        rows = lb.get("data") or []
        row_upd = rows[0].get("updatedTime") if rows else None
        print(
            f"[{label}] {resp.status} {time.time()-t0:.1f}s | 键={keys} | "
            f"页面updatedTime={lb.get('updatedTime')} | 行updatedTime={row_upd}"
        )
    except Exception as e:
        print(f"[{label}] 失败 {getattr(e, 'code', '?')}: {type(e).__name__}: {e}")


def variant(**overrides) -> dict:
    h = dict(USER_HEADERS)
    h.update(overrides)
    return h


# 1. 完整请求头复现
call(USER_HEADERS, "完整头")
# 2. 去掉 cookie
call(variant(cookie=""), "无cookie")
# 3. 保留 cookie，去掉 referer
call(variant(referer=""), "无referer")
# 4. 最小头（无 cookie/referer/device-info 等）
MINIMAL_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/json",
    "lang": "zh-CN",
    "origin": "https://www.edhojmmldkl.com",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
}
call(MINIMAL_HEADERS, "最小头")
