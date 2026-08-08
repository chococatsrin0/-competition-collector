// 探索脚本：验证官方域名活动页自动请求是否返回 eligibleUserCount/updatedTime
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
const hits = []

page.on('response', async (res) => {
  const url = res.url()
  if (!/bapi\/growth\/.*resource\/summary\/list/.test(url)) return
  try {
    const obj = await res.json()
    const lb = obj?.data?.resourceSummaryList || {}
    hits.push({
      url,
      post: res.request().postData() || '',
      keys: Object.keys(lb),
      updatedTime: lb.updatedTime ?? null,
      eligible: lb.eligibleUserCount ?? null,
    })
  } catch {}
})

for (const path of [
  'https://www.binance.com/zh-CN/activity/trading-competition/spot-altcoin-festival-wave-BABY2',
  'https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT',
]) {
  try {
    await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(6000)
    await page.evaluate(() => {
      const els = [...document.querySelectorAll('button, [role="tab"], a, div, span')]
      const el = els.find((e) => (e.textContent || '').trim().startsWith('主奖池') && e.offsetParent !== null)
      if (el) el.click()
    })
    await page.waitForTimeout(5000)
  } catch (e) {
    console.log('页面加载失败:', path, e.message)
  }
}

console.log(`捕获 ${hits.length} 个 summary/list 响应`)
for (const h of hits) {
  console.log(JSON.stringify(h))
}
await browser.close()
