// 探索脚本：捕获页面自动发出的 summary/list 请求头，复现 eligible 字段
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

let capturedHeaders = null
let capturedPost = null
page.on('request', (req) => {
  const url = req.url()
  if (url.includes('resource/summary/list') && req.method() === 'POST' && !capturedHeaders) {
    capturedHeaders = req.headers()
    capturedPost = req.postData()
  }
})

await page.goto(
  'https://www.edhojmmldkl.com/zh-CN/activity/trading-competition/spot-altcoin-festival-wave-BABY2',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(6000)

// 点击主奖池 tab 触发请求
await page.evaluate(() => {
  const els = [...document.querySelectorAll('button, [role="tab"], a, div, span')]
  const el = els.find((e) => (e.textContent || '').trim().startsWith('主奖池') && e.offsetParent !== null)
  if (el) el.click()
})
await page.waitForTimeout(6000)

console.log('=== 页面自动请求 payload ===')
console.log(capturedPost)
console.log('\n=== 页面自动请求 headers ===')
console.log(JSON.stringify(capturedHeaders, null, 1))

if (capturedHeaders && capturedPost) {
  // 页面内 fetch：带页面同款自定义头（referer/cookie 由浏览器自动带）
  const skipPrefixes = ['referer', 'cookie', 'content-length', 'accept-encoding', 'sec-fetch', 'sec-ch-ua', 'host', 'origin']
  const custom = {}
  for (const [k, v] of Object.entries(capturedHeaders)) {
    if (!skipPrefixes.some((p) => k.startsWith(p))) {
      custom[k] = v
    }
  }
  const body = JSON.parse(capturedPost)
  const result = await page.evaluate(async ({ headers, body }) => {
    const res = await fetch('/bapi/growth/v1/friendly/growth-paas/resource/summary/list', {
      method: 'POST',
      headers: { 'content-type': 'application/json', ...headers },
      body: JSON.stringify(body),
    })
    const obj = await res.json()
    const lb = obj.data?.resourceSummaryList || {}
    return { keys: Object.keys(lb), updatedTime: lb.updatedTime ?? null, eligible: lb.eligibleUserCount ?? null }
  }, { headers: custom, body })
  console.log('\n=== 页面内 fetch 复现（带自定义头） ===')
  console.log(JSON.stringify(result))

  // 用用户提供的完整自定义头再做一次复现
  const fullCustom = {
    'bnc-location': '',
    'bnc-time-zone': 'Asia/Shanghai',
    'bnc-uuid': '419ee6bd-203c-40bc-8cce-075fff0828eb',
    clienttype: 'web',
    csrftoken: 'd41d8cd98f00b204e9800998ecf8427e',
    'device-info': capturedHeaders['device-info'] || '',
    'fvideo-id': capturedHeaders['fvideo-id'] || '',
    'fvideo-token': capturedHeaders['fvideo-token'] || '',
    lang: 'zh-CN',
    'x-passthrough-token': '',
    'x-trace-id': '30a2eb31-81a3-408f-bc63-fd57a76d155b',
    'x-ui-request-trace': '30a2eb31-81a3-408f-bc63-fd57a76d155b',
  }
  const result2 = await page.evaluate(async ({ headers, body }) => {
    const res = await fetch('/bapi/growth/v1/friendly/growth-paas/resource/summary/list', {
      method: 'POST',
      headers: { 'content-type': 'application/json', ...headers },
      body: JSON.stringify(body),
    })
    const obj = await res.json()
    const lb = obj.data?.resourceSummaryList || {}
    return { keys: Object.keys(lb), updatedTime: lb.updatedTime ?? null, eligible: lb.eligibleUserCount ?? null }
  }, { headers: fullCustom, body })
  console.log('\n=== 页面内 fetch 复现（完整自定义头） ===')
  console.log(JSON.stringify(result2))

  // 用 API 请求上下文：完全相同的请求头 + cookie + referer
  const cookies = await context.cookies()
  const cookieStr = cookies.map((c) => `${c.name}=${c.value}`).join('; ')
  const apiHeaders = {}
  for (const [k, v] of Object.entries(capturedHeaders)) {
    if (!['host', 'content-length', 'accept-encoding'].includes(k)) {
      apiHeaders[k] = v
    }
  }
  apiHeaders.cookie = cookieStr
  const r3 = await context.request.post(
    'https://www.edhojmmldkl.com/bapi/growth/v1/friendly/growth-paas/resource/summary/list',
    { headers: apiHeaders, data: JSON.parse(capturedPost) }
  )
  const t3 = await r3.text()
  try {
    const obj3 = JSON.parse(t3)
    const lb3 = obj3.data?.resourceSummaryList || {}
    console.log('\n=== context.request 复现（完整头+cookie） ===')
    console.log('状态:', r3.status(), '键:', Object.keys(lb3), 'updatedTime:', lb3.updatedTime, 'eligible:', lb3.eligibleUserCount)
  } catch {
    console.log('\n=== context.request 复现（完整头+cookie） ===')
    console.log('状态:', r3.status(), '响应非JSON:', t3.slice(0, 200))
  }
}

await browser.close()
