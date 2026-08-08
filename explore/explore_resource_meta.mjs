// 探索脚本：查找活动页内嵌的 resourceId->名称 映射，并探测公告详情 API
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
  const u = res.url()
  if (!/\/bapi\//.test(u)) return
  const postData = res.request().postData() || null
  if (captured.some((c) => c.url === u && c.postData === postData)) return
  let body = null
  try {
    const text = await res.text()
    body = text.length > 200000 ? text.slice(0, 200000) + '...[截断]' : text
  } catch {
    body = '<无法读取响应体>'
  }
  captured.push({ url: u, status: res.status(), method: res.request().method(), postData, body })
})

await page.goto(
  'https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(8000)

// 1. 在页面源码/脚本中搜索 resourceId 与「主奖池」
const hits = await page.evaluate(() => {
  const html = document.documentElement.outerHTML
  const scripts = [...document.querySelectorAll('script')].map((s) => s.textContent || '')
  const hay = html + '\n' + scripts.join('\n')
  const out = []
  for (const id of ['100016874', '100016875', '100016877', '100016879']) {
    const idx = hay.indexOf(id)
    if (idx > -1) out.push({ id, ctx: hay.slice(Math.max(0, idx - 300), idx + 500) })
  }
  return out
})

console.log('=== 页面内 resourceId 上下文 ===')
for (const h of hits) {
  console.log(`\n[${h.id}]\n${h.ctx}\n`)
}

// 2. 在页面中找「主奖池」文本附近的 data
const poolHits = await page.evaluate(() => {
  const html = document.documentElement.outerHTML
  const out = []
  let idx = 0
  while (true) {
    const i = html.indexOf('主奖池', idx)
    if (i === -1) break
    out.push(html.slice(Math.max(0, i - 200), i + 300))
    idx = i + 3
    if (out.length >= 5) break
  }
  return out
})
console.log('\n=== 页面内「主奖池」上下文 ===')
for (const p of poolHits) console.log(`\n${p}\n`)

// 3. 探测公告详情 API
const detailProbes = [
  {
    name: 'cms article detail',
    path: '/bapi/apex/v1/public/apex/cms/article/detail/query',
    params: { code: '93cc46505d6b46c9be248138b836cb7c' },
  },
  {
    name: 'cms article detail POST',
    path: '/bapi/apex/v1/public/apex/cms/article/detail/query',
    body: { code: '93cc46505d6b46c9be248138b836cb7c' },
  },
  {
    name: 'cms article query',
    path: '/bapi/composite/v1/public/cms/article/query',
    params: { code: '93cc46505d6b46c9be248138b836cb7c' },
  },
]
console.log('\n=== 公告详情 API 探测 ===')
for (const p of detailProbes) {
  const url = 'https://www.binance.com' + p.path + (p.params ? '?' + new URLSearchParams(p.params) : '')
  const result = await page.evaluate(
    async ({ url, body }) => {
      try {
        const res = await fetch(url, {
          method: body ? 'POST' : 'GET',
          headers: body ? { 'content-type': 'application/json' } : undefined,
          body: body ? JSON.stringify(body) : undefined,
        })
        return { status: res.status, text: (await res.text()).slice(0, 3000) }
      } catch (e) {
        return { status: -1, text: 'fetch error: ' + e.message }
      }
    },
    { url, body: p.body }
  )
  console.log(`\n--- ${p.name} ${p.path}`)
  console.log(`响应(${result.status}): ${result.text}`)
}

mkdirSync(dirname(resolve(`${saveDir}/explore_resource_meta.json`)), { recursive: true })
writeFileSync(
  resolve(`${saveDir}/explore_resource_meta.json`),
  JSON.stringify({ hits, poolHits, captured }, null, 2)
)
console.log(`\n[探索] 已保存 explore/har/explore_resource_meta.json`)
await browser.close()
