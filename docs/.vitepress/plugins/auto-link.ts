/**
 * 自动内链插件
 *
 * 构建时扫描正文，把命中的词条替换成链接。规则：
 *   - 不做数量限制：凡是命中词条的正文文本一律加链，同一页出现几次就链几次。
 *     段落之间互不占用配额：读者在任何一段看到名词，都能当场点过去。
 *     （早期版本是「每页一次」，结果页首引言和基本信息表把配额吃光，
 *      正文主体一条金线都没有，移动端读者根本点不了。）
 *   - 长词优先：「匹诺康尼危机」不会被拆成「匹诺康尼」+「危机」
 *   - 跳过标题、代码、已有链接内部
 *   - 不链当前页面自己，避免自指
 *   - 词条表来自 scripts/collect.mjs 生成的 entries.json
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type MarkdownIt from 'markdown-it'
const here = path.dirname(fileURLToPath(import.meta.url))
const dataFile = path.resolve(here, '../data/entries.json')

type Target = { term: string; path: string; kind: 'entry' | 'anchor' | 'skip'; slug: string }

let cached: Target[] | null = null

function loadTargets(): Target[] {
  if (cached) return cached
  try {
    const raw = JSON.parse(fs.readFileSync(dataFile, 'utf8'))
    cached = (raw.linkTargets as Target[]) || []
  } catch {
    cached = []
  }
  return cached
}

/** 缓存失效钩子：dev 模式下 collect 重跑后可调用 */
export function invalidateAutoLinkCache() {
  cached = null
}

export function autoLinkPlugin(md: MarkdownIt) {
  md.core.ruler.push('hq_auto_link', state => {
    const targets = loadTargets()
    if (!targets.length) return

    const env = state.env as Record<string, unknown>
    const rel = String(env.relativePath || '').replace(/\\/g, '/')
    const selfSlug = rel.replace(/\.md$/, '')
    const selfDir = path.posix.dirname('/' + selfSlug)

    /**
     * 生成相对当前页面的链接。
     * 用相对路径而非绝对路径，有两个好处：
     *   1. 部署到 /repo/ 子路径时不需要手动拼 base，浏览器按当前 URL 解析
     *   2. VitePress 的死链检查器能正确解析相对路径，不会误报
     */
    const toHref = (targetPath: string) => {
      const [pure, hash] = targetPath.split('#')
      let href = path.posix.relative(selfDir, pure)
      if (!href.startsWith('.')) href = './' + href
      return hash ? `${href}#${hash}` : href
    }

    const Token = state.Token

    const textToken = (content: string) => {
      const t = new Token('text', '', 0)
      t.content = content
      return t
    }

    const linkToken = (href: string) => {
      const open = new Token('link_open', 'a', 1)
      open.attrSet('href', href)
      open.attrSet('class', 'hq-ilink')
      return open
    }

    const splitText = (text: string) => {
      const out: InstanceType<typeof Token>[] = []
      let rest = text

      while (rest) {
        let best: { idx: number; term: string; target: Target } | null = null

        for (const t of targets) {
          if (t.slug === selfSlug) continue
          const idx = rest.indexOf(t.term)
          if (idx === -1) continue
          // 位置更靠前优先；同位置时长词优先
          if (
            !best ||
            idx < best.idx ||
            (idx === best.idx && t.term.length > best.term.length)
          ) {
            best = { idx, term: t.term, target: t }
          }
        }

        if (!best) {
          out.push(textToken(rest))
          break
        }

        if (best.idx > 0) out.push(textToken(rest.slice(0, best.idx)))
        // 保护词：只吞掉，不链接（如宝石名「砂金石」不该指向人物「砂金」）
        if (best.target.kind !== 'skip') {
          out.push(linkToken(toHref(best.target.path)))
        }
        out.push(textToken(best.term))
        if (best.target.kind !== 'skip') {
          out.push(new Token('link_close', 'a', -1))
        }

        rest = rest.slice(best.idx + best.term.length)
      }

      return out
    }

    for (let i = 0; i < state.tokens.length; i++) {
      const token = state.tokens[i]
      if (token.type !== 'inline' || !token.children) continue

      // 标题不参与内链
      const prev = state.tokens[i - 1]
      if (prev && prev.type === 'heading_open') continue

      const next: typeof token.children = []
      let inLink = 0

      for (const child of token.children) {
        if (child.type === 'link_open') {
          inLink++
          // 手写的站内链接（[匹诺康尼](../locations/penacony)）默认会吃
          // VitePress 的品牌色，在正文里格外扎眼。统一补上 hq-ilink，
          // 让手写链接和自动内链长得一模一样；外链与页内锚点保持原样。
          const href = child.attrGet('href') || ''
          if (href && !/^(?:https?:|mailto:|tel:|\/\/|#)/i.test(href)) {
            child.attrJoin('class', 'hq-ilink')
          }
        } else if (child.type === 'link_close') {
          inLink = Math.max(0, inLink - 1)
        }

        if (child.type === 'text' && inLink === 0 && child.content) {
          next.push(...splitText(child.content))
        } else {
          next.push(child)
        }
      }

      token.children = next
    }
  })
}
