// 探索脚本：在活动页内直接探测候选接口，并点击各奖池页签捕获排行榜 API
import { createRequire } from 'node:module'
const require = createRequire(
  'C:/Users/choco/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/'
)
const { chromium } = require('playwright')
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

const saveDir = 'explore/har'
const url = 'https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT'

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
  if (!/growth-paas/.test(u)) return
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

await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 })
await page.waitForTimeout(8000)

// 1. 直接探测候选接口（页面同源 fetch，带相同 cookie/UA）
const probes = [
  {
    name: 'resource/summary/list',
    path: '/bapi/growth/v1/friendly/growth-paas/resource/summary/list',
    body: { resourceId: 100016875, leaderboardType: 'USER', pageIndex: 1, pageSize: 100 },
  },
  {
    name: 'resource/summary/list(全部)',
    path: '/bapi/growth/v1/friendly/growth-paas/resource/summary/list',
    body: { resourceIdList: ['100016874', '100016875', '100016877', '100016879'] },
  },
  {
    name: 'resource/summary/detail',
    path: '/bapi/growth/v1/friendly/growth-paas/resource/summary/detail',
    body: { resourceId: 100016875 },
  },
  {
    name: 'resource/summary/list(leaderboard)',
    path: '/bapi/growth/v1/friendly/growth-paas/resource/summary/list',
    body: { resourceId: 100016875, leaderboardType: 'USER', pageIndex: 1, pageSize: 20 },
  },
]

console.log('=== 接口探测 ===')
for (const p of probes) {
  const result = await page.evaluate(
    async ({ path, body }) => {
      try {
        const res = await fetch('https://www.binance.com' + path, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body),
        })
        const text = await res.text()
        return { status: res.status, text: text.slice(0, 4000) }
      } catch (e) {
        return { status: -1, text: 'fetch error: ' + e.message }
      }
    },
    p
  )
  console.log(`\n--- ${p.name} [${p.path}]`)
  console.log(`请求: ${JSON.stringify(p.body)}`)
  console.log(`响应(${result.status}): ${result.text}`)
}

// 2. 点击各奖池页签，观察排行榜 API
console.log('\n=== 点击页签 ===')
for (const label of ['主奖池', '第一轮限时奖池', '第二轮限时奖池']) {
  const clicked = await page.evaluate((t) => {
    const els = [...document.querySelectorAll('button, [role="tab"], a, div, span')]
    const el = els.find((e) => (e.textContent || '').trim().startsWith(t) && e.offsetParent !== null)
    if (el) {
      el.click()
      return true
    }
    return false
  }, label)
  console.log(`点击「${label}」: ${clicked ? '成功' : '未找到'}`)
  await page.waitForTimeout(5000)
}

console.log('\n=== 页签点击后捕获的 growth-paas 请求 ===')
for (const c of captured) {
  console.log(`\n--- ${c.method} ${c.status} ${c.url}`)
  if (c.postData) console.log(`POST: ${c.postData.slice(0, 800)}`)
  if (c.body) console.log(`BODY: ${c.body.slice(0, 2500)}`)
}

mkdirSync(dirname(resolve(`${saveDir}/explore_leaderboard_api.json`)), { recursive: true })
writeFileSync(
  resolve(`${saveDir}/explore_leaderboard_api.json`),
  JSON.stringify({ captured }, null, 2)
)
console.log(`\n[探索] 已保存 explore/har/explore_leaderboard_api.json`)
await browser.close()
