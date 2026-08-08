"""入口：执行一次完整采集"""

import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from src.collector import run_collection
from src.config import RECENT_DAYS


def main() -> None:
    parser = argparse.ArgumentParser(description="币安交易锦标赛排行榜采集（执行一次）")
    parser.add_argument("--no-catalog", action="store_true", help="不限定公告分类（全量扫描）")
    parser.add_argument("--days", type=int, default=RECENT_DAYS, help="只采集最近 N 天内发布的锦标赛")
    args = parser.parse_args()
    paths = run_collection(catalog_id=None if args.no_catalog else 93, max_age_days=args.days)
    if not paths:
        raise SystemExit("本次未生成任何 CSV，请检查日志")
    print("生成 CSV:")
    for p in paths:
        print(" -", p)


if __name__ == "__main__":
    main()
