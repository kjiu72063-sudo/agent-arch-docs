<script setup>
/**
 * P9Calculator · 「显存与容量规划」交互式计算器
 * ---------------------------------------------------------------
 * 参数与 9-A《参数词典》一一对应；公式与 9-3 ~ 9-10 正文一致。
 * 纯前端计算、无网络请求、无副作用；全部数值实时派生。
 *
 * 公式出处：
 *   权重      = Φ × 位宽字节                          (9-3 / 9-4)
 *   KV(通式)  = 2 · L · n_kv · d_head · s · b · C · B  (9-5)  MHA/GQA/MQA/SWA
 *   KV(MLA)   = L · d_c · s · b · C · B                (9-5)  潜变量式
 *   KV(CSA2)  = KV(MLA) / 4                            (9-6)  跨层复用
 *   激活(推)  = 权重 × 系数（默认 30%）                (9-7)
 *   激活(训)  = 34 · s · b · h · 2B · L                (9-7 / 9-14)
 *   梯度      = 可训练参数 × 2 B                        (9-13)
 *   优化器    = 可训练参数 × opt字节                    (9-8)
 *   摊分      = ÷ (TP × PP × [DP])                     (9-10)
 */
import { computed, ref } from 'vue'

/* ── 档位常量 ───────────────────────────────────────────── */

const ATTN = [
  { id: 'MHA',  label: '多头注意力 (MHA)',        storage: '最大', note: 'n_kv = n_q' },
  { id: 'GQA',  label: '分组查询注意力 (GQA)',     storage: '↓ g/n_q', note: 'n_kv = g < n_q' },
  { id: 'MQA',  label: '多查询注意力 (MQA)',       storage: '↓ 1/n_q', note: 'n_kv = 1' },
  { id: 'MLA',  label: '多头隐变量注意力 (MLA)',   storage: '潜变量', note: '存 d_c，与 n_q 解耦' },
  { id: 'SWA',  label: '滑动窗口注意力 (SWA)',     storage: '↓ min(s,W)', note: '省【存储】' },
  { id: 'DSA',  label: 'DeepSeek 稀疏注意力 (DSA)', storage: '不变', note: '省【带宽】不省存储' },
  { id: 'CSA2', label: '压缩稀疏注意力 2 (CSA2)',  storage: '↓ ~1/4', note: '跨层复用 global KV' },
]

const W_PREC = [
  { id: 'FP16', label: '完整 FP16', bytes: 2 },
  { id: 'BF16', label: 'BF16',      bytes: 2 },
  { id: 'FP8',  label: 'FP8',       bytes: 1 },
  { id: 'INT8', label: 'INT8',      bytes: 1 },
  { id: 'INT4', label: 'Q4 (INT4)', bytes: 0.5 },
]

const KV_PREC = [
  { id: 'FP16', label: 'FP16 / BF16', bytes: 2 },
  { id: 'INT8', label: 'INT8',        bytes: 1 },
  { id: 'INT4', label: 'INT4',        bytes: 0.5 },
]

const OPTIMIZERS = [
  { id: 'SGD',  label: 'SGD',          bytes: 0 },
  { id: 'SGD_M', label: 'SGD + Momentum', bytes: 4 },
  { id: 'RMSProp', label: 'RMSProp',   bytes: 4 },
  { id: 'AdamW', label: 'Adam / AdamW', bytes: 8, csdn: 12 },
]

const SEQ = [2048, 4096, 8192, 16384, 32768]
const BATCH = [1, 2, 4, 6, 8]
const CONC = [1, 2, 4, 8, 16]
const GPU_MEM = [
  { label: 'RTX 5090 (32GB)',  gb: 32,  bw: 1792, rent: 1.10 },
  { label: 'T4 (16GB)',        gb: 16,  bw: 320,  rent: 0.12 },
  { label: 'RTX 4090 (24GB)',  gb: 24,  bw: 1008, rent: 0.70 },
  { label: 'A100 80GB',        gb: 80,  bw: 2039, rent: 1.80 },
  { label: 'H100 80GB',        gb: 80,  bw: 3350, rent: 2.90 },
]

