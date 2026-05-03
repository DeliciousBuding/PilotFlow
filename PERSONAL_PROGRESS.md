# 个人进度 — PilotFlow

## 项目定位

PilotFlow 是飞书群聊中的 AI 项目运行官。用户在群里 @PilotFlow 说一句需求，LLM 自动理解意图，调用飞书 API 创建真实文档、任务和项目入口消息。

**技术栈**：Hermes Agent（Python）+ lark_oapi SDK + OpenAI-compatible LLM

## 开发历程

### 第一阶段：原型验证（4月）

最初用 TypeScript 自建 Agent，实现了确定性计划解析和飞书工具调用。通过飞书群实测发现核心问题：
- 没有 LLM 接入，本质是脚本而非 AI
- 确认门控未生效，消息一次性全部发出
- 中英文混杂，产品化程度不足

**关键决策**：放弃自建 Agent，转向 Hermes Agent 运行时。

### 第二阶段：架构重构（5月初）

将项目从 TypeScript 自建 Agent 重构为 Hermes Python 插件：
- 研究 Hermes 源码，理解插件注册、工具调度、飞书网关机制
- 用 `ctx.register_tool()` 注册 PilotFlow 工具
- 配置 Hermes gateway 连接飞书 WebSocket
- 配置 OpenAI-compatible LLM

### 第三阶段：插件完善（5月2日）

从 lark-cli 子进程调用迁移到 lark_oapi SDK 直连：
- 修复工具 handler 签名（`**kwargs` 兼容 Hermes 注入的 `task_id`）
- 新增 @mention 支持（解析群成员列表，文档内 mention_user 元素）
- 文档格式化写入（markdown → 飞书 block_type：标题、列表、分隔线）
- 创建文档后自动开放链接访问权限
- 排查 gateway 消息接收问题（FEISHU_GROUP_POLICY=open）

### 第四阶段：端到端验证

完整链路跑通：
```
飞书群 @PilotFlow → Hermes gateway 收消息 → LLM 理解意图
→ 调用 pilotflow_create_project_space → 创建飞书文档 + 多维表格 + 任务 + 群消息
→ bot 回复用户，~30秒完成

多轮管理：
飞书群 @PilotFlow → "把答辩项目的截止时间改成5月10日"
→ LLM 调用 pilotflow_update_project → 发送更新通知
```

### 第五阶段：质量加固（v0.9）

代码质量全面审计和修复：
- 确认门控从全局布尔值改为按 chat_id 隔离，支持多群并发
- 成员缓存增加定期过期清理，防止内存泄漏
- 任务创建移除静默重试，返回明确成功/失败状态
- 日历事件创建结果透明化，成功时计入产物列表
- SKILL.md/DESCRIPTION.md 职责分离（完整 vs 发现提示）
- 修复工具数量声明（7→6，与实际注册一致）
- 新增 AGENTS.md 供 Claude Code agent 使用
- plugin.yaml 版本同步至 0.9.0

### 第六阶段：深度审计修复（v0.9.1）

基于 Hermes 源码和飞书 SDK 源码的三方审计，修复所有确认的 bug：

**Hermes 集成修复：**
- `get_session_env()` 调用签名修正（原来缺参数，永远走 env fallback）
- `_hermes_send` 成功检测逻辑重写（registry 返回 `{"error": ...}` 表示失败）
- lark_oapi client 增加 10 秒超时，防止 gateway 线程阻塞
- `_check_available` 结果缓存，避免重复 import

**线程安全修复：**
- `_member_cache` 加独立锁 `_member_cache_lock`
- `_evict_caches` 中变量作用域修复（`expired_plans` 初始化）

**错误处理增强：**
- `_add_editors` 每个成员的 permission create 检查响应并记录失败
- `_create_bitable` 字段创建检查响应
- `_add_editors` 成员数上限 20，防止无界 API 调用
- `_resolve_member` 增加 `resp.data` 空值检查
- `_hermes_send` 增加类型安全（`isinstance(result, str)`）

