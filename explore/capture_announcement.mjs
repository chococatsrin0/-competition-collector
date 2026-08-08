// 探索脚本：打开 Binance 公告页，捕获网络请求，定位真实 API
// 用法: node explore/capture_announcement.mjs [--save explore/har/announcement.json]
import { createRequire } from 'node:module'
const require = createRequire(
  'C:/Users/choco/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'
)
const { chromium } = require('playwright')
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

const saveArg = process.argv.indexOf('--save')
const savePath = saveArg > -1 ? process.argv[saveArg + 1] : null

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
  const url = res.url()
  if (!/\/bapi\//.test(url)) return
  let body = null
  try {
    const text = await res.text()
    body = text.length > 3000 ? text.slice(0, 3000) + '...[截断]' : text
  } catch {
    body = '<无法读取响应体>'
  }
  captured.push({
    url,
    status: res.status(),
    method: res.request().method(),
    postData: res.request().postData() || null,
    body,
  })
})

const targets = process.argv.filter((a) => a.startsWith('http'))
const url = targets[0] || 'https://www.binance.com/zh-CN/support/announcement'

console.log(`[探索] 打开: ${url}`)
try {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.waitForTimeout(8000)
} catch (e) {
  console.log('[探索] 页面加载异常:', e.message)
}

console.log(`[探索] 捕获到 ${captured.length} 个 /bapi/ 请求`)
for (const c of captured) {
  console.log(`\n=== ${c.method} ${c.status} ${c.url}`)
  if (c.postData) console.log(`POST数据: ${c.postData}`)
  if (c.body) console.log(`响应: ${c.body.slice(0, 800)}`)
}

if (savePath) {
  mkdirSync(dirname(resolve(savePath)), { recursive: true })
  writeFileSync(resolve(savePath), JSON.stringify(captured, null, 2))
  console.log(`[探索] HAR 已保存: ${savePath}`)
}

await browser.close()