/* 真实模型配置（取自公开模型卡；同 9-C 附录） */
const MODELS = [
  { id: 'cal',   name: 'Custom 3B · MoE · MLA（计算器默认）', params: 3,    active: 0.1, moe: true,  attn: 'MLA',  L: 32, h: 3072, nq: 48,  nkv: 48, ffn: 18944, vocab: 152064, dc: 576, win: 4096 },
  { id: 'q3',    name: 'Qwen2.5-3B · 密集 · GQA',            params: 3.09, active: 3.09, moe: false, attn: 'GQA',  L: 36, h: 2048, nq: 16,  nkv: 2,  ffn: 11008, vocab: 151936, dc: 0,   win: 32768 },
  { id: 'q7',    name: 'Qwen2.5-7B · 密集 · GQA',            params: 7.62, active: 7.62, moe: false, attn: 'GQA',  L: 28, h: 3584, nq: 28,  nkv: 4,  ffn: 18944, vocab: 152064, dc: 0,   win: 32768 },
  { id: 'llama3', name: 'Llama-3.1-8B · 密集 · GQA',          params: 8.03, active: 8.03, moe: false, attn: 'GQA',  L: 32, h: 4096, nq: 32,  nkv: 8,  ffn: 14336, vocab: 128256, dc: 0,   win: 131072 },
  { id: 'mistral', name: 'Mistral-7B · 密集 · SWA',            params: 7.24, active: 7.24, moe: false, attn: 'SWA',  L: 32, h: 4096, nq: 32,  nkv: 8,  ffn: 14336, vocab: 32000,  dc: 0,   win: 4096 },
  { id: 'v3',    name: 'DeepSeek-V3 671B · MoE · MLA',        params: 671,  active: 37,  moe: true,  attn: 'MLA',  L: 61, h: 7168, nq: 128, nkv: 128, ffn: 18432, vocab: 129280, dc: 576, win: 131072 },
]

/* ── 状态 ──────────────────────────────────────────────── */

const tab = ref('infer')
const presetId = ref('cal')

const params = ref(3)          // 十亿(B)
const activeParams = ref(0.1)
const moe = ref(true)
const attn = ref('MLA')
const L = ref(32)
const h = ref(3072)
const nq = ref(48)
const nkv = ref(48)
const ffn = ref(18944)
const vocab = ref(152064)
const dc = ref(576)
const win = ref(4096)

const wPrec = ref('INT8')
const kvPrec = ref('FP16')
const seq = ref(4096)
const batch = ref(1)
const conc = ref(1)

// 微调侧
const trainMode = ref('QLoRA')     // 全参 / LoRA / QLoRA
const loraR = ref(16)
const loraScope = ref('full')      // attn | full
const optimizer = ref('AdamW')
const accum = ref(1)
const zero = ref(3)
const tp = ref(1), pp = ref(1), gpus = ref(1)
const techs = ref({ flash: true, fused: true, dynpad: true, pack: true, ckpt: false, opt8: false, paged: false, pure16: false })

// 硬件 / 成本
const gpuIdx = ref(0)
const frameworkOverhead = ref(1.01)  // GB
const effFactor = ref(0.58)          // 带宽效率系数（decode）
const elecPrice = ref(0.12)          // $/kWh
const carbonInt = ref(0.475)         // kg/kWh
const power = ref(586)               // W

const expanded = ref(false)

/* ── 派生计算 ───────────────────────────────────────────── */

const B = 1e9
const GiB = 1024 ** 3

const applyPreset = (id) => {
  const m = MODELS.find(v => v.id === id)
  if (!m) return
  params.value = m.params; activeParams.value = m.active; moe.value = m.moe
  attn.value = m.attn; L.value = m.L; h.value = m.h; nq.value = m.nq; nkv.value = m.nkv
  ffn.value = m.ffn; vocab.value = m.vocab; dc.value = m.dc; win.value = m.win
}

const dHead = computed(() => Math.max(1, Math.round(h.value / Math.max(1, nq.value))))
const wBytes = computed(() => W_PREC.find(p => p.id === wPrec.value).bytes)
const kvBytes = computed(() => KV_PREC.find(p => p.id === kvPrec.value).bytes)
const optBytes = computed(() => OPTIMIZERS.find(o => o.id === optimizer.value).bytes)

/* 权重（推理/训练共用） */
const weightBytes = computed(() => {
  const p = moe.value ? activeParams.value : params.value
  void p
  const base = params.value * B          // MoE：总参必须全部加载
  const q = trainMode.value === 'QLoRA' && tab.value === 'train' ? 0.5 : wBytes.value
  return base * q
})

/* 可训练参数量 */
const trainable = computed(() => {
  if (trainMode.value === '全参') return params.value * B
  const r = loraR.value
  if (loraScope.value === 'attn') return L.value * 4 * 2 * h.value * r
  return L.value * (4 * 2 * h.value * r + 2 * (h.value * r + r * ffn.value) + (ffn.value * r + r * h.value))
})