**SDK 修复：**
- 分隔线 Divider 使用正确的 `DocDivider.builder().build()` 而非 `{}`
- 日历事件增加 `calendar_id("primary")` 参数

**数据修复：**
- 多维表格中负责人字段使用纯文本，不再混入 `@mention` XML 标记
- 新增 `_member_names_plain()` 辅助函数

**产品修复：**
- 工具描述全面加强（写明参数格式、前置条件、LLM 行为指引）
- 移除确认卡片中无回调处理的按钮（防止用户点击无响应）
- SKILL.md 移除冗余的 send_summary 步骤
- INSTALL.md 补全缺失的飞书权限（bitable/drive/calendar）
- INSTALL.md 修复验证命令（加 sys.path）
- INSTALL.md 统一模型配置说明

### 第七阶段：功能真实性修复（v0.9.2-v0.9.3）

竞赛评审审计发现的核心问题：功能声称与实现不符。

**v0.9.2 — 文档一致性修复：**
- ARCHITECTURE.md 补全 6 个工具 + 多轮管理流程
- README_EN.md 模型配置说明同步
- PRODUCT_SPEC.md 移除已删除的互动按钮描述
- INNOVATION.md 重新分类功能状态
- query_status 新增内存项目注册表（解决 tenant token 无法查询任务的问题）
- 日历事件使用 UTC+8 时区

**v0.9.3 — update_project 从通知变为真实更新：**
- `_handle_update_project` 重写：更新内存注册表 + 更新多维表格记录 + 发送通知
- `_create_bitable` 返回 app_token/table_id/record_id 元数据，支持后续更新
- `_update_bitable_record` 新函数：调用 `app_table_record.update` API
- 模糊匹配项目名称（子串匹配）
- 日历事件修复为 9:00 AM 开始、1 小时时长（原来零时长）
- 新增 15 个单元测试（模板检测、成员格式化、注册表、确认门控、缓存驱逐）

### 第八阶段：Hermes 深度融合（v1.0）

Hermes memory 集成 + 结构化计划输出 + schema 加固：
- `_save_to_hermes_memory`: 项目创建时通过 `registry.dispatch("memory")` 保存项目模式
- LLM 下次创建项目时可参考历史模式，自动建议成员和交付物
- `_handle_generate_plan` 返回结构化 `plan` 对象（含模板预填充的交付物和截止时间）
- `create_project_space` schema 的 `required` 增加 `members` 和 `deliverables`
- `_pending_plans` 存储计划参数，防止 LLM 参数幻觉
- README 竞品对比表新增「学习能力」行，路线图更新至 Phase 5 完成
- INNOVATION.md/PRODUCT_SPEC.md 同步更新

### 第九阶段：文档同步 + 代码清理（v1.0.1-v1.0.2）

- `_pending_plans` 增加过期清理（与 `_plan_generated` 同步驱逐）
- README_EN.md 竞品对比表新增 Learning/memory 行
- README_EN.md 路线图 Phase 4-5 更新为已完成
- README_EN.md 核心优势表新增 "Gets Smarter" 行
- 删除 `_build_confirmation_card` 死代码（按钮移除后不再使用）

### 第十阶段：任务深化（v1.1）

飞书任务从占位符升级为有意义的项目管理实体：
- `_create_task` 新增 `assignee_name`、`deadline`、`chat_id` 参数
- 任务创建时自动解析成员 → open_id，设置负责人
- 任务截止时间设为 deadline 当天 18:00（UTC+8）
- 交付物与成员轮询分配（round-robin）
- 新字段用 try/except 保护，SDK 不支持时优雅降级

### 第十一阶段：项目看板增强（v1.1.4-v1.2）

