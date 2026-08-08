# Binance 交易锦标赛数据自动采集系统

自动发现币安最新交易锦标赛公告，解析活动页面获取主奖池 `resourceId`，采集排行榜数据，并按北京时间每小时第 30 分钟生成 CSV。

## 功能

- **自动发现**：从币安公告分类「币安最新活动」（catalogId=93）发现最新交易锦标赛（关键词：交易量锦标赛 / Trading Tournament / Trading Competition）。
- **活动 URL**：解析公告正文，找到「立即参与 / Join Now」按钮的真实活动链接。
- **主奖池 resourceId**：通过浏览器抓取活动页（AWS WAF 保护），从 `__APP_DATA` 中按「资源名称 = 主奖池」规则选出主奖池资源。
- **排行榜采集**：调用真实排行榜接口，分页（并发）采集完整排名、用户名称、交易量 USD。
- **自动停止**：每次定时运行都会重新发现最新锦标赛并纳入采集；活动结束时间 + 4 小时后自动停止采集该活动（宽限期在 `src/config.py` 的 `COLLECT_GRACE_HOURS` 调整，`None` 表示不限制）。
- **CSV 输出**：`data/leaderboard/{TOKEN}/YYYYMMDDHHMM.csv`，列：`排名,用户名称,交易量USD,采集时间,系统更新时间`。
- **定时任务**：北京时间（东八区）每小时第 30 分钟自动采集。

## 环境

- Python 3.9+（推荐使用项目指定 conda 环境：`D:\soft\conda\python.exe`）
- 依赖：`playwright`（已包含 Chromium 浏览器）

```powershell
D:\soft\conda\python.exe -m pip install -r requirements.txt
D:\soft\conda\python.exe -m playwright install chromium
```

## 使用

### 执行一次采集

```powershell
D:\soft\conda\python.exe run_collector.py
```

可选参数：

- `--days N`：只采集最近 N 天内发布的锦标赛（默认 7 天，避免历史活动导致采集时间过长）
- `--no-catalog`：不限定「币安最新活动」分类，全量扫描公告

### 定时任务（每小时第 30 分钟）

```powershell
D:\soft\conda\python.exe run_scheduler.py
```

程序会持续运行，在每小时第 30 分钟（北京时间）自动执行一次完整采集。

## 项目结构

```text
src/
  config.py        # 接口地址、关键词、时区等配置
  http_client.py   # urllib 封装：重试、WAF 挑战检测
  browser_fetcher.py  # Playwright 抓取被 WAF 保护的页面（浏览器复用）
  discover.py      # 阶段1：发现交易锦标赛
  activity.py      # 阶段2：公告正文 -> 活动 URL
  resource.py      # 阶段3：活动页 -> 主奖池 resourceId 与元数据
  leaderboard.py   # 阶段4：排行榜采集（分页并发）
  csv_writer.py    # CSV 输出
  collector.py     # 主流程编排
  scheduler.py     # 定时任务（北京时间 :30）
tests/             # 单元测试 + 联网集成测试（TC001-TC004）
explore/           # 浏览器探索脚本与网络请求证据
reports/           # 验证报告
data/leaderboard/  # 生成的 CSV
```

## 测试

```powershell
# 单元测试（离线）
D:\soft\conda\python.exe -m unittest discover -s tests -p "test_*.py"

# 联网集成测试（验收标准 TC001-TC004）
$env:BINANCE_LIVE_TEST='1'
D:\soft\conda\python.exe -m unittest tests.test_live -v
```

## 说明与限制

- 币安公告/活动页面受 AWS WAF JS 挑战保护，纯 HTTP 客户端拿不到活动页 HTML，因此活动页抓取依赖 Playwright（真实 Chromium）。
- 公告列表、公告详情、排行榜均为纯 HTTP 接口，无需浏览器。
- 「主奖池」选择规则：`i18nContent.title == 主奖池`，兜底 `globalContent.uri == Main-Reward`。
- 排行榜接口按页返回，`total` 字段可能持续增长（活动进行中），每次采集以当时的 `total` 为准。
