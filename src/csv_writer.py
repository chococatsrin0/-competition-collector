"""CSV 输出：data/leaderboard/{TOKEN}/YYYYMMDDHHMM.csv"""

from __future__ import annotations

import csv
import os
from datetime import datetime

from .config import BEIJING_TZ, CSV_COLUMNS, LEADERBOARD_DIR
from .leaderboard import LeaderboardRow


def build_csv_path(token: str, collected_at: datetime) -> str:
    """按北京时间生成 CSV 路径"""
    ts = collected_at.astimezone(BEIJING_TZ).strftime("%Y%m%d%H%M")
    return os.path.normpath(os.path.join(LEADERBOARD_DIR, token.upper(), f"{ts}.csv"))


def write_leaderboard_csv(token: str, rows: list[LeaderboardRow], collected_at: datetime | None = None) -> str:
    """写排行榜 CSV（utf-8-sig，Excel 可直接打开）"""
    collected_at = collected_at or datetime.now(tz=BEIJING_TZ)
    path = build_csv_path(token, collected_at)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_dict())
    return path
