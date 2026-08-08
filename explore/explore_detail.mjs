// 探索脚本：打开公告分类页 93 与交易锦标赛详情页，捕获 API，提取活动按钮链接
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
  if (!/\/bapi\//.test(url)) return
  const postData = res.request().postData() || null
  if (captured.some((c) => c.url === url && c.postData === postData)) return
  let body = null
  try {
    const text = await res.text()
    body = text.length > 200000 ? text.slice(0, 200000) + '...[截断]' : text
  } catch {
    body = '<无法读取响应体>'
  }
  captured.push({ url, status: res.status(), method: res.request().method(), postData, body })
})

async function visit(url, label) {
  console.log(`\n[探索] === ${label}: ${url}`)
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(6000)
  } catch (e) {
    console.log('[探索] 加载异常:', e.message)
  }
  for (let i = 0; i < 3; i++) {
    await page.mouse.wheel(0, 1000)
    await page.waitForTimeout(1000)
  }
}

// 1. 分类页 93
await visit('https://www.binance.com/zh-CN/support/announcement/list/93', '分类页 93')
const listLinks = await page.evaluate(() => {
  const out = []
  for (const a of document.querySelectorAll('a')) {
    const href = a.getAttribute('href') || ''
    const text = (a.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 150)
    if (href.includes('/support/announcement/detail/')) out.push({ text, href })
  }
  return out.slice(0, 40)
})

// 2. MMT 交易量锦标赛详情
await visit('https://www.binance.com/zh-CN/support/announcement/detail/93cc46505d6b46c9be248138b836cb7c', 'MMT 交易量锦标赛详情')

// 提取详情页所有链接（找立即参与按钮）
const detailLinks = await page.evaluate(() => {
  const out = []
  for (const a of document.querySelectorAll('a')) {
    const href = a.getAttribute('href') || ''
    const text = (a.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120)
    if (href && !href.startsWith('javascript')) out.push({ text, href })
  }
  return out.slice(0, 60)
})

const detailText = (await page.evaluate(() => document.body.innerText)).slice(0, 3000)

console.log('\n=== 分类93公告链接 ===')
for (const l of listLinks.slice(0, 30)) console.log(`${l.text.slice(0, 70)} | ${l.href}`)

console.log('\n=== 详情页链接 ===')
for (const l of detailLinks) console.log(`${l.text.slice(0, 60)} | ${l.href}`)

console.log('\n=== 详情页文本(前3000字) ===')
console.log(detailText)

console.log('\n=== 相关 API 请求 ===')
for (const c of captured) {
  if (/cms|article|announcement|growth/i.test(c.url)) {
    console.log(`\n--- ${c.method} ${c.status} ${c.url}`)
    if (c.postData) console.log(`POST: ${c.postData.slice(0, 600)}`)
    if (c.body) console.log(`BODY: ${c.body.slice(0, 2000)}`)
  }
}

mkdirSync(dirname(resolve(`${saveDir}/explore_detail.json`)), { recursive: true })
writeFileSync(
  resolve(`${saveDir}/explore_detail.json`),
  JSON.stringify({ captured, listLinks, detailLinks, detailText }, null, 2)
)
console.log(`\n[探索] 已保存 explore/har/explore_detail.json`)
await browser.close()