/* KV Cache（按注意力结构分形态） */
const kvTotal = computed(() => {
  const b = batch.value, C = conc.value, s = seq.value
  const kb = kvBytes.value
  const effS = attn.value === 'SWA' ? Math.min(s, win.value || s) : s
  switch (attn.value) {
    case 'MHA':  return 2 * L.value * nq.value * dHead.value * effS * b * C * kb
    case 'GQA':
    case 'SWA':  return 2 * L.value * nkv.value * dHead.value * effS * b * C * kb
    case 'MQA':  return 2 * L.value * 1 * dHead.value * effS * b * C * kb
    case 'MLA':
    case 'DSA':  return L.value * dc.value * s * b * C * kb
    case 'CSA2': return (L.value * dc.value * s * b * C * kb) / 4
    default:     return 0
  }
})

/* 对照：同一模型若用 MHA 会是多少 */
const kvIfMHA = computed(() => 2 * L.value * nq.value * dHead.value * seq.value * batch.value * conc.value * kvBytes.value)

/* 激活值 */
const ckptFactor = computed(() => (techs.value.ckpt ? 1 / Math.sqrt(Math.max(1, L.value)) : 1))
const actInfer = computed(() => weightBytes.value * 0.30)
const actTrain = computed(() => 34 * seq.value * batch.value * h.value * 2 * L.value * ckptFactor.value)

/* 框架开销 / 多 GPU 开销 */
const frameBytes = computed(() => frameworkOverhead.value * B)
const multiGpu = computed(() => (gpus.value > 1 ? 0 * B : 0))   // 无公开公式 → 显示为待估

/* 账本 */
const ledger = computed(() => {
  if (tab.value === 'infer') {
    return [
      { key: 'w',  label: '模型权重',    bytes: weightBytes.value, color: '#0d7d6e', formula: 'Φ × 权重位宽' },
      { key: 'kv', label: 'KV Cache',   bytes: kvTotal.value,     color: '#4f46e5', formula: attn.value === 'MLA' || attn.value === 'DSA' ? 'L·d_c·s·b·C·B' : attn.value === 'CSA2' ? 'MLA ÷ 4' : '2·L·n_kv·d_head·s·b·C·B' },
      { key: 'a',  label: '激活值',      bytes: actInfer.value,    color: '#b45309', formula: '权重 × 30%' },
      { key: 'f',  label: '框架开销',    bytes: frameBytes.value,  color: '#7c3aed', formula: '经验值 1~2 GB' },
      { key: 'g',  label: '多GPU开销',   bytes: multiGpu.value,    color: '#64748b', formula: '【推断】单卡≈0' },
    ]
  }
  const opt = trainable.value * optBytes.value * (techs.value.opt8 ? 0.25 : 1) * (techs.value.pure16 ? 0.5 : 1)
  const grad = trainable.value * 2 * (techs.value.pure16 ? 1 : 1)
  const act = actTrain.value * (techs.value.flash ? 0.75 : 1) * (techs.value.fused ? 0.92 : 1) * (techs.value.dynpad ? 0.9 : 1)
  return [
    { key: 'w',  label: '模型权重',     bytes: weightBytes.value, color: '#0d7d6e', formula: 'Φ × 位宽字节' },
    { key: 'gr', label: '梯度',         bytes: grad,              color: '#8b1a1a', formula: '可训练参数 × 2 B' },
    { key: 'os', label: '优化器状态',    bytes: opt,               color: '#be123c', formula: `可训练参数 × ${optBytes.value} B` },
    { key: 'a',  label: '激活值',        bytes: act,               color: '#b45309', formula: '34·s·b·h·2B·L' },
    { key: 'f',  label: '框架开销',      bytes: frameBytes.value,  color: '#7c3aed', formula: '经验值 1~2 GB' },
  ]
})

const totalBytes = computed(() => ledger.value.reduce((s, it) => s + it.bytes, 0))
const gpuGB = computed(() => GPU_MEM[gpuIdx.value].gb)
const usage = computed(() => (totalBytes.value / B) / gpuGB.value)

/* 判定词（档位为站点自定，界面实测仅见过「非常高」；档表标注【待核实】） */
const verdict = computed(() => {
  const u = usage.value
  if (u > 0.90) return { word: '非常高', tone: 'crit', hint: '已逼近上限，任何额外开销都会 OOM' }
  if (u > 0.70) return { word: '偏高',   tone: 'warn', hint: '建议预留 20% 余量，注意显存碎片' }
  if (u > 0.50) return { word: '充足',   tone: 'ok',   hint: '可尝试加大 batch 或序列长度' }
  return { word: '可以', tone: 'good', hint: '余量充裕，可上更大并发' }
})

