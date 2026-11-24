#!/usr/bin/env node
/**
 * harvest.mjs — 全量抓取 BWIKI 崩铁站主命名空间原文，存到 raw/bwiki/
 *
 * 用法:
 *   node scripts/harvest.mjs titles        # 只枚举标题 -> raw/titles.json
 *   node scripts/harvest.mjs fetch         # 抓正文（断点续传）
 *   node scripts/harvest.mjs fetch --force # 忽略已存在文件重新抓
 *   node scripts/harvest.mjs stats         # 统计
 *
 * 特点: 批量 titles=25/请求、4 并发、失败重试、已存在跳过。
 */
import fs from 'node:fs'
import path from 'node:path'

const API = 'https://wiki.biligame.com/sr/api.php'
const ROOT = path.resolve(process.cwd(), 'raw')
const OUT = path.join(ROOT, 'bwiki')
const TITLES_FILE = path.join(ROOT, 'titles.json')
const INDEX_FILE = path.join(ROOT, 'index.jsonl')
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'

const BATCH = 10
const CONCURRENCY = 2
const RETRY = 3

fs.mkdirSync(OUT, { recursive: true })

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function safeName(title) {
  return title
    .replace(/[\\/:*?"<>|]/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 180)
}

async function api(params) {
  const u = new URL(API)
  u.search = new URLSearchParams({ ...params, format: 'json', formatversion: '2' }).toString()
  for (let i = 0; i < RETRY; i++) {
    try {
      const res = await fetch(u, { headers: { 'User-Agent': UA, Referer: 'https://wiki.biligame.com/sr/' } })
      if (!res.ok) throw new Error('HTTP ' + res.status)
      return await res.json()
    } catch (e) {
      if (i === RETRY - 1) throw e
      await sleep(800 * (i + 1))
    }
  }
}

async function listTitles() {
  let cont = null
  const all = []
  do {
    const p = { action: 'query', list: 'allpages', apnamespace: '0', aplimit: '500' }
    if (cont) p.apcontinue = cont
    const d = await api(p)
    for (const x of d.query.allpages) all.push(x.title)
    cont = d.continue?.apcontinue || null
    process.stdout.write(`\r枚举标题 ${all.length}   `)
    await sleep(200)
  } while (cont)
  fs.writeFileSync(TITLES_FILE, JSON.stringify(all, null, 0))
  console.log(`\n共 ${all.length} 个条目，已写入 ${TITLES_FILE}`)
}

async function fetchBatch(titles, force) {
  const todo = force ? titles : titles.filter((t) => !fs.existsSync(path.join(OUT, safeName(t) + '.txt')))
  if (!todo.length) return 0
  const p = {
    action: 'query',
    prop: 'revisions',
    rvprop: 'content|timestamp',
    rvslots: 'main',
    titles: todo.join('|'),
  }
  const d = await api(p)
  const ts = new Date().toISOString()
  let n = 0
  for (const page of d.query?.pages || []) {
    if (page.missing) continue
    const rev = page.revisions?.[0]
    const text = rev?.slots?.main?.content ?? ''
    const fn = path.join(OUT, safeName(page.title) + '.txt')
    fs.writeFileSync(fn, text)
    fs.appendFileSync(
      INDEX_FILE,
      JSON.stringify({ title: page.title, file: safeName(page.title) + '.txt', size: text.length, rev: rev?.timestamp || '', at: ts }) + '\n'
    )
    n++
  }
  return n
}

async function fetchAll(force) {
  const titles = JSON.parse(fs.readFileSync(TITLES_FILE, 'utf8'))
  const batches = []
  for (let i = 0; i < titles.length; i += BATCH) batches.push(titles.slice(i, i + BATCH))
  let done = 0
  let saved = 0
  let cursor = 0
  const t0 = Date.now()

  async function worker(id) {
    while (true) {
      const idx = cursor++
      if (idx >= batches.length) return
      try {
        saved += await fetchBatch(batches[idx], force)
      } catch (e) {
        fs.appendFileSync(path.join(ROOT, 'errors.log'), `${new Date().toISOString()}\t${batches[idx][0]}\t${e.message}\n`)
      }
      done++
      if (done % 5 === 0 || done === batches.length) {
        const el = (Date.now() - t0) / 1000
        const pct = ((done / batches.length) * 100).toFixed(1)
        process.stdout.write(`\r批次 ${done}/${batches.length} (${pct}%)  存 ${saved} 页  用时 ${el.toFixed(0)}s   `)
      }
      await sleep(700)
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, (_, i) => worker(i)))
  console.log(`\n完成，新增 ${saved} 个文件 -> ${OUT}`)
}

function stats() {
  const files = fs.readdirSync(OUT).filter((f) => f.endsWith('.txt'))
  let bytes = 0
  for (const f of files) bytes += fs.statSync(path.join(OUT, f)).size
  console.log(`文件 ${files.length}  总体积 ${(bytes / 1024 / 1024).toFixed(1)} MB  平均 ${(bytes / files.length / 1024).toFixed(1)} KB`)
}

const cmd = process.argv[2]
const force = process.argv.includes('--force')
if (cmd === 'titles') await listTitles()
else if (cmd === 'fetch') await fetchAll(force)
else if (cmd === 'stats') stats()
else console.log('用法: node scripts/harvest.mjs titles|fetch|stats [--force]')
