"""主流程编排：发现 -> 活动URL -> 主奖池resourceId -> 采集排行榜 -> CSV"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from .activity import resolve_activity_url
from .config import BEIJING_TZ, COLLECT_GRACE_HOURS, RECENT_DAYS
from .csv_writer import write_leaderboard_csv
from .discover import Competition, discover_competitions
from .leaderboard import collect_leaderboard
from .resource import ActivityMeta, extract_activity_meta

logger = logging.getLogger(__name__)


def is_expired(meta: ActivityMeta, collected_at: datetime) -> bool:
    """判断活动是否已结束超过宽限期（默认结束时间 + 4 小时）"""
    if meta.end_time is None or COLLECT_GRACE_HOURS is None:
        return False
    deadline = meta.end_time + timedelta(hours=COLLECT_GRACE_HOURS)
    return collected_at > deadline


def collect_one(competition: Competition, collected_at: datetime | None = None) -> str | None:
    """处理单个交易锦标赛：解析活动 URL -> resourceId -> 采集 -> CSV"""
    collected_at = collected_at or datetime.now(tz=BEIJING_TZ)
    logger.info("处理公告: %s", competition.title)

    activity_url = resolve_activity_url(competition)
    if not activity_url:
        logger.warning("未找到活动链接: %s", competition.title)
        return None
    logger.info("活动 URL: %s", activity_url)

    meta = extract_activity_meta(activity_url)
    logger.info(
        "主奖池 resourceId=%s token=%s 开始=%s 结束=%s",
        meta.main_resource_id,
        meta.token,
        meta.start_time,
        meta.end_time,
    )
    if is_expired(meta, collected_at):
        logger.warning(
            "活动已结束超过 %s 小时，跳过采集: %s（结束时间 %s）",
            COLLECT_GRACE_HOURS,
            competition.title,
            meta.end_time,
        )
        return None

    rows = collect_leaderboard(meta.main_resource_id, collected_at=collected_at)
    logger.info("采集到 %d 条排行榜数据", len(rows))
    if not rows:
        logger.warning("排行榜为空: %s", competition.title)
        return None

    path = write_leaderboard_csv(meta.token or "UNKNOWN", rows, collected_at=collected_at)
    logger.info("CSV 已写出: %s", path)
    return path


def run_collection(catalog_id: int | None = None, max_age_days: int | None = RECENT_DAYS) -> list[str]:
    """完整采集流程，返回所有 CSV 路径"""
    competitions = discover_competitions(catalog_id=catalog_id, max_age_days=max_age_days)
    logger.info("发现 %d 个交易锦标赛", len(competitions))
    paths: list[str] = []
    for comp in competitions:
        try:
            path = collect_one(comp)
            if path:
                paths.append(path)
        except Exception as e:  # 单个比赛失败不阻塞整体
            logger.exception("处理失败: %s -> %s", comp.title, e)
    return paths