/* 每卡摊分 */
const perCard = computed(() => {
  const d = Math.max(1, tp.value * pp.value)
  const dp = Math.max(1, Math.round(gpus.value / d))
  const z = dp > 1 ? zero.value : 0
  const out = []
  for (const it of ledger.value) {
    let div = d
    if (it.key === 'os') div = d * (z >= 1 ? dp : 1)
    else if (it.key === 'gr') div = d * (z >= 2 ? dp : 1)
    else if (it.key === 'w') div = d * (z >= 3 || (tab.value === 'infer' && false) ? dp : 1)
    else if (z >= 3 && tab.value === 'train' && it.key === 'w') div = d * dp
    out.push({ ...it, bytes: it.bytes / div })
  }
  return { rows: out, dp, total: out.reduce((s, r) => s + r.bytes, 0) }
})

/* 吞吐：decode 阶段的带宽上界（memory-bound） */
const bwBound = computed(() => {
  const g = GPU_MEM[gpuIdx.value]
  return g.bw / (weightBytes.value / B)          // GB/s ÷ GB = 1/s
})
const estThroughput = computed(() => Math.max(0, bwBound.value * effFactor.value))
const costPerM = computed(() => {
  const rent = GPU_MEM[gpuIdx.value].rent
  const tps = estThroughput.value
  return tps > 0 ? (rent / (tps * 3600)) * 1e6 : 0
})

/* 成本 / 绿色 AI */
const dailyKwh = computed(() => (power.value / 1000) * 24)
const dailyCost = computed(() => dailyKwh.value * elecPrice.value)
const yearlyCo2 = computed(() => dailyKwh.value * 365 * carbonInt.value)

/* 训练时长（按 3 轮 × 样本数 × 序列 / 吞吐 的粗估，仅作量级） */
const trainHours = computed(() => {
  const samples = 10000, epochs = 3, s = Math.min(seq.value, 512)
  const tokens = samples * epochs * s
  const tps = estThroughput.value > 0 ? estThroughput.value : 1
  return tokens / (tps * 0.35) / 3600       // 0.35 = 训练侧经验效率系数
})

/* 格式化 */
const fmt = (bytes) => (bytes / B >= 1 ? (bytes / B).toFixed(2) + ' GB' : (bytes / 1e6).toFixed(0) + ' MB')
const pct = (bytes) => (totalBytes.value > 0 ? (bytes / totalBytes.value) * 100 : 0)
const kvRatio = computed(() => (kvTotal.value > 0 ? kvIfMHA.value / kvTotal.value : 0))
</script>

