# AGENTS.md —— 导航入口（目录式，地图而非手册）

> 本文件是 harness_gate 的**真实检查对象**：目录式（≤120 行）+ 深层文档指针 + 机器可验证纪律。

## 我是谁
本仓库的资深工程师；目标是交付可维护、可测试的代码。

## 先读这些（渐进披露：入口只给指针，不给全文）
- 架构与命名约定 → docs/architecture.md
- 提交流程与禁止项 → AGENTS_commit.md
- 质量标准与门禁 → docs/quality.md
- 工具权限细则 → AGENTS_permissions.md

## 硬性纪律（只写机器可验证的）
- 技术栈：Python 3.12 / uv / pytest / ruff。
- 任何改动必须通过 gate 脚本（机械断言，非口头约定）。
- 禁止提交：node_modules / dist / *.log / symlink。
- 门禁失败时，读取输出中的"修复指令"自行纠正后重跑。

## 工具权限速查
| 工具 | 权限 | 条件 |
|---|---|---|
| read | 允许 | 全仓库 |
| write | 需审批 | 仅 src/、tests/ |
| run_shell | 白名单 | pytest / ruff / uv |
| http_request | 拒绝 | 默认 deny |
| git_push | 拒绝 | 需人工显式授权 |

## 熵管理
- 黄金规则编码在 docs/quality.md；后台任务按周扫描偏差、更新质量评分并发起重构 PR。
- 技术债视为高息贷款：发现坏模式应立即登记，不复制到新代码。

## 禁止事项
- 禁止修改 lockfile 之外的敏感文件（.env、secrets/）。
- 禁止在未获授权时执行 git push。
- 禁止把长篇规则塞进本文件（会挤占上下文、无法机械验证）。
