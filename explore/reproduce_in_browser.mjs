// 探索脚本：在真实浏览器中打开 Main-Reward 子页面，再调用接口复现 updatedTime
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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
  locale: 'zh-CN',
  viewport: { width: 1920, height: 1080 },
})
const page = await context.newPage()

// 打开主奖池子页面（与用户 referer 一致）
await page.goto(
  'https://www.edhojmmldkl.com/zh-CN/activity/trading-competition/spot-altcoin-festival-wave-BABY2/Main-Reward',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(8000)

const body = { resourceId: 100016669, leaderboardType: 'USER', pageIndex: 1, pageSize: 10 }
const result = await page.evaluate(async (body) => {
  const res = await fetch('/bapi/growth/v1/friendly/growth-paas/resource/summary/list', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  const text = await res.text()
  return { status: res.status, head: text.slice(0, 300), text }
}, body)

console.log('状态:', result.status)
console.log('响应开头:', result.head)
try {
  const obj = JSON.parse(result.text)
  const lb = obj.data?.resourceSummaryList || {}
  console.log('resourceSummaryList 键:', Object.keys(lb))
  console.log('页面 updatedTime:', lb.updatedTime)
  console.log('eligibleUserCount:', lb.eligibleUserCount)
  console.log('eligibleTradingVolume:', lb.eligibleTradingVolume)
} catch {
  console.log('响应非 JSON（可能为 WAF 挑战页）')
}

await browser.close()
