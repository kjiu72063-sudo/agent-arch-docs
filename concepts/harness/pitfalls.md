---
title: 3-3 harness 常见坑 + 自检
---

# 3-3 · harness 常见坑 + 掌握自检

harness 最容易"看起来搭了、实际兜不住"。本页依据教材《Harness Engineering 从入门到精通实战》（[S11](/practice/sources)）的**踩坑指南**给出六条真实翻车姿势（症状 / 原因 / 解法），再给落地清单与三档自检。

## 教材六条踩坑

### 坑① AGENTS.md 写太长

| | |
|---|---|
| **症状** | Agent 的输出质量**反而下降**了，经常忽略部分规则 |
| **原因** | 上下文窗口被指令文件占满，留给"正事"的空间不够 |
| **解法** | 砍到 **50–100 行**；超出的内容移到 `docs/`，`AGENTS.md` 里只留链接 |

### 坑② Linter 规则太多，Agent 陷入死循环

| | |
|---|---|
| **症状** | Agent 修了一个 Checkstyle 错误，又触发了另一个 ArchUnit 错误，**反复循环** |
| **解法** | ① **逐条添加** Linter 规则，每加一条都让 Agent 试跑一遍；② 确保每条规则的 FIX 信息**给出具体代码片段**；③ 互相冲突的规则**只保留一条** |

### 坑③ 版本飘移（Java 8 专属）

| | |
|---|---|
| **症状** | 升级了 Checkstyle 或某个依赖后，本地 `mvn verify` 抛 `UnsupportedClassVersionError` |
| **原因** | 很多工具的最新版已不再支持 Java 8 运行时（Checkstyle 10+、Spring 6+、Maven 4+） |
| **解法** | ① `pom.xml` 显式锁定 Java 8 兼容版本；② `dependabot.yml` 配置 `ignore` 阻止**误升级** |

```yaml
# .github/dependabot.yml —— 防止误升级到要求 Java 11+ 的版本
version: 2
updates:
  - package-ecosystem: maven
    directory: "/"
    schedule: { interval: weekly }
    ignore:
      - dependency-name: "com.puppycrawl.tools:checkstyle"
        update-types: ["version-update:semver-major"]
      - dependency-name: "org.springframework.boot:*"
        update-types: ["version-update:semver-major"]
```
> 要点：`maven-enforcer-plugin` 与 Dependabot `ignore` **不是可选项**，而是 Harness 闭环里的**第零道防线**。

### 坑④ 架构约束太严，阻碍合理的跨层调用

| | |
|---|---|
| **症状** | 某些合理的代码模式被 ArchUnit 拦截，**团队开始绕过规则** |
| **解法** | 设置**豁免白名单**机制（把历史遗留代码排除在规则外，而非放弃规则） |

```java
// 豁免：legacy 包不受"Controller 不得依赖 Mapper"约束
@ArchTest
public static final ArchRule controllerMustNotUseMapperExceptLegacy = noClasses()
    .that().resideInAPackage("..controller..")
    .and().resideOutsideOfPackage("..controller.legacy..")
    .should().dependOnClassesThat().resideInAPackage("..mapper..");
```
> 关键：**要么给规则一个合法出口（豁免），要么团队会给你一个非法出口（绕过）。**

### 坑⑤ Doc-gardening 没人管，文档比不写还误导

| | |
|---|---|
| **症状** | Agent 参考了**过时文档**，写出的代码基于错误的假设 |
| **解法** | ① CI 中加**文档新鲜度检查**；② **每两周**跑一次 doc-gardening Agent；③ 设计文档加 `status` 字段，过期的标记为 `deprecated` |

### 坑⑥ 过度依赖 Agent，忘了"审查环境"

| | |
|---|---|
| **症状** | 只盯着 Agent 的输出，没人审查**环境本身**是否还健康 |
| **解法** | 每周 30 分钟做一次"**环境审查**"，固定问四个问题：<br>① 最近一周的 CI 失败率是否上升？<br>② Checkstyle / ArchUnit 规则是否覆盖了新出现的 bad pattern？<br>③ `AGENTS.md` 和 `docs/` 是否跟代码库一致？<br>④ 是否有人尝试升级到 SB 3.x / Java 11+？ |

