import { defineConfig } from 'vitepress'
import { withMermaid } from "vitepress-plugin-mermaid"

// 大模型工程知识体系 · 文档站配置
// 双模块：Agent 架构（原有 Track 0–D） / 训练·微调·部署（新增 Part 0–8）
// 两者内容零依赖，共用同一套主题、搜索与构建；左栏按 URL 路径自动切换侧边栏。
// Mermaid 已接入（图多字少 · 关系图即导航），自动跟随站点明暗主题。
export default withMermaid({
  title: '大模型工程知识体系',
  description: 'Agent 架构 × 训练·微调·部署 · 从会用到会造 · 概念主轴 + 实例专项 + 复刻实战 + 工程流水线',
  lang: 'zh-CN',
  // 部署到 GitHub Pages 时站点位于子路径 /agent-arch-docs/；本地开发仍用根路径
  base: process.env.GITHUB_ACTIONS ? '/agent-arch-docs/' : '/',
  lastUpdated: true,
  cleanUrls: true,

  // 教程正文里出现的 http://localhost:xxxx 是"用户本机跑起来才有"的服务端点
  // （Ollama 11434 / Open-WebUI 6006 / TensorBoard 等），构建期必然不可达。
  // 这里只放行 loopback，站内 md 相对链接依旧严格校验，不会掩盖真正的死链。
  ignoreDeadLinks: [
    /^https?:\/\/localhost(:\d+)?/,
    /^https?:\/\/127\.0\.0\.1(:\d+)?/,
  ],

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
      { text: 'Agent 架构', link: '/concepts/prompt' },
      { text: '训练·微调·部署', link: '/training/' },
    ],

    // 双模块侧边栏：VitePress 取最长前缀匹配，/training/ 命中训练模块，其余落回 Agent 模块
    sidebar: {
      '/training/': [
        {
          text: 'Part 0 · 导读',
          collapsed: false,
          items: [
            { text: '0 导读与知识地图', link: '/training/' },
          ],
        },
        {
          text: 'Part 1 · 微调基础与环境',
          collapsed: false,
          items: [
            { text: '1-1 大模型训练全景', link: '/training/p1/01-overview' },
            { text: '1-2 微调的能与不能', link: '/training/p1/02-boundary' },
            { text: '1-3 微调的四大难点', link: '/training/p1/03-difficulty' },
            { text: '1-4 显卡选型', link: '/training/p1/04-gpu' },
            { text: '1-5 本地与云端环境', link: '/training/p1/05-env' },
            { text: '1-6 主流微调框架横评', link: '/training/p1/06-frameworks' },
            { text: '1-7 LLaMA-Factory 安装与结构', link: '/training/p1/07-llamafactory' },
            { text: '1-8 模型下载与 WebUI', link: '/training/p1/08-webui' },
            { text: '1-9 调参难点（上）量化与阶段', link: '/training/p1/09-tuning-quant' },
            { text: '1-10 调参难点（下）调度器·RoPE·加速', link: '/training/p1/10-tuning-rope' },
            { text: '1-11 AutoDL 租卡：云上环境全流程', link: '/training/p1/11-autodl' },
          ],
        },
        {
          text: 'Part 2 · 数据工程',
          collapsed: false,
          items: [
            { text: '2-1 微调数据集构建策略', link: '/training/p2/01-data-strategy' },
            { text: '2-2 数据集格式与注册', link: '/training/p2/02-data-format' },
            { text: '2-3 公共数据集使用', link: '/training/p2/03-public-dataset' },
            { text: '2-4 自定义数据集构建', link: '/training/p2/04-custom-dataset' },
          ],
        },
        {
          text: 'Part 3 · 微调方法与加速',
          collapsed: false,
          items: [
            { text: '3-1 高效微调方法全景', link: '/training/p3/01-methods-overview' },
            { text: '3-2 LoRA 深入', link: '/training/p3/02-lora' },
            { text: '3-3 QLoRA 与 bitsandbytes', link: '/training/p3/03-qlora' },
            { text: '3-4 全参 / Freeze / GaLore / BAdam', link: '/training/p3/04-full-freeze' },
            { text: '3-5 训练加速技术', link: '/training/p3/05-accel' },
            { text: '3-6 量化技术专题', link: '/training/p3/06-quantization' },
            { text: '3-7 实验监控与评估', link: '/training/p3/07-monitor-eval' },
            { text: '3-8 实战三则', link: '/training/p3/08-practice' },
          ],
        },
        {
          text: 'Part 4 · 分布式训练',
          collapsed: false,
          items: [
            { text: '4-1 分布式训练基础', link: '/training/p4/01-basics' },
            { text: '4-2 网络环境解读', link: '/training/p4/02-network' },
            { text: '4-3 服务器间互联与 RDMA', link: '/training/p4/03-rdma' },
            { text: '4-4 网络拓扑', link: '/training/p4/04-topology' },
            { text: '4-5 带宽与延迟的影响', link: '/training/p4/05-bandwidth-latency' },
            { text: '4-6 InfiniBand 与 RoCE', link: '/training/p4/06-ib-roce' },
            { text: '4-7 集合通信原语 ★', link: '/training/p4/07-primitives' },
            { text: '4-8 AllReduce 算法演进 ★', link: '/training/p4/08-allreduce' },
            { text: '4-9 通信后端 NCCL 与 Gloo', link: '/training/p4/09-backends' },
            { text: '4-10 数据并行 DP → DDP ★', link: '/training/p4/10-ddp' },
            { text: '4-11 模型并行与流水线并行', link: '/training/p4/11-model-pipeline-parallel' },
            { text: '4-12 DeepSpeed 与 ZeRO ★', link: '/training/p4/12-deepspeed-zero' },
            { text: '4-13 FSDP 与 DeepSpeed 对比 ★', link: '/training/p4/13-fsdp' },
            { text: '4-14 其他优化与实战', link: '/training/p4/14-optim-practice' },
          ],
        },
        {
          text: 'Part 5 · 知识蒸馏',
          collapsed: false,
          items: [
            { text: '5-1 蒸馏是什么', link: '/training/p5/01-what' },
            { text: '5-2 蒸馏技术分类', link: '/training/p5/02-taxonomy' },
            { text: '5-3 响应式蒸馏 ★', link: '/training/p5/03-response' },
            { text: '5-4 特征式蒸馏', link: '/training/p5/04-feature' },
            { text: '5-5 关系式蒸馏', link: '/training/p5/05-relation' },
            { text: '5-6 演进方向', link: '/training/p5/06-evolution' },
            { text: '5-7 大模型蒸馏的挑战', link: '/training/p5/07-challenges' },
            { text: '5-8 工业方案：DeepSeek 与 Qwen', link: '/training/p5/08-industry' },
            { text: '5-9 实战：白盒蒸馏 4B→1.7B ▶', link: '/training/p5/09-practice' },
          ],
        },
        {
          text: 'Part 6 · 部署与推理优化',
          collapsed: false,
          items: [
            { text: '6-1 部署的四大挑战', link: '/training/p6/01-challenges' },
            { text: '6-2 推理优化：KV Cache ★', link: '/training/p6/02-kvcache' },
            { text: '6-3 推理优化：批处理', link: '/training/p6/03-batching' },
            { text: '6-4 模型剪枝', link: '/training/p6/04-pruning' },
            { text: '6-5 编译与加速', link: '/training/p6/05-compile' },
            { text: '6-6 服务化与 API 设计', link: '/training/p6/06-api' },
            { text: '6-7 Ollama 部署全流程 ▶', link: '/training/p6/07-ollama' },
            { text: '6-8 vLLM 深入：PagedAttention ★', link: '/training/p6/08-vllm-pagedattention' },
            { text: '6-9 vLLM + FastAPI 实战 ▶', link: '/training/p6/09-vllm-fastapi' },
            { text: '6-10 其他部署方案 ▶', link: '/training/p6/10-others' },
            { text: '6-11 MLOps 与大模型生命周期', link: '/training/p6/11-mlops' },
          ],
        },
        {
          text: 'Part 7 · 综合实战与展望',
          collapsed: false,
          items: [
            { text: '7-1 端到端综合项目', link: '/training/p7/01-project' },
            { text: '7-2 趋势与职业路径', link: '/training/p7/02-trends' },
          ],
        },
        {
          text: 'Part 8 · 附录',
          collapsed: true,
          items: [
            { text: 'A1 术语表', link: '/training/p8/a1-glossary' },
            { text: 'A2 来源与页码对照', link: '/training/p8/a2-source-map' },
            { text: 'A3 命令与配置速查', link: '/training/p8/a3-cheatsheet' },
          ],
        },
        {
          text: 'Part 9 · 显存与容量规划',
          collapsed: false,
          items: [
            { text: '9-1 显存为什么是第一约束', link: '/training/p9/01-first-constraint' },
            { text: '9-2 显存账本总览：推理5项·训练5项', link: '/training/p9/02-ledger-overview' },
            { text: '9-3 模型权重（上）：参数量从哪来', link: '/training/p9/03-weights-params' },
            { text: '9-4 模型权重（下）：用公式反推', link: '/training/p9/04-weights-formula' },
            { text: '9-5 KV Cache（上）：公式与前4档', link: '/training/p9/05-kv-classic' },
            { text: '9-6 KV Cache（下）：后3档前沿结构', link: '/training/p9/06-kv-frontier' },
            { text: '9-7 激活值：训练显存的最大变量', link: '/training/p9/07-activation' },
            { text: '9-8 优化器状态：12B/参数怎么压', link: '/training/p9/08-optimizer-states' },
            { text: '9-9 算不到的那部分', link: '/training/p9/09-unaccounted' },
            { text: '9-10 并行切分：TP×PP×DP×ZeRO', link: '/training/p9/10-parallel-split' },
            { text: '9-11 硬件选型', link: '/training/p9/11-hardware' },
            { text: '9-11b 成本与绿色 AI', link: '/training/p9/12-cost-green' },
            { text: '9-12 推理调参手册：6旋钮+4预设', link: '/training/p9/13-inference-tuning' },
            { text: '9-13 训练调参手册：8项优先级', link: '/training/p9/14-training-tuning' },
            { text: '9-14 端到端实战：两组预设各算一遍', link: '/training/p9/15-end-to-end' },
            { text: '9-15 交互式计算器', link: '/training/p9/16-calculator' },
            {
              text: '附录',
              collapsed: true,
              items: [
                { text: '9-A 参数词典（85字段）', link: '/training/p9/A-param-dict' },
                { text: '9-B 公式速查卡', link: '/training/p9/B-formula-card' },
                { text: '9-C 主流模型配置对照表', link: '/training/p9/C-model-matrix' },
              ],
            },
          ],
        },
        {
          text: 'Part 10 · 练习案例库',
          collapsed: true,
          items: [
            { text: '10-0 案例库总览与用法', link: '/training/p10/' },
            { text: 'C01 在 AutoDL 上搭好 LLaMA-Factory 环境', link: '/training/p10/c01-llamafactory-env' },
            { text: 'C02 下载 Qwen3-4B-Base 跑通 WebUI', link: '/training/p10/c02-model-download-webui' },
            { text: 'C03 制作合规的 Alpaca 自定义数据集', link: '/training/p10/c03-alpaca-dataset' },
            { text: 'C04 多轮对话 → ShareGPT → 接入', link: '/training/p10/c04-sharegpt-dataset' },
            { text: 'C05 用 LoRA 对 Qwen3-4B-Base 做完整 SFT', link: '/training/p10/c05-lora-sft' },
            { text: 'C06 QLoRA(4-bit) vs LoRA 对照', link: '/training/p10/c06-qlora-vs-lora' },
            { text: 'C07 单卡实测 + 多卡推演：DDP 与 ZeRO-2', link: '/training/p10/c07-ddp-zero2' },
            { text: 'C08 单卡 offload 真跑 + FSDP 配置对照', link: '/training/p10/c08-zero3-fsdp' },
            { text: 'C09 跑通白盒蒸馏：4B → 1.7B', link: '/training/p10/c09-whitebox-distill' },
            { text: 'C10 蒸馏 vs 直接 SFT 效果对比', link: '/training/p10/c10-distill-vs-sft' },
            { text: 'C11 vLLM + FastAPI 部署并调通', link: '/training/p10/c11-vllm-fastapi' },
            { text: 'C12 Ollama 自定义模型 + 吞吐优化', link: '/training/p10/c12-ollama' },
            { text: 'C13 用 9-15 计算器做容量规划', link: '/training/p10/c13-calculator-planning' },
            { text: 'C14 手算复现计算器读数', link: '/training/p10/c14-handcalc-reproduce' },
          ],
        },
      ],
      '/': [
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
            { text: '2-2 设计决策 + 验证', link: '/concepts/context/design' },
            { text: '2-3 常见坑 + 自检', link: '/concepts/context/pitfalls' },
            { text: '2 验收 gate', link: '/concepts/context/gate/context_gate' },
          ]},
          { text: '03 harness engineering', link: '/concepts/harness', items: [
            { text: '3-1 机制详解', link: '/concepts/harness/mechanism' },
            { text: '3-2 设计决策 + 验证', link: '/concepts/harness/design' },
            { text: '3-3 常见坑 + 自检', link: '/concepts/harness/pitfalls' },
            { text: '3 验收 gate', link: '/concepts/harness/gate/harness_gate' },
          ]},
          { text: '04 loop engineering', link: '/concepts/loop', items: [
            { text: '4-1 机制详解', link: '/concepts/loop/mechanism' },
            { text: '4-2 设计决策 + 验证', link: '/concepts/loop/design' },
            { text: '4-3 常见坑 + 自检', link: '/concepts/loop/pitfalls' },
            { text: '4 验收 gate', link: '/concepts/loop/gate/loop_gate' },
          ]},
          { text: '05 graph engineering', link: '/concepts/graph', items: [
            { text: '5-1 机制详解', link: '/concepts/graph/mechanism' },
            { text: '5-2 设计决策 + 验证', link: '/concepts/graph/design' },
            { text: '5-3 常见坑 + 自检', link: '/concepts/graph/pitfalls' },
            { text: '5 验收 gate', link: '/concepts/graph/gate/graph_gate' },
          ]},
          { text: '06 skill 体系架构', link: '/concepts/skill', items: [
            { text: '6-1 概念定义', link: '/concepts/skill/concept' },
            { text: '6-2 基础实践', link: '/concepts/skill/basics' },
            { text: '6-3 渐进披露与按需加载', link: '/concepts/skill/disclosure' },
            { text: '6-4 进阶用法', link: '/concepts/skill/reference-script' },
            { text: '6-5 架构总结', link: '/concepts/skill/architecture' },
            { text: 'skill 验收 gate', link: '/concepts/skill/gate/skill_gate' },
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
          { text: '事实源清单', link: '/practice/sources' },
          { text: '统一对比矩阵', link: '/practice/compare' },
          { text: '学习路径', link: '/practice/path' },
          { text: '掌握自检', link: '/practice/selfcheck' },
          { text: '自研 harness', link: '/practice/build' },
        ],
      },
      {
        text: 'Track D · 生产级流程',
        collapsed: true,
        items: [
          { text: 'D0 导读', link: '/process/' },
          { text: 'D1 第一性原理', link: '/process/principles' },
          { text: 'D2 控制模型 ★', link: '/process/control-model' },
          { text: 'D3 生命周期主干', link: '/process/lifecycle' },
          { text: 'D4 阶段细则（上）S0–S2', link: '/process/stages-1' },
          { text: 'D5 阶段细则（下）S3–S5', link: '/process/stages-2' },
          { text: 'D6 贯穿机制', link: '/process/mechanisms' },
          { text: 'D7 模板库', link: '/process/templates' },
          { text: 'D8 工具·清单·反模式·附录', link: '/process/tooling' },
        ],
      },
      ],
    },

    search: {
      provider: 'local',
      options: { translations: { button: { buttonText: '搜索', placeholder: '搜索文档…' }, modal: { noResultsText: '找不到结果', resetButtonTitle: '清除', footer: { selectText: '选择', navigateText: '切换' } } } },
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/kjiu72063-sudo/agent-arch-docs' },
    ],

    docFooter: { prev: '上一页', next: '下一页' },
    outline: { label: '本页目录', level: [2, 3] },
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '浅色',
    darkModeSwitchTitle: '深色',
    lastUpdatedText: '最后更新',

    footer: {
      message: '✍️ 作者 <strong>Aer</strong> · <a href="https://github.com/kjiu72063-sudo/agent-arch-docs" target="_blank" rel="noopener">GitHub 仓库</a> · 内容持续更新中',
      copyright: '大模型工程知识体系 · Agent 架构 × 训练·微调·部署 · 图多字少 · 关系图即导航',
    },
  },
})
