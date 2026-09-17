---
title: 3-2 harness 设计决策与验证
---

# 3-2 · harness 设计决策与验证

::: info 难度分层 · 本页 = L2「设计层」
**前置**：请先掌握 [L1 机制详解](/concepts/harness/mechanism)。
本页是 L2——讲**落地路线与配置取舍**，并附可直接运行的 [gate 验收](/concepts/harness/gate/harness_gate)。
:::

3-1 讲清了七大组件。本节回答**"到底怎么搭"**——依据教材《Harness Engineering 从入门到精通实战》（[S11](/practice/sources)）的**落地三步走**，给出可直接抄用的配置与决策依据。

## 总览：落地三步走（不要一步到位）

```mermaid
flowchart LR
  A["阶段1 信息层\n1-2 天"] --> B["阶段2 约束层\n3-5 天"]
  B --> C["阶段3 自动化层\n1-2 周"]
  style A fill:#0d7d6e,color:#fff
  style B fill:#b45309,color:#fff
  style C fill:#4f46e5,color:#fff
```

| 阶段 | 内容 | 适合 | 收益 |
|---|---|---|---|
| **1 信息层** | AGENTS.md 地图模式 + docs/ 结构化文档 | 所有项目 | Agent 输出一致性 ↑ |
| **2 约束层** | 分层架构 + Linter + CI 约束检查 + 错误信息含修复指令 | 中期项目 | 代码质量可控（**质变点**） |
| **3 自动化层** | Agent 自验证闭环 + 后台清理 Agent + 覆盖率/截图自动验证 | 长期维护项目 | 人工审查量 ↓↓↓ |

::: warning 很多人失败在这一点
**不要一步到位。** 很多人失败就在于想一次性搭完所有基础设施。**阶段 1 已能带来显著提升，阶段 2 是质变点，阶段 3 是锦上添花。**
:::

## 决策一：AGENTS.md 写地图，不写百科全书（阶段 1）

教材给出的"反面教材 vs 正确做法"对照（【事实】）：

```text
# ❌ 错误示范：把所有内容塞进一个文件
我们使用 Spring Boot 2.7.18 + Java 1.8 + Maven 3.6.3 + MySQL 5.7...
类命名使用 PascalCase，方法用 camelCase，常量用 UPPER_SNAKE_CASE...
ORM 用 MyBatis-Plus，迁移用 Flyway，缓存用 Caffeine...
（后面还有 500 行）
```
> 问题：**挤占上下文窗口、难以维护、Agent 很难定位需要的信息。**

**正确做法**（可直接用，控制在 **50–100 行**）：

```markdown
# AGENTS.md

## 项目简介
[一句话] 面向中小企业的在线项目管理平台，Spring Boot 2.7 + Java 1.8 + MySQL 5.7。

## 技术栈基线（不允许擅自升级）
- JDK: 1.8，不可使用 Java 9+ 语法（record/var/text blocks）
- Spring Boot: 2.7.x，不可升 3.x（Spring 6 要求 JDK 17）
- Maven: 3.6.3，由 enforcer 强制
- 数据库: MySQL 5.7（utf8mb4）

## 快速导航
| 你想做什么 | 去哪里看 |
|-----------|---------|
| 了解系统架构 | docs/architecture/overview.md |
| 了解模块边界和依赖规则 | docs/architecture/boundaries.md |
| 了解编码规范 | docs/conventions/README.md |
| 了解当前迭代任务 | docs/plans/current-sprint.md |
| 了解 API 规范 | docs/reference/api-spec.yaml |

## 硬性规则（必须遵守，CI 会验证）
1. 依赖方向：domain → config → mapper → service → controller
2. 横切关注点只能通过 Spring 注入，禁止 `new` 实例化
3. 单文件 ≤ 300 行；单方法 ≤ 50 行
4. 禁止 `System.out.println` / `e.printStackTrace()`，统一 SLF4J
5. 新增代码必须有 JUnit 5 测试，行覆盖率 ≥ 80%
```

::: tip 三条设计原则
1. **控制在 50–100 行**——超过就说明你在写百科全书了；
2. **"你想做什么 → 去哪里看" 比 "这是什么" 更有效**——面向任务而非面向知识；
3. **硬性规则单独列出**——这些是 CI 会强制验证的，不是"建议"。
:::

**docs/ 结构化知识库**（每个文档头部加元信息，供 doc-gardening Agent 扫描过期）：

