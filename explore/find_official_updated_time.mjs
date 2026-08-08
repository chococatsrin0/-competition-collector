// 探索脚本：定位官方活动页「数据上次更新时间」的来源
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
const apiResponses = []

page.on('response', async (res) => {
  const url = res.url()
  if (!/\/bapi\//.test(url)) return
  try {
    const text = await res.text()
    apiResponses.push({ url, post: res.request().postData() || '', text })
  } catch {}
})

await page.goto(
  'https://www.binance.com/zh-CN/activity/trading-competition/spot-altcoin-festival-wave-MMT/Main-Reward',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(10000)

// 1. 页面文本中找「更新时间」相关
const text = await page.evaluate(() => document.body.innerText)
const lines = text.split('\n').filter((l) => /更新|同步|时间/.test(l))
console.log('=== 页面含「更新/同步/时间」的文本行 ===')
for (const l of lines.slice(0, 30)) console.log(' ', l.trim())

// 2. 在所有 API 响应里找近期毫秒时间戳（2026-08-08 ~ 2026-08-09）
console.log('\n=== 含 1786xxx 时间戳的响应 ===')
for (const r of apiResponses) {
  const m = r.text.match(/1786\d{9}/)
  if (m) {
    console.log(`--- ${r.url}`)
    console.log(`POST: ${r.post}`)
    const idx = r.text.indexOf(m[0])
    console.log(`时间戳上下文: ...${r.text.slice(Math.max(0, idx - 150), idx + 150)}...`)
  }
}

// 3. 检查 __APP_DATA 中的时间字段
const appData = await page.evaluate(() => {
  const el = document.getElementById('__APP_DATA')
  if (!el) return null
  try {
    return JSON.parse(el.textContent)
  } catch {
    return null
  }
})
if (appData) {
  const walk = (node, path) => {
    const out = []
    if (node && typeof node === 'object') {
      for (const [k, v] of Object.entries(node)) {
        const key = String(k).toLowerCase()
        if (/update|sync|refresh/.test(key)) {
          out.push({ path: path + '.' + k, value: v })
        }
        out.push(...walk(v, path + '.' + k))
      }
    }
    return out
  }
  const hits = walk(appData, 'root')
  console.log('\n=== __APP_DATA 中含 update/sync 的字段 ===')
  for (const h of hits.slice(0, 20)) console.log(JSON.stringify(h))
}

await browser.close()
