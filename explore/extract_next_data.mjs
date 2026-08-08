// 探索脚本：提取 __NEXT_DATA__，汇总活动组/主奖池/Token/时间字段
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

const data = await page.evaluate(() => {
  const el = document.getElementById('__NEXT_DATA__')
  if (el) return JSON.parse(el.textContent)
  return null
})

if (!data) {
  console.log('未找到 __NEXT_DATA__')
  process.exit(1)
}

mkdirSync(dirname(resolve(`${saveDir}/next_data.json`)), { recursive: true })
writeFileSync(resolve(`${saveDir}/next_data.json`), JSON.stringify(data, null, 2))

// 定位 dataByRouteId 中的活动数据
const routes = data?.props?.pageProps?.dataByRouteId || {}
let activityRoot = null
for (const [k, v] of Object.entries(routes)) {
  if (v && v.activityGroup) {
    activityRoot = v
    console.log(`找到活动数据于 dataByRouteId.${k}`)
    break
  }
}

if (activityRoot) {
  console.log('\n=== activityGroup 摘要 ===')
  const g = activityRoot.activityGroup
  console.log(JSON.stringify({
    id: g.id,
    code: g.code,
    type: g.type,
    status: g.status,
    publishedTime: g.publishedTime,
    taskExpiredTime: g.taskExpiredTime,
  }, null, 2))

  console.log('\n=== activities 摘要 ===')
  for (const a of activityRoot.activities || []) {
    console.log(JSON.stringify({
      id: a.id,
      uri: a.globalContent?.uri,
      status: a.status,
      publishedTime: a.publishedTime,
      taskExpiredTime: a.taskExpiredTime,
    }))
  }

  console.log('\n=== 第一个活动完整结构（前 6000 字符） ===')
  console.log(JSON.stringify(activityRoot.activities?.[0], null, 2).slice(0, 6000))
}

console.log('\n[探索] 完整 __NEXT_DATA__ 已保存 explore/har/next_data.json')
await browser.close()
