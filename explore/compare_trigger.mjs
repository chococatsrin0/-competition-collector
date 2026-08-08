// 探索脚本：对比「首屏自动请求」与「点击 tab 请求」的 referer 与响应 updatedTime
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
const events = []

page.on('request', (req) => {
  if (req.url().includes('resource/summary/list')) {
    events.push({ type: 'request', time: Date.now(), referer: req.headers()['referer'] || null, post: req.postData() })
  }
})
page.on('response', async (res) => {
  if (res.url().includes('resource/summary/list')) {
    try {
      const obj = await res.json()
      const lb = obj?.data?.resourceSummaryList || {}
      events.push({
        type: 'response',
        time: Date.now(),
        keys: Object.keys(lb),
        updatedTime: lb.updatedTime ?? null,
        eligible: lb.eligibleUserCount ?? null,
      })
    } catch {
      events.push({ type: 'response', time: Date.now(), parseError: true })
    }
  }
})

// 1. 首屏
await page.goto('https://www.edhojmmldkl.com/zh-CN/activity/trading-competition/spot-altcoin-festival-wave-BABY2', {
  waitUntil: 'domcontentloaded',
  timeout: 60000,
})
await page.waitForTimeout(7000)
console.log('首屏后事件数:', events.length)

// 2. 点击主奖池 tab
await page.evaluate(() => {
  const els = [...document.querySelectorAll('button, [role="tab"], a, div, span')]
  const el = els.find((e) => (e.textContent || '').trim().startsWith('主奖池') && e.offsetParent !== null)
  if (el) el.click()
})
await page.waitForTimeout(6000)
console.log('点击后事件数:', events.length)
console.log('页面 URL:', page.url())

for (const e of events) {
  console.log(JSON.stringify(e))
}
await browser.close()