<template>
  <section class="p9-calc" aria-label="显存与容量规划计算器">
    <!-- 顶栏 -->
    <header class="bar">
      <div class="tabs" role="tablist">
        <button
          v-for="t in [{ id: 'infer', label: '推理' }, { id: 'train', label: '微调' }]"
          :key="t.id" role="tab" :aria-selected="tab === t.id"
          class="tab" :class="{ on: tab === t.id }" @click="tab = t.id"
        >{{ t.label }}</button>
      </div>
      <div class="gauge" :data-tone="verdict.tone">
        <svg viewBox="0 0 120 120" class="ring" aria-hidden="true">
          <circle cx="60" cy="60" r="52" class="ring-bg" />
          <circle
            cx="60" cy="60" r="52" class="ring-fg"
            :stroke-dasharray="`${Math.min(1, usage) * 326.7} 326.7`"
          />
        </svg>
        <div class="gauge-txt">
          <b>{{ (usage * 100).toFixed(1) }}%</b>
          <span>{{ verdict.word }}</span>
        </div>
      </div>
      <p class="gauge-sub">{{ fmt(totalBytes) }} / 共 {{ gpuGB }} GB · {{ verdict.hint }}</p>
    </header>

    <div class="grid">
      <!-- 左：参数 -->
      <div class="col">
        <fieldset>
          <legend>① 模型</legend>
          <label class="row sel">
            <span>选择模型</span>
            <select :value="presetId" @change="presetId = $event.target.value; applyPreset($event.target.value)">
              <option v-for="m in MODELS" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </label>
          <div class="kv2">
            <label class="row"><span>总参数量 (B)</span><input type="number" step="0.1" v-model.number="params" /></label>
            <label class="row"><span>MoE 激活参数量 (B)</span><input type="number" step="0.1" v-model.number="activeParams" :disabled="!moe" /></label>
          </div>
          <label class="check"><input type="checkbox" v-model="moe" /><span>混合专家架构 (MoE)</span></label>
          <label class="row sel">
            <span>注意力机制结构</span>
            <select v-model="attn">
              <option v-for="a in ATTN" :key="a.id" :value="a.id">{{ a.label }}</option>
            </select>
          </label>
          <p class="tip">{{ ATTN.find(a => a.id === attn).note }} · 存储档：{{ ATTN.find(a => a.id === attn).storage }}</p>
        </fieldset>

        <fieldset>
          <legend>② 输入参数</legend>
          <label class="row sel"><span>序列长度</span>
            <select v-model.number="seq"><option v-for="v in SEQ" :key="v" :value="v">{{ v.toLocaleString() }}</option></select>
          </label>
          <label class="row"><span>批量大小 <b>{{ batch }}</b></span>
            <input type="range" min="1" max="8" step="1" v-model.number="batch" />
          </label>
          <label class="row"><span>并发用户数 <b>{{ conc }}</b></span>
            <input type="range" min="1" max="16" step="1" v-model.number="conc" />
          </label>
          <label class="row sel"><span>推理量化</span>
            <select v-model="wPrec"><option v-for="p in W_PREC" :key="p.id" :value="p.id">{{ p.label }}</option></select>
          </label>
          <label class="row sel"><span>KV 缓存量化</span>
            <select v-model="kvPrec"><option v-for="p in KV_PREC" :key="p.id" :value="p.id">{{ p.label }}</option></select>
          </label>
        </fieldset>

        <fieldset v-if="tab === 'train'">
          <legend>③ 训练</legend>
          <label class="row sel"><span>训练模式</span>
            <select v-model="trainMode"><option>全参</option><option>LoRA</option><option>QLoRA</option></select>
          </label>
          <label class="row" v-if="trainMode !== '全参'"><span>LoRA 秩 r <b>{{ loraR }}</b></span>
            <input type="range" min="4" max="128" step="4" v-model.number="loraR" />
          </label>
          <label class="row sel" v-if="trainMode !== '全参'"><span>LoRA 挂载范围</span>
            <select v-model="loraScope"><option value="attn">仅注意力 q/k/v/o</option><option value="full">全线性层（含 MLP）</option></select>
          </label>
          <label class="row sel"><span>优化器类型</span>
            <select v-model="optimizer"><option v-for="o in OPTIMIZERS" :key="o.id" :value="o.id">{{ o.label }}</option></select>
          </label>
          <label class="row"><span>梯度累积 <b>{{ accum }}</b></span>
            <input type="range" min="1" max="8" step="1" v-model.number="accum" />
          </label>
          <p class="tip">可训练参数量：{{ (trainable / 1e6).toFixed(2) }} M（{{ (trainable / (params * B) * 100).toFixed(3) }}% of 总参）</p>
          <div class="chips">
            <label v-for="(t, k) in { flash: 'Flash Attention', fused: '融合内核', dynpad: '动态填充', pack: '序列打包', ckpt: '梯度检查点', opt8: '8 位优化器', paged: '分页优化器', pure16: '纯 16 位训练' }" :key="k" class="chip" :class="{ on: techs[k] }">
              <input type="checkbox" v-model="techs[k]" /><span>{{ t }}</span>
            </label>
          </div>
        </fieldset>

        <fieldset>
          <legend>④ 硬件与并行</legend>
          <label class="row sel"><span>设备 / GPU</span>
            <select v-model.number="gpuIdx"><option v-for="(g, i) in GPU_MEM" :key="g.label" :value="i">{{ g.label }}</option></select>
          </label>
          <div class="kv3">
            <label class="row"><span>GPU 数</span><input type="number" min="1" step="1" v-model.number="gpus" /></label>
            <label class="row"><span>PP</span><input type="number" min="1" step="1" v-model.number="pp" /></label>
            <label class="row"><span>TP</span><input type="number" min="1" step="1" v-model.number="tp" /></label>
          </div>
          <label class="row sel" v-if="tab === 'train'"><span>ZeRO 阶段</span>
            <select v-model.number="zero"><option :value="0">不启用</option><option :value="1">阶段 1 · 优化器状态</option><option :value="2">阶段 2 · + 梯度</option><option :value="3">阶段 3 · + 权重</option></select>
          </label>
          <p class="tip">3D 网格：{{ tp }}TP × {{ pp }}PP × {{ perCard.dp }}DP　·　配置有效：{{ gpus % (tp * pp) === 0 ? '是' : '否（TP×PP 应整除 GPU 数）' }}</p>
          <button class="more" @click="expanded = !expanded">{{ expanded ? '收起' : '展开' }}架构与成本细项</button>
          <div v-if="expanded" class="adv">
            <div class="kv3">
              <label class="row"><span>层数 L</span><input type="number" v-model.number="L" /></label>
              <label class="row"><span>隐藏维度 h</span><input type="number" v-model.number="h" /></label>
              <label class="row"><span>Q 头数</span><input type="number" v-model.number="nq" /></label>
              <label class="row"><span>KV 头数</span><input type="number" v-model.number="nkv" /></label>
              <label class="row"><span>FFN 维度</span><input type="number" v-model.number="ffn" /></label>
              <label class="row"><span>词表大小</span><input type="number" v-model.number="vocab" /></label>
              <label class="row"><span>KV 潜变量 d_c</span><input type="number" v-model.number="dc" /></label>
              <label class="row"><span>滑动窗口 W</span><input type="number" v-model.number="win" /></label>
            </div>
            <div class="kv2">
              <label class="row"><span>框架开销 (GB) <b>{{ frameworkOverhead }}</b></span><input type="range" min="1" max="2" step="0.01" v-model.number="frameworkOverhead" /></label>
              <label class="row"><span>带宽效率系数 <b>{{ effFactor }}</b></span><input type="range" min="0.15" max="0.9" step="0.01" v-model.number="effFactor" /></label>
              <label class="row"><span>电价 ($/kWh) <b>{{ elecPrice }}</b></span><input type="range" min="0.04" max="0.35" step="0.01" v-model.number="elecPrice" /></label>
              <label class="row"><span>碳强度 (kg/kWh) <b>{{ carbonInt }}</b></span><input type="range" min="0.05" max="0.8" step="0.001" v-model.number="carbonInt" /></label>
              <label class="row"><span>功耗 (W) <b>{{ power }}</b></span><input type="range" min="150" max="1200" step="1" v-model.number="power" /></label>
            </div>
          </div>
        </fieldset>
      </div>

      <!-- 右：账本 -->
      <div class="col">
        <div class="card">
          <h3>内存分配</h3>
          <div class="stack" role="img" :aria-label="`显存分项占比，总 ${fmt(totalBytes)}`">
            <span
              v-for="it in ledger" :key="it.key"
              class="seg" :style="{ width: pct(it.bytes) + '%', background: it.color }"
              :title="`${it.label} ${fmt(it.bytes)}`"
            />
          </div>
          <table class="led">
            <thead><tr><th>项</th><th>公式</th><th class="num">占用</th><th class="num">占比</th></tr></thead>
            <tbody>
              <tr v-for="it in ledger" :key="it.key">
                <td><i class="dot" :style="{ background: it.color }" />{{ it.label }}</td>
                <td class="f">{{ it.formula }}</td>
                <td class="num">{{ fmt(it.bytes) }}</td>
                <td class="num">{{ pct(it.bytes).toFixed(1) }}%</td>
              </tr>
            </tbody>
            <tfoot><tr><td colspan="2">合计</td><td class="num"><b>{{ fmt(totalBytes) }}</b></td><td class="num">{{ (usage * 100).toFixed(1) }}%</td></tr></tfoot>
          </table>
          <p class="tip" v-if="tab === 'infer' && kvRatio > 1.05">
            同一模型若用 <b>MHA</b>，KV 将是现在的 <b>{{ kvRatio.toFixed(1) }} 倍</b>（{{ fmt(kvIfMHA) }}）——这是"换注意力结构"的量级。
          </p>
        </div>

        <div class="card">
          <h3>性能与成本</h3>
          <dl class="stats">
            <div><dt>带宽上界吞吐</dt><dd>{{ bwBound.toFixed(0) }} t/s</dd></div>
            <div><dt>估算吞吐（×{{ effFactor }}）</dt><dd>{{ estThroughput.toFixed(0) }} t/s</dd></div>
            <div><dt>租金</dt><dd>${{ GPU_MEM[gpuIdx].rent.toFixed(2) }}/hr</dd></div>
            <div><dt>$/百万 token</dt><dd class="hl">${{ costPerM.toFixed(4) }}</dd></div>
            <div><dt>每天电费</dt><dd>${{ dailyCost.toFixed(3) }}</dd></div>
            <div><dt>每年 CO₂</dt><dd>{{ yearlyCo2.toFixed(1) }} kg</dd></div>
            <div v-if="tab === 'train'"><dt>预计训练时长</dt><dd>{{ trainHours.toFixed(1) }} h</dd></div>
            <div v-if="tab === 'train'"><dt>训练总成本（On-Demand）</dt><dd>${{ (trainHours * GPU_MEM[gpuIdx].rent).toFixed(2) }}</dd></div>
          </dl>
        </div>

        <div class="card" v-if="gpus > 1">
          <h3>每卡摊分（TP {{ tp }} × PP {{ pp }} × DP {{ perCard.dp }}{{ zero && tab === 'train' ? ` · ZeRO-${zero}` : '' }}）</h3>
          <table class="led">
            <thead><tr><th>项</th><th class="num">每卡</th></tr></thead>
            <tbody>
              <tr v-for="r in perCard.rows" :key="r.key"><td>{{ r.label }}</td><td class="num">{{ fmt(r.bytes) }}</td></tr>
            </tbody>
            <tfoot><tr><td>每卡合计</td><td class="num"><b>{{ fmt(perCard.total) }}</b></td></tr></tfoot>
          </table>
          <p class="tip">DP 是<b>复制</b>不是切分——纯 DP 不省显存，必须配 ZeRO。</p>
        </div>
      </div>
    </div>

    <footer class="foot">
      <p>参数与 <a href="/training/p9/16-calculator">9-15</a> 词典同源；公式与 <a href="/training/p9/02-ledger-overview">9-2</a> 账本一致。
        所有数值为<b>量级估算</b>，不同框架/版本差异可达 ±20%，不用于替代实测。</p>
    </footer>
  </section>
