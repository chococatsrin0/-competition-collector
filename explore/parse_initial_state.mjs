// 探索脚本：解析活动页内嵌 JSON，提取活动组/主奖池/Token/时间等字段
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

const parsed = await page.evaluate(() => {
  for (const s of document.querySelectorAll('script[type="application/json"]')) {
    const t = s.textContent || ''
    try {
      const obj = JSON.parse(t)
      if (obj && (obj.activityGroup || (obj.data && obj.data.activityGroup))) {
        return obj
      }
    } catch {
      // 跳过非 JSON
    }
  }
  return null
})

if (!parsed) {
  console.log('未找到可解析的活动 JSON')
  process.exit(1)
}

// 找出实际包含 activityGroup 的层级
let root = parsed
if (root.data && root.data.activityGroup) root = root.data

writeFileSync(resolve(`${saveDir}/activity_initial_state.json`), JSON.stringify(root, null, 2))

console.log('=== 顶层键 ===')
console.log(Object.keys(root))
console.log('\n=== activityGroup 摘要 ===')
console.log(JSON.stringify(root.activityGroup, null, 2).slice(0, 3000))
console.log('\n=== activities 列表 ===')
for (const a of root.activities || []) {
  const summary = {
    id: a.id,
    code: a.code,
    type: a.type,
    status: a.status,
    uri: a.globalContent?.uri,
    publishedTime: a.publishedTime,
    taskExpiredTime: a.taskExpiredTime,
    unpublishedTime: a.unpublishedTime,
    title: a.globalContent?.title,
  }
  console.log(JSON.stringify(summary))
}

console.log('\n[探索] 完整 JSON 已保存 explore/har/activity_initial_state.json')
await browser.close()
