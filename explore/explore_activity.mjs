// 探索脚本：打开交易锦标赛活动页，捕获 growth-paas 排行榜 API 与 resourceId
import { createRequire } from 'node:module'
const require = createRequire(
  'C:/Users/choco/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'
)
const { chromium } = require('playwright')
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

const saveDir = 'explore/har'
const url =
  process.argv.find((a) => a.startsWith('http')) ||
  'https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT'

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
const captured = []

page.on('response', async (res) => {
  const u = res.url()
  if (!/\/bapi\//.test(u)) return
  const postData = res.request().postData() || null
  if (captured.some((c) => c.url === u && c.postData === postData)) return
  let body = null
  try {
    const text = await res.text()
    body = text.length > 300000 ? text.slice(0, 300000) + '...[截断]' : text
  } catch {
    body = '<无法读取响应体>'
  }
  captured.push({ url: u, status: res.status(), method: res.request().method(), postData, body })
})

console.log(`[探索] 打开活动页: ${url}`)
try {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.waitForTimeout(10000)
} catch (e) {
  console.log('[探索] 加载异常:', e.message)
}

// 滚动触发排行榜懒加载
for (let i = 0; i < 10; i++) {
  await page.mouse.wheel(0, 1200)
  await page.waitForTimeout(1500)
}
await page.waitForTimeout(4000)

// 尝试点击排行榜页签（如 Leaderboard / 排行榜）
for (const label of ['排行榜', 'Leaderboard', '排名']) {
  const found = await page.evaluate((t) => {
    const els = [...document.querySelectorAll('button, [role="tab"], a, div')]
    const el = els.find((e) => (e.textContent || '').trim() === t && e.offsetParent !== null)
    if (el) {
      el.click()
      return true
    }
    return false
  }, label)
  if (found) {
    console.log(`[探索] 已点击「${label}」`)
    await page.waitForTimeout(5000)
    break
  }
}

const pageText = (await page.evaluate(() => document.body.innerText)).slice(0, 2500)
console.log('\n=== 页面文本(前2500字) ===')
console.log(pageText)

console.log('\n=== 捕获到的 growth/resource API ===')
for (const c of captured) {
  if (/growth|resource|leaderboard/i.test(c.url)) {
    console.log(`\n--- ${c.method} ${c.status} ${c.url}`)
    if (c.postData) console.log(`POST: ${c.postData.slice(0, 800)}`)
    if (c.body) console.log(`BODY: ${c.body.slice(0, 3000)}`)
  }
}

mkdirSync(dirname(resolve(`${saveDir}/explore_activity.json`)), { recursive: true })
writeFileSync(
  resolve(`${saveDir}/explore_activity.json`),
  JSON.stringify({ captured, pageText }, null, 2)
)
console.log(`\n[探索] 已保存 explore/har/explore_activity.json`)
await browser.close()