</template>

<style scoped>
.p9-calc {
  --c-crit: #b91c1c; --c-warn: #b45309; --c-ok: #0d7d6e; --c-good: #4338ca;
  margin: 24px 0; padding: 18px;
  border: 1px solid var(--vp-c-divider); border-radius: 14px;
  background:
    radial-gradient(620px 220px at 100% 0%, rgba(79, 70, 229, .07), transparent 62%),
    var(--vp-c-bg-elv);
  color: var(--vp-c-text-1);
  font-variant-numeric: tabular-nums;
}
.p9-calc * { box-sizing: border-box; }

/* 顶栏：移动端纵向堆叠 */
.bar { display: flex; flex-direction: column; gap: 12px; align-items: center; padding-bottom: 14px; border-bottom: 1px dashed var(--vp-c-divider); }
.tabs { display: inline-flex; padding: 3px; border-radius: 10px; background: var(--vp-c-bg-alt); }
.tab { min-height: 44px; padding: 0 20px; border: 0; border-radius: 8px; background: transparent; color: var(--vp-c-text-2); font: inherit; font-weight: 600; cursor: pointer; transition: background .15s, color .15s; }
.tab.on { background: var(--vp-c-brand-2); color: #fff; }
.gauge { position: relative; width: 116px; height: 116px; }
.ring { width: 116px; height: 116px; transform: rotate(-90deg); }
.ring-bg { fill: none; stroke: var(--vp-c-bg-alt); stroke-width: 11; }
.ring-fg { fill: none; stroke: var(--c-ok); stroke-width: 11; stroke-linecap: round; transition: stroke-dasharray .35s, stroke .25s; }
.gauge[data-tone='crit'] .ring-fg { stroke: var(--c-crit); }
.gauge[data-tone='warn'] .ring-fg { stroke: var(--c-warn); }
.gauge[data-tone='good'] .ring-fg { stroke: var(--c-good); }
.gauge-txt { position: absolute; inset: 0; display: grid; place-content: center; text-align: center; line-height: 1.15; }
.gauge-txt b { font-size: 21px; font-family: var(--vp-font-family-mono); }
.gauge-txt span { font-size: 12px; font-weight: 700; letter-spacing: .06em; color: var(--vp-c-text-2); }
.gauge[data-tone='crit'] .gauge-txt span { color: var(--c-crit); }
.gauge[data-tone='warn'] .gauge-txt span { color: var(--c-warn); }
.gauge-sub { margin: 0; font-size: 13px; color: var(--vp-c-text-3); text-align: center; }

/* 主体：移动优先单列，≥900px 双列 */
.grid { display: grid; grid-template-columns: 1fr; gap: 18px; padding-top: 16px; }
@media (min-width: 900px) { .grid { grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr); } }
@media (min-width: 900px) { .bar { flex-direction: row; align-items: center; } .gauge { margin-left: auto; } .gauge-sub { text-align: right; max-width: 200px; margin: 0 0 0 12px; } }
.col { display: flex; flex-direction: column; gap: 14px; min-width: 0; }

