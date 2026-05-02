# 架构设计

## 系统架构

```
┌─────────────────────────────────────────┐
│           Hermes/OpenClaw 运行时          │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Agent    │  │ 飞书网关   │  │ 工具   │ │
│  │ Runtime  │  │ Gateway  │  │ 注册表  │ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │            │      │
│       └──────────────┴────────────┘      │
│                      │                   │
│           ┌──────────┴──────────┐        │
│           │   PilotFlow 插件     │        │
│           │                     │        │
│           │  ┌───────────────┐  │        │
│           │  │ 项目管理工作流  │  │        │
│           │  └───────┬───────┘  │        │
│           │          │          │        │
│           │  ┌───────┴───────┐  │        │
│           │  │ 飞书项目工具   │  │        │
│           │  └───────────────┘  │        │
│           └─────────────────────┘        │
└─────────────────────────────────────────┘
```

## 组件说明

### Hermes 运行时（底座）

| 组件 | 职责 |
| --- | --- |
| Agent Runtime | LLM 调用、对话管理、工具调度 |
| 飞书网关 | WebSocket 连接、@mention 解析、消息收发、互动卡片 |
| 工具注册表 | 插件注册工具、工具发现、权限校验 |

### PilotFlow 插件

| 组件 | 职责 |
| --- | --- |
| 项目管理工作流 | 意图提取 → 计划生成 → 确认门控 → 执行 → 总结 |
| 飞书项目工具 | 封装 lark-cli 调用，提供文档、表格、任务、消息工具 |

## 工具列表

| 工具 | 说明 | 输出 |
| --- | --- | --- |
| `pilotflow_generate_plan` | 从自然语言提取项目信息 | 结构化项目计划 |
| `pilotflow_detect_risks` | 检测计划中的潜在风险 | 风险列表 + 建议 |
| `pilotflow_create_project_space` | 一键创建全套项目产物 | 文档 + 表格 + 任务 + 消息 |
| `pilotflow_send_summary` | 发送执行总结到群聊 | 总结消息 |

## 状态模型

```
IDLE → PLAN_GENERATED → AWAITING_CONFIRMATION → EXECUTING → COMPLETED
                                                     ↓
                                                  FAILED → RETRY
```

| 状态 | 触发条件 | 下一步 |
| --- | --- | --- |
| IDLE | 初始状态 | 收到用户消息 → PLAN_GENERATED |
| PLAN_GENERATED | LLM 解析完成 | 展示计划 → AWAITING_CONFIRMATION |
| AWAITING_CONFIRMATION | 计划卡片已发送 | 用户确认 → EXECUTING |
| EXECUTING | 调用飞书 API | 全部成功 → COMPLETED，失败 → FAILED |
| COMPLETED | 所有产物创建完成 | 发送总结 → IDLE |
| FAILED | 某步 API 调用失败 | 重试或报错 |

## 工具路由

PilotFlow 工具通过 Hermes 工具注册表注册，使用 `pilotflow` toolset 前缀。LLM 根据用户意图选择调用：

1. 用户 @PilotFlow → 飞书网关路由到 Agent
2. Agent 分析意图，调用 `pilotflow_generate_plan`
3. Agent 展示计划，等待确认
4. 用户确认后，Agent 调用 `pilotflow_create_project_space`
5. Agent 调用 `pilotflow_send_summary` 完成闭环

## 依赖关系

```
PilotFlow 插件
  ├── lark-cli（Feishu API 命令行工具）
  ├── Hermes 工具注册表（tools/registry）
  └── 环境变量（.env）
```

PilotFlow 不直接调用飞书 API，而是通过 lark-cli 间接调用。这样做的好处：
- lark-cli 处理认证、重试、错误格式化
- PilotFlow 代码保持简洁，专注业务逻辑
- 可以在终端独立调试每个 API 调用
