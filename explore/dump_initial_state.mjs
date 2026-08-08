// 探索脚本：提取活动页内嵌 JSON 的完整结构
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

await page.goto(
  'https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(8000)

// 找出包含活动数据的 script 标签与变量名
const scripts = await page.evaluate(() => {
  const out = []
  for (const s of document.querySelectorAll('script')) {
    const t = s.textContent || ''
    if (t.includes('spot-altcoin-festival-wave-MMT') || t.includes('100016875')) {
      out.push({ type: s.type || '', src: s.src || '', len: t.length, head: t.slice(0, 200) })
    }
  }
  return out
})
console.log('=== 包含活动数据的 script 标签 ===')
for (const s of scripts) console.log(JSON.stringify(s))

// 提取完整的初始化数据对象
const data = await page.evaluate(() => {
  const out = { found: [] }
  for (const s of document.querySelectorAll('script')) {
    const t = s.textContent || ''
    // 常见内嵌模式: window.__INITIAL_STATE__ = {...}; 或 self.__next_f.push(...)
    const m = t.match(/window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*<\/?script/i)
    if (m) out.found.push({ name: '__INITIAL_STATE__', json: m[1] })
    const m2 = t.match(/(?:window\.)?__INITIAL_DATA__\s*=\s*(\{.*\})/s)
    if (m2) out.found.push({ name: '__INITIAL_DATA__', json: m2[1] })
    if (t.includes('"activityGroup"') && t.includes('"activities"')) {
      out.found.push({ name: 'script-with-activities', len: t.length, head: t.slice(0, 300) })
    }
  }
  return out
})

console.log('\n=== 内嵌数据定位 ===')
for (const f of data.found) {
  console.log(`${f.name}: len=${f.json ? f.json.length : f.len} head=${(f.head || f.json || '').slice(0, 300)}`)
}

// 直接抓取整个页面 HTML 里 activities 数组附近的结构并保存原文
const html = await page.content()
writeFileSync(resolve(`${saveDir}/activity_page.html`), html)

// 用正则提取 activities 数组 JSON 片段（从 "activities": 到最近的 "}]}" 附近）
const m = html.match(/"activities":\s*(\[[\s\S]*?\]\s*\]\s*})/)
if (m) {
  writeFileSync(resolve(`${saveDir}/activities_fragment.json`), m[1].slice(0, 200000))
  console.log(`\nactivities 片段已保存（${m[1].length} 字符）`)
} else {
  console.log('\n未找到 activities 数组片段')
}

console.log('\n[探索] 已保存 explore/har/activity_page.html')
await browser.close()
