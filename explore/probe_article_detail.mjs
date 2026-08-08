// 探索脚本：探测公告详情 API 的 GET 参数形式
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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
  locale: 'zh-CN',
  viewport: { width: 1440, height: 900 },
})
const page = await context.newPage()
await page.goto('https://www.binance.com/zh-CN/support/announcement', {
  waitUntil: 'domcontentloaded',
  timeout: 60000,
})
await page.waitForTimeout(5000)

const code = '93cc46505d6b46c9be248138b836cb7c'
const probes = [
  `/bapi/apex/v1/public/apex/cms/article/detail/query?articleCode=${code}&type=1&catalogId=93`,
  `/bapi/apex/v1/public/apex/cms/article/detail/query?articleCode=${code}&catalogId=93`,
  `/bapi/apex/v1/public/apex/cms/article/detail/query?articleCode=${code}`,
  `/bapi/apex/v1/public/apex/cms/article/detail/query?articleCode=${code}&type=1&pageNo=1&pageSize=10`,
]

const postProbes = [
  {
    name: 'composite cms article list POST',
    path: '/bapi/composite/v1/public/cms/article/list/query',
    body: { pageNo: 1, pageSize: 5, blockType: 0, type: 1, catalogId: 93 },
  },
  {
    name: 'composite cms article catalog POST',
    path: '/bapi/composite/v1/public/cms/article/catalog/list/query',
    body: { pageNo: 1, pageSize: 5, blockType: 0, type: 1, catalogId: 93 },
  },
]

for (const path of probes) {
  const result = await page.evaluate(async (p) => {
    try {
      const res = await fetch('https://www.binance.com' + p)
      return { status: res.status, text: (await res.text()).slice(0, 2000) }
    } catch (e) {
      return { status: -1, text: 'fetch error: ' + e.message }
    }
  }, path)
  console.log(`\n--- GET ${path}`)
  console.log(`响应(${result.status}): ${result.text}`)
}

for (const p of postProbes) {
  const result = await page.evaluate(
    async ({ path, body }) => {
      try {
        const res = await fetch('https://www.binance.com' + path, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body),
        })
        return { status: res.status, text: (await res.text()).slice(0, 2000) }
      } catch (e) {
        return { status: -1, text: 'fetch error: ' + e.message }
      }
    },
    p
  )
  console.log(`\n--- POST ${p.path} body=${JSON.stringify(p.body)}`)
  console.log(`响应(${result.status}): ${result.text}`)
}

await browser.close()
