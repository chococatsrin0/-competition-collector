"""入口：定时任务（北京时间每小时第 30 分钟采集）"""

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from src.scheduler import run_scheduler


def main() -> None:
    run_scheduler(run_once=False)


if __name__ == "__main__":
    main()