LLM 输出一致性 + 项目看板可视化：
- `display` 字段：预格式化中文摘要行，防止 LLM 幻觉 URL
- display 包含完整信息：标题、文档、表格、成员、交付物、截止时间、日历、通知
- 截止时间倒计时：🟢/🟡/🔴 色标指示紧急程度
  - 🔴 已逾期：截止日期已过
  - 🔴 剩余 ≤3 天：紧急
  - 🟡 剩余 4-7 天：注意
  - 🟢 剩余 >7 天：正常
- `_pending_plans` 过期清理（与确认门控同步驱逐）
- 静默异常替换为 debug 日志

### 第十二阶段：真实测试 + 深度 Hermes 集成（v1.4-v1.6）

真实编码和测试发现的关键修复 + 深度 Hermes 能力融合：

**v1.4 — 修复双重 JSON 编码 bug（关键）：**
- `tool_result(json.dumps({...}))` 导致所有工具返回值被双重编码
- 修复为 `tool_result({...})`，`tool_result` 内部调用 `json.dumps`
- 在 hermes-agent 环境中实际测试发现并修复

**v1.5 — 截止提醒 via Hermes cron jobs：**
- `_schedule_deadline_reminder`: 项目创建时 best-effort 调度截止前 1 天提醒
- 通过 `registry.dispatch("cronjob", {...})` 深度融合 Hermes 调度系统
- 自动计算提醒时间：明天截止 → 1小时后提醒，远期 → 截止前1天 9:00 AM
- 已过期项目跳过提醒

**v1.6 — 互动确认卡片 with 按钮回调：**
- 利用 Hermes gateway 的 card action callback 机制，并在插件侧注册 `/card` 桥接命令
- 确认卡片发送在 `generate_plan` 阶段（正确时机）
- 按钮点击被 gateway 路由为 `/card button {json}` 合成命令
- 插件桥接处理合成命令并调用 `pilotflow_handle_card_action`

**测试：**
- 19 个单元测试 + 集成测试（全部通过）
- 在 hermes-agent 环境中测试完整流程
- 测试 cron job 调度（6 种截止时间场景）
- 测试互动卡片 JSON 结构

### 第十三阶段：安装自动化 + 集成测试（v1.9-v1.10）

- `setup.py` 自动化安装脚本：复制插件、复制技能、检查环境变量、验证安装
- `tests/test_integration.py` 集成测试（6 个测试，模拟完整 gateway 流程）
- 25 个测试全部通过（19 单元 + 6 集成）
- README/INSTALL 更新为使用 setup.py 安装

### 第十四阶段：状态收敛 + 卡片 action 工具（v1.11-v1.12）

- 工具描述继续加强：`pilotflow_generate_plan` 默认发送确认卡片，并明确文字确认/卡片确认两条路径
- 新增 `pilotflow_handle_card_action` 注册工具：处理 Hermes 合成的 `/card button {...}` 命令
- 确认按钮从 `_pending_plans` 恢复参数，避免 LLM 重新提取导致字段漂移
- 取消按钮清理确认门控和 pending plan，防止用户取消后仍能执行
- Hermes memory 写入内容本地化，避免英文技术痕迹进入用户侧记忆
- README 移除 star badge，避免公开仓库早期数据影响观感
- `plugin.yaml` 同步到 1.12.0

当前边界：以上能力已在代码和本地测试层面完成；真实飞书已验证互动卡片发送、按钮确认续跑和原卡片状态更新，录屏与真实产物链接作为提交材料继续补齐。

### 第十五阶段：产品化包装与交付口径（v1.13）

- README / INSTALL / 复赛材料统一到 47 测试通过的当前口径
- 真实飞书按钮确认、取消和原卡片状态反馈已经可演示
- 对外文档改成“已验证 + 提交前补齐录屏与链接”，不再写成内部排障笔记
- 2026-05-03 追加 lark-cli 真实状态查询验证：Bot 返回中文文本反馈和 `interactive` 项目看板卡片，脱敏证据写入 `docs/LIVE_TEST_EVIDENCE.md`

## 已验证能力

