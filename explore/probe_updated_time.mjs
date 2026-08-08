// 探索脚本：在真实浏览器中请求排行榜接口，确认 updatedTime 字段与风控情况
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

const probes = [
  { name: 'MMT 主奖池 pageSize=3', body: { resourceId: 100016875, leaderboardType: 'USER', pageIndex: 1, pageSize: 3 } },
  { name: 'BABY 主奖池 pageSize=3', body: { resourceId: 100016669, leaderboardType: 'USER', pageIndex: 1, pageSize: 3 } },
  { name: 'participant/list', body: { resourceIdList: ['100016875'] } },
]

for (const p of probes) {
  const result = await page.evaluate(
    async ({ body }) => {
      const res = await fetch('https://www.binance.com/bapi/growth/v1/friendly/growth-paas/resource/summary/list', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      })
      return { status: res.status, text: (await res.text()).slice(0, 4000) }
    },
    p
  )
  console.log(`\n=== ${p.name}`)
  console.log(`状态 ${result.status}: ${result.text}`)
}

await browser.close()
