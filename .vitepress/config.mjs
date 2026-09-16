import { defineConfig } from 'vitepress'
import { withMermaid } from "vitepress-plugin-mermaid"

// Agent 架构知识体系 · 文档站配置
// 对标 openclaw-docs：左栏树 / 右栏 TOC / 本地搜索 / 暗亮主题
// Mermaid 已接入（图多字少 · 关系图即导航），自动跟随站点明暗主题。
export default withMermaid({
  title: 'Agent 架构知识体系',
  description: '从会用到会造 Agent · 概念主轴 + 实例专项 + 复刻实战',
  lang: 'zh-CN',
  lastUpdated: true,
  cleanUrls: true,

  // gate/ 下的 fixtures 是验收脚本的检查对象（测试资产），不参与站点渲染
  srcExclude: ['**/fixtures/**'],

  // Mermaid 全局配置：亮色用 neutral，暗色由插件自动切换为内置 dark。
  mermaid: {
    securityLevel: 'loose',
    theme: 'neutral',
    themeVariables: {
      fontFamily: 'Noto Sans SC, sans-serif',
    },
  },

  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@600;700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=Space+Grotesk:wght@500;700&display=swap',
    }],
  ],

  themeConfig: {
    nav: [
      { text: '总览', link: '/' },
      { text: '概念主轴', link: '/concepts/prompt' },
      { text: '实例专项', link: '/instances/hermes' },
      { text: '复刻实战', link: '/practice/compare' },
    ],

    sidebar: [
      {
        text: 'Track 0 · 新手前置',
        collapsed: false,
        items: [
          { text: '0 新手前置（总入口）', link: '/start/' },
          { text: '0-1 什么是 LLM', link: '/start/01-llm' },
          { text: '0-2 token 与上下文窗口', link: '/start/02-token' },
          { text: '0-3 对话角色', link: '/start/03-roles' },
          { text: '0-4 工具调用 Tool Use', link: '/start/04-tool-use' },
          { text: '0-5 什么是 Agent', link: '/start/05-agent' },
          { text: '0-6 读懂总览图', link: '/start/06-overview' },
        ],
      },
      {
        text: 'Track A · 概念主轴',
        collapsed: false,
        items: [
          {
            text: '01 prompt engineering',
            link: '/concepts/prompt',
            items: [
              { text: '1-1 入门', link: '/concepts/prompt/intro' },
              { text: '1-2 system prompt 机制', link: '/concepts/prompt/basics' },
              { text: '1-3 策略① 清晰指令', link: '/concepts/prompt/clarity' },
              { text: '1-4 策略②③ 参考+拆分', link: '/concepts/prompt/ref-split' },
              { text: '1-5 策略④⑤⑥ 思考/工具/测试', link: '/concepts/prompt/think-tools-test' },
              { text: '1-6 实例里的 prompt', link: '/concepts/prompt/instances' },
              { text: '1-7 常见坑 + 自检', link: '/concepts/prompt/pitfalls' },
            ],
          },
          { text: '02 context engineering', link: '/concepts/context', items: [
            { text: '2-1 机制详解', link: '/concepts/context/mechanism' },
            { text: '2-2 常见坑 + 自检', link: '/concepts/context/pitfalls' },
            { text: '2-3 设计决策 + 验证', link: '/concepts/context/design' },
          ]},
          { text: '03 harness engineering', link: '/concepts/harness', items: [
            { text: '3-1 机制详解', link: '/concepts/harness/mechanism' },
            { text: '3-2 常见坑 + 自检', link: '/concepts/harness/pitfalls' },
            { text: '3-3 设计决策 + 验证', link: '/concepts/harness/design' },
          ]},
          { text: '04 loop engineering', link: '/concepts/loop', items: [
            { text: '4-1 机制详解', link: '/concepts/loop/mechanism' },
            { text: '4-2 常见坑 + 自检', link: '/concepts/loop/pitfalls' },
            { text: '4-3 设计决策 + 验证', link: '/concepts/loop/design' },
          ]},
          { text: '05 graph engineering', link: '/concepts/graph', items: [
            { text: '5-1 机制详解', link: '/concepts/graph/mechanism' },
            { text: '5-2 常见坑 + 自检', link: '/concepts/graph/pitfalls' },
            { text: '5-3 设计决策 + 验证', link: '/concepts/graph/design' },
          ]},
          { text: '06 skill 体系架构', link: '/concepts/skill', items: [
            { text: '6-1 机制详解', link: '/concepts/skill/mechanism' },
            { text: '6-2 常见坑 + 自检', link: '/concepts/skill/pitfalls' },
            { text: '6-3 设计决策 + 验证', link: '/concepts/skill/design' },
          ]},
        ],
      },
      {
        text: 'Track B · 框架实例专项',
        collapsed: true,
        items: [
          { text: 'Hermes', link: '/instances/hermes' },
          { text: 'DeepAgent', link: '/instances/deepagent' },
          { text: 'OpenClaw', link: '/instances/openclaw' },
          { text: 'Claude Code', link: '/instances/claude-code' },
          { text: 'Codex', link: '/instances/codex' },
          { text: 'DeepSeek Harness', link: '/instances/deepseek-harness' },
        ],
      },
      {
        text: 'Track C · 复刻实战',
        collapsed: true,
        items: [
          { text: '统一对比矩阵', link: '/practice/compare' },
          { text: '学习路径', link: '/practice/path' },
          { text: '掌握自检', link: '/practice/selfcheck' },
          { text: '自研 harness', link: '/practice/build' },
        ],
      },
    ],

    search: {
      provider: 'local',
      options: { translations: { button: { buttonText: '搜索', placeholder: '搜索文档…' }, modal: { noResultsText: '找不到结果', resetButtonTitle: '清除', footer: { selectText: '选择', navigateText: '切换' } } } },
    },

    socialLinks: [],

    docFooter: { prev: '上一页', next: '下一页' },
    outline: { label: '本页目录', level: [2, 3] },
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '浅色',
    darkModeSwitchTitle: '深色',
    lastUpdatedText: '最后更新',

    footer: {
      message: 'Agent 架构知识体系 · v0.6 设计者级深化',
      copyright: '图多字少 · 关系图即导航',
    },
  },
})