| 能力 | 状态 | 技术实现 |
| --- | --- | --- |
| 飞书文档创建 | ✅ | lark_oapi docx API，markdown 格式化 |
| 文档权限自动开放 | ✅ | drive permission_public.patch |
| 飞书任务创建 | ✅ | lark_oapi task v2 API，负责人分配 + 截止时间 |
| 群消息发送 | ✅ | lark_oapi im message create |
| @mention（群消息） | ✅ | 解析群成员 open_id，<at> 标签 |
| @mention（文档内） | ✅ | docx mention_user 元素 |
| 权限自管理 | ✅ | 链接可查看 + 群成员自动加编辑权限 |
| 多维表格自建 | ✅ | 自动创建表格、字段、记录、权限 |
| LLM 意图理解 | ✅ | Hermes OpenAI-compatible provider + pilotflow skill |
| 端到端群聊触发 | 真实群已验证 | Hermes gateway WebSocket，约 30 秒创建核心项目产物 |
| 确认门控 | ✅ | 代码级拦截 + 线程安全 + 按群聊隔离 |
| 项目模板识别 | ✅ | 答辩/sprint/活动/上线 模板自动建议 |
| 项目状态查询 | ✅ | 内存项目注册表 + 飞书任务 API 双源查询 |
| 多轮项目更新 | ✅ | 注册表更新 + 多维表格 record.update + 群通知 |
| Hermes Memory 写入 | ✅ | best-effort 调用 registry.dispatch("memory") 保存项目模式 |
| Hermes Memory 读取 | 待验证 | 生成计划时读取历史模式、自动建议成员/交付物 |
| 卡片 action 工具 | ✅ | `pilotflow_handle_card_action` 处理确认/取消 |
| 卡片按钮续跑 | 真实按钮确认与原卡片状态更新已验证 | 插件 `/card` 桥接处理真实飞书按钮点击 |
| 真实状态看板 | ✅ | lark-cli 群内状态查询，Bot 返回中文文本 + interactive 看板卡片 |
| 文本消息走 Hermes | ✅ | registry.dispatch("send_message") |
| 互动卡片直发飞书 | ✅ | lark_oapi IM API，`msg_type=interactive` |
| 安装脚本校验 | ✅ | 校验插件/skill 复制、`.env` 占位符、Hermes `config.yaml` |
| Memory 隐私默认 | ✅ | 默认只保存成员数量，不持久化成员姓名 |

## 技术决策

| 决策 | 原因 | 权衡 |
| --- | --- | --- |
| 基于 Hermes 而非自建 | 不重复造轮子，LLM + 工具调度开箱即用 | 受限于 Hermes 架构 |
| lark_oapi SDK 而非 lark-cli | 零外部依赖，即插即用 | 需自己处理 API 错误 |
| Python 而非 TypeScript | Hermes 生态全 Python | 放弃旧 TS 代码 |
| OpenAI-compatible LLM | 跟随 Hermes provider 配置 | 不绑定特定私有服务 |
| 插件而非 fork | 不改 Hermes 代码，通过 setup.py 安装到运行时 | 无法修改 gateway 行为 |

## 项目结构

```
PilotFlow/
├── plugins/pilotflow/      # 核心插件（tools.py + __init__.py + plugin.yaml）
├── skills/pilotflow/       # Hermes skill（SKILL.md + DESCRIPTION.md）
├── docs/                   # 产品规格、架构设计、创新点
├── README.md / README_EN.md
├── INSTALL.md
├── AGENTS.md               # Claude Code agent 上下文
├── PERSONAL_PROGRESS.md
└── .env.example
```

## 迭代方向

| 方向 | 说明 |
| --- | --- |
| 多轮项目管理 | 改截止时间、查状态、重新分配成员 |
| 日历集成 | 自动创建截止时间日历事件 |
| 审批流 | 飞书审批 API 集成 |
| Hermes memory 读取 | 记住并复用用户项目偏好 |
| 互动卡片录屏 | 按钮点击真实续跑和取消 |