```yaml
---
last_updated: 2026-03-28
status: active          # active | deprecated | draft
owner: @zhangsan
---
```

```text
docs/
├── architecture/   overview.md · boundaries.md · data-flow.md
├── conventions/    README.md · naming.md · error-handling.md · testing.md · logging.md
├── design/         feature-auth.md · feature-search.md · feature-billing.md
├── plans/          current-sprint.md · backlog.md
└── reference/      api-spec.yaml · error-codes.md
```

**设计文档模板**（Agent 动手前先填，审批通过再写码——"明确意图"的工程化）：

```markdown
# Feature: [功能名称]
## Status: 📝 Draft | 📋 Approved | 🚧 In Progress | ✅ Implemented
## 目标          — 一句话描述要解决什么问题
## 非目标        — 明确列出这次不做什么（防止 Agent 扩大范围）
## 技术方案      — 涉及的模块 / 数据模型变更 / API 变更
## 验收标准      — 具体的、可验证的标准；测试覆盖率 ≥ 80%
## 依赖          — 依赖哪些已实现的功能
```

## 决策二：把"主观品味"翻译成机械规则（阶段 2）

教材的核心对照表——**左边是团队口头约定（Agent 学不会），右边是机械规则（CI 强制执行）**：

| 团队口头约定 | 机械化规则 | 实现方式 |
|---|---|---|
| "方法要短" | 单方法 ≤ 50 行 | Checkstyle `MethodLength` |
| "文件要短" | 单文件 ≤ 300 行 | Checkstyle `FileLength` |
| "日志要规范" | 禁止 `System.out` / `printStackTrace` | Checkstyle 正则规则 |
| "HTTP 调用要统一" | 禁止裸 `RestTemplate` / `HttpURLConnection` | ArchUnit 自定义规则 |
| "Controller 要纯" | Controller 不得直接调 Mapper | ArchUnit 分层规则 |
| "依赖要构造器注入" | 禁止字段级 `@Autowired` | ArchUnit 注解检查 |
| "不要污染全局" | 禁止 `public static` 非 final 字段 | SpotBugs `MS_*` 规则族 |
| "测试要充分" | 行覆盖率 ≥ 80% | JaCoCo `coverage check` |
| "锁定构建工具版本" | Maven ≥ 3.6.3，JDK = 1.8 | `maven-enforcer-plugin` |

> **经验法则：如果一条规则在 Code Review 中被提过 3 次以上，就应该写成 Linter 规则。**

### 分层依赖检查（真实可用配置）

包结构与依赖方向（教材 Java 8 + Spring Boot 2.7 示例）：

```text
src/main/java/com/example/app/
├── domain/         # 领域模型与 DTO（不依赖任何业务包）
├── config/         # Spring 配置类（只依赖 domain）
├── mapper/         # MyBatis-Plus Mapper（只依赖 domain、config）
├── service/        # 业务逻辑（依赖 domain、config、mapper）
├── controller/     # REST Controller
└── infrastructure/ # 横切关注点：ApiClient、日志、指标、安全
```

**ArchUnit 分层规则**（`src/test/.../architecture/LayerDependencyTest.java`）：

```java
@AnalyzeClasses(packages = "com.example.app",
                importOptions = ImportOption.DoNotIncludeTests.class)
public class LayerDependencyTest {

    @ArchTest
    public static final ArchRule layered = layeredArchitecture()
        .consideringAllDependencies()
        .layer("Domain").definedBy("..domain..")
        .layer("Config").definedBy("..config..")
        .layer("Mapper").definedBy("..mapper..")
        .layer("Service").definedBy("..service..")
        .layer("Controller").definedBy("..controller..")
        .whereLayer("Controller").mayNotBeAccessedByAnyLayer()
        .whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")
        .whereLayer("Mapper").mayOnlyBeAccessedByLayers("Service")
        .as(
            "❌ 层级依赖违规。\n" +
            "✅ FIX: Controller 必须经 Service，Service 通过 MyBatis-Plus Mapper 访问数据。\n" +
            "📖 See: docs/architecture/boundaries.md"
        );
}
```
> 注意：示例字段一律用 `public static final`，是 **Java 8 + JUnit 5** 的字段访问要求。

### 核心决策：错误信息即 Prompt（三要素公式）

**这是 Harness Engineering 最有杠杆的实践之一。** 每条 Linter 报错都必须包含三要素：

