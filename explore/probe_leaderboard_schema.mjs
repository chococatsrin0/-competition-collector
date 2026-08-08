// 探索脚本：确认排行榜接口新参数格式，并定位系统更新时间字段
import { createRequire } from 'node:module'
const require = createRequire(
  'C:/Users/choco/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'
)
const { chromium } = require('playwright')

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-blink-features=AutomationControlled'],
})
const context = await browser.newContext({
  userAgent:
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
  locale: 'zh-CN',
  viewport: { width: 1440, height: 900 },
})
const page = await context.newPage()
await page.goto('https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT', {
  waitUntil: 'domcontentloaded',
  timeout: 60000,
})
await page.waitForTimeout(6000)

const url = 'https://www.binance.com/bapi/growth/v1/friendly/growth-paas/resource/summary/list'
const bodies = [
  { name: 'resourceIdList only', body: { resourceIdList: ['100016875'] } },
  { name: 'resourceIdList + page', body: { resourceIdList: ['100016875'], pageIndex: 1, pageSize: 100 } },
  { name: 'resourceIdList + lbType', body: { resourceIdList: ['100016875'], leaderboardType: 'USER', pageIndex: 1, pageSize: 100 } },
  { name: 'resourceId + page (无 leaderboardType)', body: { resourceId: 100016875, pageIndex: 1, pageSize: 100 } },
]

for (const p of bodies) {
  const result = await page.evaluate(
    async ({ body }) => {
      const res = await fetch('https://www.binance.com/bapi/growth/v1/friendly/growth-paas/resource/summary/list', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      })
      return { status: res.status, text: await res.text() }
    },
    p
  )
  console.log(`\n===== ${p.name} -> ${result.status}`)
  if (result.status !== 200) {
    console.log(result.text.slice(0, 300))
    continue
  }
  const obj = JSON.parse(result.text)
  const lb = obj.data?.resourceSummaryList || {}
  const top = {}
  for (const [k, v] of Object.entries(lb)) {
    if (k !== 'data') top[k] = v
  }
  console.log('resourceSummaryList 顶层:', JSON.stringify(top))
  const rows = lb.data || []
  console.log('返回行数:', rows.length)
  if (rows.length) {
    console.log('首行所有字段:', JSON.stringify(rows[0], null, 1).slice(0, 2500))
  }
}

await browser.close()
