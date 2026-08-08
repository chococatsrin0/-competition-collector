"""探索脚本：处理单个比赛并输出各阶段耗时"""

import sys
import time
from datetime import datetime

from src.config import BEIJING_TZ
from src.discover import Competition


def main() -> None:
    code = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else code
    comp = Competition(title=title, article_id=0, article_code=code, release_date=None, announcement_url="")

    from src.activity import resolve_activity_url

    t0 = time.time()
    url = resolve_activity_url(comp)
    print(f"[{time.time()-t0:.1f}s] 活动URL: {url}", flush=True)

    from src.resource import extract_activity_meta

    t1 = time.time()
    meta = extract_activity_meta(url)
    print(f"[{time.time()-t1:.1f}s] resourceId={meta.main_resource_id} token={meta.token}", flush=True)

    from src.leaderboard import collect_leaderboard

    t2 = time.time()
    rows = collect_leaderboard(meta.main_resource_id, collected_at=datetime.now(tz=BEIJING_TZ))
    print(f"[{time.time()-t2:.1f}s] 采集 {len(rows)} 行", flush=True)

    from src.csv_writer import write_leaderboard_csv

    t3 = time.time()
    path = write_leaderboard_csv(meta.token or "UNKNOWN", rows)
    print(f"[{time.time()-t3:.1f}s] CSV: {path}", flush=True)


if __name__ == "__main__":
    main()
