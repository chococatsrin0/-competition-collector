// 探索脚本：打开公告页，滚动触发懒加载，切换分类，捕获真实 API 与公告链接
import { createRequire } from 'node:module'
const require = createRequire(
  'C:/Users/choco/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'
)
const { chromium } = require('playwright')
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

const saveDir = 'explore/har'
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
  if (!/\/bapi\//.test(url) || captured.some((c) => c.url === url && c.postData === (res.request().postData() || null))) {
    return
  }
  let body = null
  try {
    const text = await res.text()
    body = text.length > 200000 ? text.slice(0, 200000) + '...[截断]' : text
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

await page.goto('https://www.binance.com/zh-CN/support/announcement', {
  waitUntil: 'domcontentloaded',
  timeout: 60000,
})
await page.waitForTimeout(6000)

// 滚动触发懒加载
for (let i = 0; i < 8; i++) {
  await page.mouse.wheel(0, 1200)
  await page.waitForTimeout(1500)
}
await page.waitForTimeout(3000)

// 提取页面中的公告链接与文本
const links = await page.evaluate(() => {
  const out = []
  for (const a of document.querySelectorAll('a')) {
    const href = a.getAttribute('href') || ''
    const text = (a.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 200)
    if (href.includes('/support/announcement/')) {
      out.push({ text, href })
    }
  }
  return out.slice(0, 60)
})

// 查找分类标签（交易锦标赛）
const cats = await page.evaluate(() => {
  const out = []
  for (const el of document.querySelectorAll('*')) {
    const t = (el.textContent || '').trim()
    if (t.length <= 30 && /交易锦标赛|Trading Competition/.test(t)) {
      out.push({ tag: el.tagName, text: t })
    }
  }
  return out.slice(0, 20)
})

console.log(`[探索] 捕获 ${captured.length} 个 /bapi/ 请求`)
for (const c of captured) {
  if (/cms|article|announcement/i.test(c.url)) {
    console.log(`\n=== ${c.method} ${c.status} ${c.url}`)
    if (c.postData) console.log(`POST数据: ${c.postData.slice(0, 500)}`)
    if (c.body) console.log(`响应: ${c.body.slice(0, 1500)}`)
  }
}

console.log('\n=== 公告链接样本 ===')
for (const l of links.slice(0, 30)) console.log(`${l.text.slice(0, 80)} | ${l.href}`)

console.log('\n=== 分类标签候选 ===')
for (const c of cats) console.log(`${c.tag}: ${c.text}`)

mkdirSync(dirname(resolve(`${saveDir}/explore_announcement.json`)), { recursive: true })
writeFileSync(
  resolve(`${saveDir}/explore_announcement.json`),
  JSON.stringify({ captured, links, cats }, null, 2)
)
console.log(`\n[探索] 已保存 explore/har/explore_announcement.json`)
await browser.close()
