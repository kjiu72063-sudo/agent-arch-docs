#!/usr/bin/env node
/**
 * scripts/check-mermaid.mjs — 全站 Mermaid 图谱语法校验（构建辅助，非 gate）
 *
 * 为什么需要它：Mermaid 语法错误**不会让 vitepress build 失败**——它只在浏览器
 * 运行时抛错，页面上的图会变成一块红色报错。所以构建绿灯 ≠ 图能画出来。
 *
 * 本脚本用项目自带的 mermaid 解析器（node_modules/mermaid，与站点运行时同版本）
 * 把每张图 parse 一遍，把错误在构建阶段就暴露出来。
 *
 *   node scripts/check-mermaid.mjs            # 校验全站所有 md
 *   node scripts/check-mermaid.mjs training   # 只校验指定目录
 *
 * 退出码：0 = 全部通过；1 = 有语法错误。
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const TARGETS = process.argv.slice(2)
const DIRS = TARGETS.length ? TARGETS : ['.']

// mermaid 的 parse() 在纯 Node 下需要一个最小 DOM 壳；只用于解析，不渲染。
// 关键点：dompurify 的初始化判定是
//   window.document.nodeType === 9 && window.Element
// 少任何一项它都会退回工厂函数，于是 DOMPurify.addHook 不存在 → mermaid 起不来。
if (!globalThis.document) {
  const noop = () => {}
  class ElementStub {
    constructor(tag = 'div') {
      this.tagName = String(tag).toUpperCase()
      this.nodeType = 1
      this.style = {}
      this.dataset = {}
      this.children = []
      this.childNodes = []
      this.attributes = []
      this.classList = { add: noop, remove: noop, contains: () => false, toggle: noop }
      this.innerHTML = ''
      this.textContent = ''
      this.ownerDocument = null
    }
    setAttribute() {}
    getAttribute() { return null }
    removeAttribute() {}
    hasAttribute() { return false }
    appendChild(c) { this.children.push(c); return c }
    removeChild(c) { return c }
    insertBefore(c) { return c }
    addEventListener() {}
    removeEventListener() {}
    dispatchEvent() { return true }
    querySelector() { return null }
    querySelectorAll() { return [] }
    getElementsByTagName() { return [] }
    cloneNode() { return new ElementStub(this.tagName) }
    remove() {}
    contains() { return false }
    getBoundingClientRect() { return { top: 0, left: 0, width: 0, height: 0, bottom: 0, right: 0 } }
  }
  const documentStub = new ElementStub('#document')
  documentStub.nodeType = 9                    // dompurify 硬性要求 9
  documentStub.createElement = (tag) => new ElementStub(tag)
  documentStub.createElementNS = (ns, tag) => new ElementStub(tag)
  documentStub.createTextNode = (t) => ({ nodeType: 3, textContent: String(t) })
  documentStub.createDocumentFragment = () => new ElementStub('#fragment')
  documentStub.createNodeIterator = () => ({ nextNode: () => null })
  documentStub.getElementsByTagName = () => []
  documentStub.querySelector = () => null
  documentStub.querySelectorAll = () => []
  documentStub.getElementById = () => null
  documentStub.addEventListener = noop
  documentStub.removeEventListener = noop
  documentStub.importNode = (n) => n
  documentStub.currentScript = null
  documentStub.body = new ElementStub('body')
  documentStub.head = new ElementStub('head')
  documentStub.documentElement = new ElementStub('html')
  documentStub.implementation = { createHTMLDocument: () => documentStub }

  globalThis.document = documentStub
  globalThis.window = globalThis
  globalThis.Element = ElementStub
  globalThis.Node = { ELEMENT_NODE: 1, TEXT_NODE: 3, DOCUMENT_NODE: 9 }
  globalThis.HTMLTemplateElement = ElementStub
  globalThis.DOMParser = class { parseFromString() { return { documentElement: new ElementStub() } } }
  globalThis.NodeFilter = {}
  // mermaid 在 import 期就会 window.addEventListener("load", ...)
  globalThis.addEventListener = noop
  globalThis.removeEventListener = noop
  globalThis.dispatchEvent = () => true
}

const mermaidMod = await import('mermaid')
const mermaid = mermaidMod.default

async function collect(dir) {
  const abs = path.join(ROOT, dir)
  if (!fs.existsSync(abs)) return []
  const out = []
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name)
      if (e.isDirectory()) {
        if (e.name === 'node_modules' || e.name === '.vitepress' || e.name === 'fixtures') continue
        walk(p)
      } else if (e.name.endsWith('.md')) out.push(p)
    }
  }
  walk(abs)
  return out
}

/** 抽出 ```mermaid ... ``` 代码块，返回 [{startLine, code}] */
function extractBlocks(md) {
  const lines = md.split(/\r?\n/)
  const blocks = []
  let i = 0
  while (i < lines.length) {
    if (/^\s*```+\s*mermaid\s*$/.test(lines[i])) {
      const start = i + 1
      let j = i + 1
      while (j < lines.length && !/^\s*```+\s*$/.test(lines[j])) j++
      blocks.push({ startLine: i + 1, code: lines.slice(start, j).join('\n') })
      i = j + 1
    } else i++
  }
  return blocks
}

const files = (await Promise.all(DIRS.map(collect))).flat()
let total = 0
const failures = []

for (const file of files) {
  const md = fs.readFileSync(file, 'utf8')
  for (const b of extractBlocks(md)) {
    if (!b.code.trim()) continue
    total++
    const rel = path.relative(ROOT, file).replace(/\\/g, '/')
    try {
      await mermaid.parse(b.code)
    } catch (err) {
      // mermaid 的 Parse error 前几行是「出错行 + 位置指针 + 期望 token」，保留最有信息量的部分
      const raw = String(err && err.message ? err.message : err)
      const msg = raw.split('\n').slice(0, 5).join('\n      ')
      failures.push({ rel, line: b.startLine, msg })
    }
  }
}

console.log(`扫描 ${files.length} 个 md 文件，共 ${total} 张 Mermaid 图`)
if (failures.length === 0) {
  console.log(`PASS: ${total}/${total} 张图语法全部通过`)
  process.exit(0)
}
console.log(`\nFAIL: ${failures.length}/${total} 张图有语法错误\n`)
for (const f of failures) console.log(`  ✖ ${f.rel}:${f.line}\n    ${f.msg}\n`)
process.exit(1)