fieldset { margin: 0; padding: 12px 13px 14px; border: 1px solid var(--vp-c-divider); border-radius: 12px; background: var(--vp-c-bg-alt); }
legend { padding: 0 7px; font-size: 12px; font-weight: 700; letter-spacing: .07em; color: var(--vp-c-brand-2); text-transform: uppercase; }
.row { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 44px; font-size: 13.5px; }
.row > span { color: var(--vp-c-text-2); flex: 1 1 auto; }
.row b { font-family: var(--vp-font-family-mono); color: var(--vp-c-brand-2); }
.kv2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; }
.kv3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(96px, 1fr)); gap: 4px 12px; }
@media (max-width: 520px) { .kv2, .kv3 { grid-template-columns: 1fr; } }
.row input[type='number'], .row select {
  flex: 0 0 auto; min-height: 36px; min-width: 88px; max-width: 148px; padding: 6px 9px;
  border: 1px solid var(--vp-c-divider); border-radius: 8px; background: var(--vp-c-bg-elv);
  color: var(--vp-c-text-1); font: inherit; font-size: 13px;
}
.row input[type='range'] { flex: 1 1 auto; min-width: 84px; accent-color: var(--vp-c-brand-2); }
.check, .chip { display: inline-flex; align-items: center; gap: 7px; min-height: 36px; font-size: 13px; cursor: pointer; }
.check input, .chip input { accent-color: var(--vp-c-brand-2); width: 16px; height: 16px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px 8px; margin-top: 6px; }
.chip { padding: 4px 11px; border: 1px solid var(--vp-c-divider); border-radius: 999px; background: var(--vp-c-bg-elv); color: var(--vp-c-text-2); }
.chip.on { border-color: var(--vp-c-brand-2); background: var(--vp-c-brand-soft); color: var(--vp-c-brand-3); font-weight: 600; }
.tip { margin: 8px 0 0; font-size: 12px; line-height: 1.55; color: var(--vp-c-text-3); }
.more { width: 100%; min-height: 40px; margin-top: 8px; border: 1px dashed var(--vp-c-divider); border-radius: 9px; background: transparent; color: var(--vp-c-brand-2); font: inherit; font-size: 12.5px; font-weight: 600; cursor: pointer; }
.more:hover { border-color: var(--vp-c-brand-2); }
.adv { margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--vp-c-divider); display: flex; flex-direction: column; gap: 2px; }

