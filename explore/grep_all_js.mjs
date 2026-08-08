// 探索脚本：抓取全部 JS bundle，定位模块 1492 与活动组查询 API
import { createRequire } from 'node:module'
const require = createRequire(
  'C:/Users/choco/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'
)
const { chromium } = require('playwright')
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

const saveDir = 'explore/har/bundles_all'
mkdirSync(resolve(saveDir), { recursive: true })

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

let idx = 0
page.on('response', async (res) => {
  const url = res.url()
  if (!/\.js(\?|$)/.test(url)) return
  try {
    const text = await res.text()
    if (
      text.includes('growth-paas') ||
      text.includes('activityGroupCode') ||
      /(^|[,;(])\s*1492:\s*function/.test(text)
    ) {
      const name = `${String(idx).padStart(3, '0')}.js`
      writeFileSync(resolve(saveDir, name), text)
      console.log(`已保存 ${name} (${text.length}) <- ${url}`)
      idx++
    }
  } catch {}
})

await page.goto(
  'https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(15000)

// 再触发一些交互以加载更多 chunk
for (const label of ['主奖池', '第一轮限时奖池']) {
  await page.evaluate((t) => {
    const els = [...document.querySelectorAll('button, [role="tab"], a, div, span')]
    const el = els.find((e) => (e.textContent || '').trim().startsWith(t) && e.offsetParent !== null)
    if (el) el.click()
  }, label)
  await page.waitForTimeout(4000)
}

console.log(`\n[探索] 共保存 ${idx} 个相关 JS 文件`)
await browser.close()
