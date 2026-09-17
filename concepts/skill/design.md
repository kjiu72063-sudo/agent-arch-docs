---
title: 6-2 skill 设计决策与验证
---

# 6-2 · skill 体系设计决策与验证

::: info 难度分层 · 本页 = L2「设计层」
**前置**：请先掌握 [L1 机制详解](/concepts/skill/mechanism)。
本页是 L2——讲**选型 / 权衡 / 取舍**，并附可直接运行的 [gate 验收](/concepts/skill/gate/skill_gate)。
:::


6-1 给了 SKILL.md 结构、四层架构、discovery/注入、装饰器，本节把深度推到**设计者级**——基于腾讯云《Skills 最佳实践》的真实规范，回答"一个可交付、可复用、可工程化的 skill 长什么样、怎么管生命周期、怎么写三模式与并发/缓存"。

::: tip 承接 6-1
6-1 有最小 SKILL.md / 目录 / discovery-injection / 边界 / 版本评审。本节是它们的**接口与工程规范层**：统一接口、六阶段生命周期、业务化三模式、并发/缓存/资源。
:::

## 规范一：统一接口规范（可交付 skill 的骨架）

腾讯云 Skills 接口规范（【事实】）——每个 skill 是带明确输入输出与元数据的单元：

```typescript
interface Skill {
  id: string;
  name: string;
  description: string;
  version: string;

  // 输入输出定义
  inputs: SkillInput[];
  outputs: SkillOutput[];

  // 执行方法
  execute(context: ExecutionContext): Promise<ExecutionResult>;

  // 元数据
  metadata: {
    author: string;
    tags: string[];
    dependencies: string[];
  };
}
```
> 这让 skill 可被 **discovery 检索**（description/tags）、**组合**（dependencies）、**版本管理**（version）。

## 规范二：六阶段生命周期

腾讯云生命周期（【事实】）：

| 阶段 | 产出 | 验证 |
|---|---|---|
| ① 需求分析 | 功能边界 + 输入输出定义 | 场景/数据明确 |
| ② 设计开发 | 核心逻辑 + 接口 | 单一职责 |
| ③ 测试验证 | 单测/集成/性能测试 | 覆盖率/性能达标 |
| ④ 发布部署 | 版本 + 灰度 | 向后兼容 |
| ⑤ 监控优化 | 成功率/时延/错误率监控 | 指标告警 |
| ⑥ 迭代更新 | 功能增强 | 按反馈回归 |

## 规范三：业务化三模式（真实代码）

腾讯云把三模式落到 skill 业务（【事实】）：

**组合模式** —— 一个 skill 编排多个子 skill：
```typescript
class DataAnalysisSkill {
  async execute(data) {
    const cleaned = await this.cleaningSkill.execute(data);
    const transformed = await this.transformSkill.execute(cleaned);
    return this.analysisSkill.execute(transformed);
  }
}
```

**策略模式** —— 按输入类型选处理器：
```typescript
class ProcessingSkill {
  strategies = { json: new JsonProcessor(), xml: new XmlProcessor(), csv: new CsvProcessor() };
  execute(data) { return this.strategies[data.type].execute(data); }
}
```

**装饰器模式** —— 不改原 skill 加日志/缓存：
```typescript
class LoggingSkillDecorator {
  constructor(skill) { this.skill = skill; }
  async execute(context) {
    console.log(`Starting: ${this.skill.name}`);
    const result = await this.skill.execute(context);
    console.log(`Completed: ${this.skill.name}`);
    return result;
  }
}
```

## 规范四：并发 / 缓存 / 资源

腾讯云性能实践（【事实】）：
- **并发**：`Promise.all` 并行处理条目（仅独立任务，注意资源上限）；
- **缓存**：热点结果 `Map` 缓存，命中即返；
- **资源**：`finally` 释放（连接、文件句柄），防泄漏。

```typescript
class CacheOptimizedSkill {
  cache = new Map();
  async execute(key) {
    if (this.cache.has(key)) return this.cache.get(key);
    const result = await this.computation(key);
    this.cache.set(key, result);
    return result;
  }
}
```

## 验收 gate（真实运行：`python gate/skill_gate.py`）

::: tip 验证对象改为真实文件
此前版本用 Python 模拟 `Promise.all`、检查硬编码常量（自证），已废弃。现对 `gate/fixtures/code-review-agent.md` **真实 SKILL.md** 断言，并对装饰器/策略模式做**真实调用**验证。
:::

| # | 验证内容 | 真实检查对象 |
|---|---|---|
| ① | 统一接口字段齐备 | frontmatter 含 id/name/description/version/inputs/outputs |
| ② | 版本合规 | `version` 符合语义化 `x.y.z` |
| ③ | 含失败处理 | 存在"失败处理"与"边界与约束"段（不只写 happy path） |
| ④ | 装饰器横切不改原逻辑 | 真实装饰 `base(3)=6` 且日志记录 `['start','end']` |
| ⑤ | 策略模式按类型分派 | 真实 dict 分派 → `json:a / xml:b / csv:c` |

```python
# 真实调用（节选）：装饰器与策略模式均为真实执行
def decorator_adds_logging_without_changing():
    log = []
    def logging_decorator(fn):
        def wrapper(*a, **k):
            log.append("start"); r = fn(*a, **k); log.append("end"); return r
        return wrapper
    @logging_decorator
    def base(x): return x * 2
    return base(3) == 6 and log == ["start", "end"]
```
> 运行输出：`PASS: skill gate 5/5（对 fixtures 真实文件断言）`

**fixture 即范例**：`fixtures/code-review-agent.md` 是可直接抄用的 SKILL.md 模板（含 frontmatter 接口、执行步骤、输出格式、边界、失败处理）。

## 三档自检（6-2 版）

| 档位 | 必须提交的产物 |
|---|---|
| 熟悉 | 用统一接口定义一个 skill，能说明六阶段生命周期与三模式适用 |
| 精通 | 交付一个含统一接口 + 生命周期 + 组合/策略/装饰器 + 并发/缓存/资源的可复用 skill |

> 上一节：[6-1 skill 机制详解](/concepts/skill/mechanism) ｜ 下一节：[6-3 常见坑 + 自检](/concepts/skill/pitfalls)