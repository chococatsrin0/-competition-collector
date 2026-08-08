"""第四阶段：采集排行榜数据"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from .config import BEIJING_TZ, LEADERBOARD_API, LEADERBOARD_PAGE_SIZE
from .http_client import post_json

logger = logging.getLogger(__name__)


@dataclass
class LeaderboardRow:
    """排行榜一行"""

    rank: int
    user_name: str
    trading_volume_usd: float
    collected_at: datetime
    system_updated_at: datetime | None

    def to_csv_dict(self) -> dict:
        return {
            "排名": self.rank,
            "用户名称": self.user_name,
            "交易量USD": f"{self.trading_volume_usd:.2f}",
            "采集时间": _iso(self.collected_at),
            "系统更新时间": _iso(self.system_updated_at) if self.system_updated_at else _iso(self.collected_at),
        }


def _iso(dt: datetime) -> str:
    return dt.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S %z")


def fetch_leaderboard_page(resource_id: int, page_index: int = 1, page_size: int = LEADERBOARD_PAGE_SIZE) -> dict:
    """请求一页排行榜"""
    data = post_json(
        LEADERBOARD_API,
        {
            "resourceId": resource_id,
            "leaderboardType": "USER",
            "pageIndex": page_index,
            "pageSize": page_size,
        },
    )
    return data.get("data", {}).get("resourceSummaryList") or {}


def collect_leaderboard(
    resource_id: int,
    collected_at: datetime | None = None,
    max_pages: int = 1000,
    workers: int = 4,
) -> list[LeaderboardRow]:
    """分页采集完整排行榜（并发拉取，按页序合并）"""
    collected_at = collected_at or datetime.now(tz=BEIJING_TZ)
    first = fetch_leaderboard_page(resource_id, page_index=1)
    items = first.get("data") or []
    if not items:
        return []
    total = int(first.get("total") or 0)
    page_size = first.get("pageSize") or LEADERBOARD_PAGE_SIZE
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    total_pages = min(total_pages, max_pages)

    def fetch_one(page_index: int) -> list[dict]:
        page_data = fetch_leaderboard_page(resource_id, page_index=page_index, page_size=page_size)
        return page_data.get("data") or []

    page_results: dict[int, list[dict]] = {1: items}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_one, p): p for p in range(2, total_pages + 1)}
        for idx, fut in enumerate(futures, start=1):
            p = futures[fut]
            page_results[p] = fut.result()
            if idx % 20 == 0:
                logger.info("  排行榜采集进度: 已完成 %d/%d 页（共 %d 行）", idx, total_pages, total)

    rows: list[LeaderboardRow] = []
    for page in range(1, total_pages + 1):
        for item in page_results.get(page, []):
            rows.append(
                LeaderboardRow(
                    rank=item.get("sequence"),
                    user_name=item.get("nickName") or item.get("userId") or "",
                    trading_volume_usd=float(item.get("tradingVolume") or 0),
                    collected_at=collected_at,
                    system_updated_at=None,
                )
            )
    logger.info("  排行榜采集完成: 共 %d 行", len(rows))
    return rows