```text
❌ [什么错了]
✅ FIX: [怎么改，给出代码片段]
📖 See: [哪个文档有详细说明]
```

```xml
<!-- Checkstyle 正则规则示例：禁止 System.out.println -->
<module name="RegexpSinglelineJava">
    <property name="format" value="System\.out\.println"/>
    <property name="message"
              value="❌ 禁止 System.out.println。
✅ FIX: private static final Logger log = LoggerFactory.getLogger(X.class);
       log.info(&quot;message {}&quot;, arg);
📖 See: docs/conventions/logging.md"/>
</module>
```

> **Agent 看到这种报错，不需要任何额外提示就能自动修复。你写的每一条 Linter 规则，本质上都是一个自动触发的 Prompt。**

### 版本锁定（第零道防线）

```xml
<!-- maven-enforcer-plugin：不达标直接构建失败 -->
<requireMavenVersion>
  <version>[3.6.3,)</version>
  <message>❌ Maven 版本过低。✅ FIX: 使用 Maven 3.6.3 及以上。📖 See: docs/conventions/build.md</message>
</requireMavenVersion>
<requireJavaVersion>
  <version>[1.8,9)</version>
  <message>❌ JDK 版本不符。✅ FIX: 使用 JDK 1.8 编译；不要升级到 9+。</message>
</requireJavaVersion>
```

### CI 管线：完整的 Agent 护栏

```yaml
name: Agent Guardrails
on: [pull_request]
jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: 'temurin', java-version: '8', cache: maven }
      - uses: stCarolas/setup-maven@v5
        with: { maven-version: 3.6.3 }
      # 编译 + 单测 + Checkstyle + SpotBugs + JaCoCo(≥80%) + ArchUnit 全绑定到 verify
      - name: Build & Verify
        run: mvn -B clean verify
      - name: File Size Check
        shell: bash
        run: |
          find src/main/java -name '*.java' | while read f; do
            lines=$(wc -l < "$f")
            if [ "$lines" -gt 300 ]; then
              echo "❌ $f 有 $lines 行（上限 300）"
              echo "✅ FIX: 拆分为更小的类，将辅助方法移至 *Helper 或 infrastructure。"
              echo "📖 See: docs/conventions/file-size.md"
              exit 1
            fi
          done
      - name: Doc Freshness
        shell: bash
        run: |
          find docs/design/ -name '*.md' | while read f; do
            days_old=$(( ( $(date +%s) - $(git log -1 --format=%ct "$f") ) / 86400 ))
            [ "$days_old" -gt 60 ] && echo "⚠️ $f 已 ${days_old} 天未更新，可能已过期"
          done
```

## 决策三：自动化层——让 Agent 自我验证与自我修复（阶段 3）

**后台清理 Agent 任务模板**（对抗熵积累，每个发现生成独立 PR）：

```markdown
# 任务：代码库卫生清理
## 检查清单
1. 超长文件：src/main/java/ 下超过 300 行的 .java，拆分为更小的类
2. 缺失测试：没有对应 *Test.java 的类，补基础测试
3. 未使用的 import；4. 超过 30 天的 TODO/FIXME
5. 重复代码（>10 行）提取为共享工具类；6. docs/design 中 Draft 超 30 天的文档
## 约束
- 每个修复作为独立 PR，不要混在一起
- 每个 PR 修改后必须确保 `mvn -B clean verify` 通过
- PR 标题格式：`chore(cleanup): [具体描述]`
- 不确定是否安全的修改，跳过并在 PR 中标注原因
```

**Git Worktree 隔离验证脚本**（在隔离分支上跑全量校验 + 健康检查）：

```bash
#!/bin/bash
BRANCH=$1; WORKTREE_DIR="/tmp/agent-verify-$(date +%s)"
git worktree add "$WORKTREE_DIR" "$BRANCH" && cd "$WORKTREE_DIR"
java -version 2>&1 | grep '"1.8' || { echo "❌ 必须使用 JDK 1.8"; exit 1; }
mvn -B clean verify || { echo "❌ mvn verify 失败"; exit 1; }
mvn -B spring-boot:run > /tmp/app.log 2>&1 & APP_PID=$!
for i in {1..30}; do
  sleep 2
  if curl -sf http://localhost:8080/actuator/health | grep -q '"status":"UP"'; then
    echo "✅ 健康检查通过"; kill $APP_PID; git worktree remove "$WORKTREE_DIR"; exit 0
  fi
done
echo "❌ 启动失败，最近日志："; tail -n 50 /tmp/app.log; kill $APP_PID; exit 1
```

