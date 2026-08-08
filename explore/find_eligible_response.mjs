// 探索脚本：打开 BABY2 活动页，捕获所有 growth 接口，定位 eligibleUserCount/updatedTime 来源
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
  if (!/bapi\/growth/.test(url)) return
  let text = ''
  try {
    text = await res.text()
  } catch {
    return
  }
  if (text.includes('eligibleUserCount') || (text.includes('updatedTime') && !/"updatedTime":null/.test(text))) {
    hits.push({
      url,
      postData: res.request().postData() || '',
      text: text.slice(0, 3000),
    })
  }
})

// 打开活动页首页
await page.goto(
  'https://www.edhojmmldkl.com/zh-CN/activity/trading-competition/spot-altcoin-festival-wave-BABY2',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(8000)
// 点击各 tab 触发接口
for (const label of ['首页', '主奖池', '第一轮限时奖池']) {
  await page.evaluate((t) => {
    const els = [...document.querySelectorAll('button, [role="tab"], a, div, span')]
    const el = els.find((e) => (e.textContent || '').trim().startsWith(t) && e.offsetParent !== null)
    if (el) el.click()
  }, label)
  await page.waitForTimeout(4000)
}

console.log(`命中 ${hits.length} 个包含 eligibleUserCount/非空updatedTime 的响应`)
for (const h of hits) {
  console.log(`\n=== ${h.url}`)
  console.log(`POST: ${h.postData}`)
  console.log(h.text)
}

// 手动变体探测
const variants = [
  { resourceId: 100016669, leaderboardType: 'USER', pageIndex: 2, pageSize: 10 },
  { resourceIdList: ['100016669'], pageIndex: 1, pageSize: 10 },
  { resourceId: 100016669, leaderboardType: 'USER', pageIndex: 1, pageSize: 10, needEligibleUserCount: true },
]
console.log('\n=== 手动变体 ===')
for (const body of variants) {
  const r = await page.evaluate(async (body) => {
    const res = await fetch('/bapi/growth/v1/friendly/growth-paas/resource/summary/list', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    })
    const obj = await res.json()
    const lb = obj.data?.resourceSummaryList || {}
    return { keys: Object.keys(lb), pageUpdated: lb.updatedTime ?? null, pageIndex: lb.pageIndex }
  }, body)
  console.log(JSON.stringify(body), '->', JSON.stringify(r))
}

await browser.close()
