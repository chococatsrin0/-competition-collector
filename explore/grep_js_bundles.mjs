// 探索脚本：从活动页 HTML 提取 JS bundle 列表，搜索 growth-paas API 路径
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

// 拦截静态资源请求，收集 JS bundle 内容
const jsContents = []
page.on('response', async (res) => {
  const url = res.url()
  if (/(\.js(\?|$))/.test(url) && /static|bnstatic/.test(url)) {
    try {
      const text = await res.text()
      jsContents.push({ url, len: text.length, text })
    } catch {}
  }
})

await page.goto(
  'https://www.binance.com/activity/trading-competition/spot-altcoin-festival-wave-MMT',
  { waitUntil: 'domcontentloaded', timeout: 60000 }
)
await page.waitForTimeout(12000)

console.log(`捕获到 ${jsContents.length} 个 JS 文件`)

// 搜索 growth-paas / resource / activity-group 相关 API 路径
const patterns = [
  /bapi\/growth\/v1\/friendly\/growth-paas\/[a-z0-9/_-]+/gi,
  /activity-group[a-z0-9/_-]*/gi,
  /resource\/summary[a-z0-9/_-]*/gi,
]

const hits = new Map()
for (const js of jsContents) {
  for (const pat of patterns) {
    const matches = js.text.match(pat) || []
    for (const m of matches) {
      if (!hits.has(m)) hits.set(m, js.url)
    }
  }
}

console.log('\n=== 发现的 API 路径（去重） ===')
for (const [path, src] of hits) {
  console.log(`${path}\n    <- ${src}`)
}

// 保存较大的 bundle 供进一步分析
mkdirSync(resolve(`${saveDir}/bundles`), { recursive: true })
let saved = 0
for (const js of jsContents.sort((a, b) => b.len - a.len).slice(0, 5)) {
  const name = resolve(`${saveDir}/bundles/bundle_${saved}.js`)
  writeFileSync(name, js.text)
  console.log(`\n已保存 ${name} (${js.len} 字符) <- ${js.url}`)
  saved++
}

await browser.close()