.card { padding: 14px; border: 1px solid var(--vp-c-divider); border-radius: 12px; background: var(--vp-c-bg-elv); }
.card h3 { margin: 0 0 11px; font-size: 14px; letter-spacing: .02em; }
.stack { display: flex; width: 100%; height: 26px; margin-bottom: 12px; border-radius: 7px; overflow: hidden; background: var(--vp-c-bg-alt); }
.seg { height: 100%; transition: width .3s; }
.seg:first-child { border-radius: 7px 0 0 7px; }
.seg:last-child { border-radius: 0 7px 7px 0; }

.led { width: 100%; margin: 0 !important; border-collapse: collapse; font-size: 12.5px; }
.led th, .led td { border: 0 !important; border-bottom: 1px solid var(--vp-c-divider) !important; padding: 7px 6px !important; text-align: left; }
.led th { background: transparent !important; color: var(--vp-c-text-3); font-weight: 600; font-size: 11.5px; }
.led .num { text-align: right; font-family: var(--vp-font-family-mono); white-space: nowrap; }
.led .f { color: var(--vp-c-text-3); font-family: var(--vp-font-family-mono); font-size: 11px; }
.led tfoot td { border-bottom: 0 !important; padding-top: 9px !important; }
.dot { display: inline-block; width: 9px; height: 9px; margin-right: 7px; border-radius: 3px; }

.stats { display: grid; grid-template-columns: 1fr 1fr; gap: 9px 12px; margin: 0; }
@media (max-width: 520px) { .stats { grid-template-columns: 1fr; } }
.stats > div { padding: 8px 10px; border-radius: 9px; background: var(--vp-c-bg-alt); }
.stats dt { font-size: 11.5px; color: var(--vp-c-text-3); }
.stats dd { margin: 3px 0 0; font-family: var(--vp-font-family-mono); font-size: 15px; font-weight: 600; }
.stats dd.hl { color: var(--vp-c-accent); }
.foot { margin-top: 16px; padding-top: 12px; border-top: 1px dashed var(--vp-c-divider); }
.foot p { margin: 0; font-size: 12px; line-height: 1.6; color: var(--vp-c-text-3); }

@media (prefers-reduced-motion: reduce) {
  .tab, .seg, .ring-fg { transition: none !important; }
}
</style>