## 补充：四类工程反模式（配置级对照）

| 反模式 | ✕ 错误写法 | ✓ 正确写法 |
|---|---|---|
| 权限过宽（all-or-nothing） | `{"permissions": {"allow": ["*"]}}` | `allow` 最小必要 + `deny` 危险动作 + `require_approval` 中间地带 |
| 靠模型自觉守规矩 | 只在 `AGENTS.md` 写"改动必须通过测试" | 机械化门禁（pre-commit + CI），违规 `exit 1` 阻断 |
| 缺 fail-closed | 沙箱不可用就跳过隔离裸跑 | 拿不到安全后端**直接失败**，绝不降级 |
| 熵失控 | 长任务只在内存推进，崩了全丢 | 每阶段落 checkpoint + 归档，可恢复可复现 |

## 落地清单（可勾选）

```text
□ 阶段1 信息层
  □ 创建 AGENTS.md（50–100 行，含技术栈版本基线）
  □ 建立 docs/ 结构化目录
  □ 编写架构文档 + 编码规范文档
  □ 设计文档模板（含 Status 标记）

□ 阶段2 约束层
  □ 配置 maven-enforcer-plugin（锁定 JDK / Maven 版本）
  □ 配置 ArchUnit（分层依赖 + 禁字段注入 + 禁裸 HTTP 客户端）
  □ 配置 Checkstyle + 自定义错误信息（必须显式声明版本）
  □ 配置 SpotBugs + JaCoCo（行覆盖率 ≥ 80%）
  □ CI：setup-java JKD8 + setup-maven + mvn -B clean verify
  □ 把团队口头约定翻译成机械规则

□ 阶段3 自动化层（可选，长期项目推荐）
  □ Git Worktree 隔离验证脚本（含健康检查）
  □ 后台清理 Agent 定时任务
  □ 可观测性堆栈（Actuator + Micrometer + Loki + Prometheus）
  □ 文档新鲜度自动检查
  □ Dependabot 配置（防止误升级）

□ 持续维护
  □ 每周 30 分钟"环境审查"
  □ 每月回顾并更新 ArchUnit / Checkstyle 规则
  □ 每两周运行 doc-gardening Agent
```

> **记住**：核心不是搭建复杂基础设施，而是一个简单闭环——**约束 → 告知 → 验证 → 纠正**。从 `AGENTS.md` 和一条 ArchUnit 规则开始，比什么都不做强一百倍。

## 产物化三档自检

| 档位 | 必须提交的产物 |
|---|---|
| **了解** | 说清 harness 与 prompt/context 的区别，列举七大核心组件 |
| **熟悉** | 为真实项目写一份地图式 `AGENTS.md` + 权限矩阵，并跑通 gate 门禁脚本对"违规改动"返回失败 |
| **精通** | 设计完整 harness：地图式 AGENTS + 分层约束 + 机械化门禁（错误信息含 FIX/See）+ fail-closed + 熵管理，让 agent 长任务在受控环境不跑飞，且越权动作被确定性拦截 |

::: tip 达标判断
"熟悉"档硬指标：你写的门禁脚本在**故意制造违规**（如漏跑测试、格式不合规）时**必然返回失败**——这验证了"机械化守护"真的住了。
:::

::: info 下一章承接
harness 把"能做什么、被什么约束"定死之后，agent 需要在里面**反复执行、验证、重试**——这就是 [04 loop engineering](/concepts/loop)。loop 运行在 harness 内，每轮读写 context、受 harness 权限与预算约束。
:::

::: info 【事实】来源
本页六条踩坑、落地清单、闭环总结均出自教材《Harness Engineering 从入门到精通实战》第 46–48 页（[S11](/practice/sources)）。
:::

> 上一节：[3-2 harness 设计决策 + 验证](/concepts/harness/design) ｜ 下一章：[04 loop engineering](/concepts/loop)
