"""全局配置：接口地址、关键词、时区等"""

from __future__ import annotations

from datetime import timedelta, timezone

# 北京时间（东八区固定偏移，无夏令时）
BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")

# Binance 站点
BINANCE_BASE_URL = "https://www.binance.com"
SUFFIX_ORIGIN = "binance.com"

# 公告分类：93 = 币安最新活动
ANNOUNCEMENT_CATALOG_ID = 93

# 交易锦标赛识别关键词（标题匹配，兼容中英文）
COMPETITION_KEYWORDS = ["交易量锦标赛", "交易锦标赛", "Trading Tournament", "Trading Competition"]

# 只采集最近 N 天内发布的锦标赛（避免历史活动导致采集时间过长）
RECENT_DAYS = 7
MAX_COMPETITIONS = 20

# 活动参与按钮关键词（公告正文按钮文本）
JOIN_BUTTON_KEYWORDS = [
    "立即参与",
    "立即报名",
    "立即参加",
    "Join Now",
    "Join now",
    "Participate Now",
]

# 主奖池选择规则：资源名称等于「主奖池」（i18nContent.title），
# 兜底使用 uri == "Main-Reward"
MAIN_POOL_TITLES = ["主奖池", "Main Reward", "Main Reward Pool"]
MAIN_POOL_URIS = ["Main-Reward", "Main-Reward1"]

# 接口路径（探索阶段通过浏览器 Network 捕获并逐一验证）
ARTICLE_LIST_API = "/bapi/apex/v1/public/apex/cms/article/list/query"
ARTICLE_DETAIL_API = "/bapi/composite/v1/public/cms/article/detail/query"
LEADERBOARD_API = "/bapi/growth/v1/friendly/growth-paas/resource/summary/list"
PARTICIPANT_API = "/bapi/growth/v1/friendly/growth-paas/resource/summary/participant/list"

# 分页与重试
ANNOUNCEMENT_PAGE_SIZE = 50
LEADERBOARD_PAGE_SIZE = 100
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30

# 请求头（lang 参数决定公告标题语言，zh-CN 返回中文标题）
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "lang": "zh-CN",
    "Content-Type": "application/json",
}

# CSV 输出目录
DATA_ROOT = "data"
LEADERBOARD_DIR = "data/leaderboard"

# CSV 列
CSV_COLUMNS = ["排名", "用户名称", "交易量USD", "采集时间", "系统更新时间"]
