"""定时任务：北京时间每小时第 30 分钟采集一次"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from .config import BEIJING_TZ

logger = logging.getLogger(__name__)


def next_run(now_utc: datetime, minute: int = 30) -> datetime:
    """计算下一个运行时刻（北京时间 HH:30），返回 UTC 时间"""
    now = now_utc.astimezone(BEIJING_TZ)
    target = now.replace(minute=minute, second=0, microsecond=0)
    if now >= target:
        target += timedelta(hours=1)
    return target.astimezone(now_utc.tzinfo or BEIJING_TZ)


def sleep_until(target_utc: datetime) -> None:
    """睡眠直到目标时刻"""
    delta = (target_utc - datetime.now(target_utc.tzinfo)).total_seconds()
    if delta > 0:
        logger.info("距下次采集还有 %.1f 分钟", delta / 60)
        time.sleep(delta)


def run_scheduler(run_once: bool = False, minute: int = 30) -> None:
    """定时循环：到点执行 run_collection"""
    from .collector import run_collection

    while True:
        target = next_run(datetime.now(tz=BEIJING_TZ), minute=minute)
        sleep_until(target)
        logger.info("开始定时采集（北京时间 %s）", target.astimezone(BEIJING_TZ))
        try:
            paths = run_collection()
            logger.info("本次采集完成，共 %d 个 CSV", len(paths))
        except Exception:
            logger.exception("定时采集失败")
        if run_once:
            break
