"""第三阶段：解析活动页面，获取主奖池 resourceId 与活动元数据"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime

from .config import MAIN_POOL_TITLES, MAIN_POOL_URIS
from .http_client import ApiError, fetch_html


@dataclass
class ActivityMeta:
    """活动元数据"""

    group_id: int
    group_code: str
    main_resource_id: int
    token: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    prize_tiers: list[dict] = field(default_factory=list)
    trading_pairs: list[str] = field(default_factory=list)
    threshold: float | None = None
    activity_url: str | None = None


def parse_app_data(html: str) -> dict | None:
    """从活动页 HTML 提取 __APP_DATA JSON"""
    m = re.search(r'<script id="__APP_DATA"[^>]*>([\s\S]*?)</script>', html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ApiError(f"__APP_DATA 解析失败: {e}") from e


def find_activity_root(app_data: dict) -> dict | None:
    """定位包含 activityGroup 与 activities 的节点"""

    def walk(node):
        if isinstance(node, dict):
            if "activityGroup" in node and "activities" in node:
                return node
            for v in node.values():
                r = walk(v)
                if r:
                    return r
        elif isinstance(node, list):
            for v in node:
                r = walk(v)
                if r:
                    return r
        return None

    return walk(app_data)


def _parse_cn_datetime(text: str) -> datetime | None:
    """解析「2026年08月06日18:00」这类时间文本为北京时间 datetime"""
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})", text or "")
    if not m:
        return None
    from .config import BEIJING_TZ

    y, mo, d, h, mi = (int(x) for x in m.groups())
    try:
        return datetime(y, mo, d, h, mi, tzinfo=BEIJING_TZ)
    except ValueError:
        return None


def select_main_pool(activities: list[dict]) -> dict | None:
    """选择主奖池资源：名称等于「主奖池」，兜底 uri 为 Main-Reward"""
    for act in activities:
        title = ((act.get("i18nContent") or {}).get("title") or "").strip()
        uri = ((act.get("globalContent") or {}).get("uri") or "").strip()
        if title in MAIN_POOL_TITLES or uri in MAIN_POOL_URIS:
            return act
    return None


def extract_activity_meta(activity_url: str) -> ActivityMeta:
    """抓取活动页并解析主奖池资源信息"""
    html = fetch_html(activity_url)
    app_data = parse_app_data(html)
    if not app_data:
        raise ApiError(f"活动页未找到 __APP_DATA: {activity_url}")
    root = find_activity_root(app_data)
    if not root:
        raise ApiError(f"活动页数据中未找到 activityGroup/activities: {activity_url}")

    group = root["activityGroup"]
    activities = root.get("activities") or []
    main = select_main_pool(activities)
    if not main:
        raise ApiError(f"未找到主奖池资源: {activity_url}")

    gcontent = main.get("globalContent") or {}
    icontent = main.get("i18nContent") or {}
    pool = gcontent.get("rewardPoolSetting") or {}
    ranking = gcontent.get("rankingSetting") or {}

    # 时间：优先 timelineContent 文本，兜底 ms 时间戳
    start_time = end_time = None
    for item in (icontent.get("timelineContent") or {}).get("timelineList") or []:
        title = (item.get("title") or "").strip()
        dt = _parse_cn_datetime(item.get("subtitle") or "")
        if "开始" in title:
            start_time = dt
        elif "结束" in title:
            end_time = dt
    if start_time is None and main.get("publishedTime"):
        from .config import BEIJING_TZ

        start_time = datetime.fromtimestamp(main["publishedTime"] / 1000, tz=BEIJING_TZ)
    if end_time is None and main.get("taskExpiredTime"):
        from .config import BEIJING_TZ

        end_time = datetime.fromtimestamp(main["taskExpiredTime"] / 1000, tz=BEIJING_TZ)

    return ActivityMeta(
        group_id=group.get("id"),
        group_code=group.get("code"),
        main_resource_id=main.get("id"),
        token=(pool.get("unit") or "").strip() or None,
        start_time=start_time,
        end_time=end_time,
        prize_tiers=ranking.get("rankingPrizeList") or [],
        trading_pairs=gcontent.get("includeSpotTradingPairList") or [],
        threshold=gcontent.get("leaderboardQualifyThresholds"),
        activity_url=activity_url,
    )