**可观测性接入**（让 Agent 能"看日志"）：本地起 Loki + Promtail + Prometheus + Grafana；Spring Boot 侧开 Actuator + Micrometer。Agent 排错 prompt 示例：

```text
应用在 /api/users 端点返回 500 错误。
请查看 Loki 日志中最近 5 分钟的错误日志，对照 traceId 找到完整调用链，
定位根因并修复。修复后重新跑 `mvn -B clean verify` 与对应 *Test 验证。
```

## 决策四：纠错成本低、等待成本高（吞吐量下的合并理念）

教材的关键组织结论（【事实】）：**纠错成本低，等待成本高**——这解释了 OpenAI 的 3 人 / 100 万行 / 人均日 3.5 PR。

| 情形 | 决策 | 理由 |
|---|---|---|
| 测试偶发失败 | **重跑** | 纠错成本低 |
| 确定性失败 | 人工介入 | 重跑无意义 |
| 等人工审查 | 尽量并行/后台 | 等待成本 > 纠错成本 |

> 吞吐量体系不是"更多人盯代码"，而是"**让 agent 高吞吐 + 机械兜底 + 人做闸门**"。

## 验收 gate（真实运行：`python gate/harness_gate.py`）

::: tip 验证对象是真实文件
对 `gate/fixtures/` 下**真实文件**断言：`AGENTS.md`（目录式规范）与 `permissions.json`（权限/沙箱配置）。文件缺失或不符合规范即失败。
:::

| # | 验证内容 | 真实检查对象 |
|---|---|---|
| ① | AGENTS.md 是地图式 | 行数 ≤120 且深层指针 ≥3 处 |
| ② | 不沦为手册 | 硬性纪律段 ≤15 行，其余靠指针 |
| ③ | 门禁可自纠（**错误信息三要素**） | `permissions.json` 的 `on_failure` 同时含 `❌` + `✅ FIX` + `📖 See` |
| ④ | 越权被拦截 | `git_push`/`http_request` 在 deny 且不在 allow |
| ⑤ | 沙箱 fail-closed | `sandbox.enabled` 与 `fail_closed` 均为 true |

```python
# 真实断言（节选）：读 fixtures，不再内置字符串
def is_map_style_agents():
    content = load_fixture("AGENTS.md")
    lines = content.splitlines()
    pointers = [l for l in lines if "docs/" in l or "AGENTS_" in l]
    return len(lines) <= 120 and len(pointers) >= 3

def sandbox_is_fail_closed():
    sb = load_fixture("permissions.json")["sandbox"]
    return sb.get("enabled") is True and sb.get("fail_closed") is True
```
> 运行输出：`PASS: harness gate 5/5（对 fixtures 真实文件断言）`

> **fixtures 即范例**：`fixtures/AGENTS.md` 与 `fixtures/permissions.json` 本身就可直接抄用为 harness 配置模板。

## 三档自检（3-2 版）

| 档位 | 你能做到 | 判据（怎么算达标） |
|---|---|---|
| 了解 | 说出三步走各层做什么 | 能说出"阶段 2 是质变点"并解释为什么 |
| 熟悉 | 把 AGENTS.md 写成地图式（≤100 行 + 深层指针） | 门禁报错信息**带 FIX + See**，Agent 读到即可自纠 |
| 精通 | 为一个 3–7 人 agent 团队搭完整 harness | 故意违反分层依赖/超长文件/覆盖率时，**CI 必然阻断**；Dependabot 已 ignore 掉会导致版本飘移的大版本升级 |

::: info 【事实】来源
本页三步走、配置样例、三要素公式、口头约定对照表、CI/Worktree 脚本，均出自教材《Harness Engineering 从入门到精通实战》第 14–48 页（[S11](/practice/sources)）。**具体版本号与依赖以你的项目为准**（【建议】）。
:::

::: tip 生产落地 → Track D
本页的"三步走"是**内容层面**的落地顺序；**项目层面**的阶段与门禁（S0–S5 + G0–G5）见 [D3 生命周期主干](/process/lifecycle) 与 [D4 阶段细则](/process/stages-1)。
:::

> 上一节：[3-1 harness 机制详解](/concepts/harness/mechanism) ｜ 下一节：[3-3 常见坑 + 自检](/concepts/harness/pitfalls)
