"""第一阶段：自动发现最新交易锦标赛"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from .config import (
    ANNOUNCEMENT_CATALOG_ID,
    ANNOUNCEMENT_PAGE_SIZE,
    ARTICLE_LIST_API,
    BINANCE_BASE_URL,
    COMPETITION_KEYWORDS,
    MAX_COMPETITIONS,
    RECENT_DAYS,
)
from .http_client import get_json


@dataclass
class Competition:
    """一个交易锦标赛公告"""

    title: str
    article_id: int
    article_code: str
    release_date: datetime | None
    announcement_url: str

    @property
    def token(self) -> str | None:
        """从标题中猜测币种 Token（仅作展示，最终以活动页 rewardPoolSetting.unit 为准）"""
        m = re.search(r"([A-Z][A-Z0-9]{1,10})(?:/|$|\s|奖池|Token)", self.title)
        return m.group(1) if m else None


def _parse_article_list(data: dict) -> list[dict]:
    """从接口响应中提取文章列表（兼容有/无 catalogId 两种结构）"""
    catalogs = data.get("data", {}).get("catalogs") or []
    articles: list[dict] = []
    for cat in catalogs:
        articles.extend(cat.get("articles") or [])
    return articles


def fetch_announcements(
    catalog_id: int | None = ANNOUNCEMENT_CATALOG_ID,
    page_no: int = 1,
    page_size: int = ANNOUNCEMENT_PAGE_SIZE,
) -> list[Competition]:
    """请求公告列表接口，返回全部公告"""
    params = {"type": 1, "pageNo": page_no, "pageSize": page_size}
    if catalog_id is not None:
        params["catalogId"] = catalog_id
    data = get_json(ARTICLE_LIST_API, params=params)
    result: list[Competition] = []
    for a in _parse_article_list(data):
        release_date = None
        if a.get("releaseDate"):
            release_date = datetime.fromtimestamp(a["releaseDate"] / 1000)
        result.append(
            Competition(
                title=a.get("title", ""),
                article_id=a.get("id"),
                article_code=a.get("code", ""),
                release_date=release_date,
                announcement_url=f"{BINANCE_BASE_URL}/zh-CN/support/announcement/detail/{a.get('code', '')}",
            )
        )
    return result


def filter_competitions(announcements: list[Competition], keywords: list[str] | None = None) -> list[Competition]:
    """按关键词过滤交易锦标赛公告"""
    kws = keywords or COMPETITION_KEYWORDS
    return [a for a in announcements if any(k.lower() in a.title.lower() for k in kws)]


def discover_competitions(
    catalog_id: int | None = ANNOUNCEMENT_CATALOG_ID,
    max_age_days: int | None = RECENT_DAYS,
    max_competitions: int = MAX_COMPETITIONS,
) -> list[Competition]:
    """一键发现：请求公告列表并过滤出最近发布的交易锦标赛"""
    announcements = fetch_announcements(catalog_id=catalog_id)
    comps = filter_competitions(announcements)
    if max_age_days is not None:
        cutoff = datetime.now().astimezone() - timedelta(days=max_age_days)
        comps = [c for c in comps if c.release_date is None or c.release_date.astimezone() >= cutoff]
    return comps[:max_competitions]
