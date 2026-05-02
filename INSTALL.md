# 安装指南

PilotFlow 是 Hermes Agent 的插件。以下步骤将引导你完成从零到运行的全过程。

## 前置条件

| 依赖 | 版本要求 | 说明 |
| --- | --- | --- |
| Python | 3.12+ | Hermes 运行时要求 |
| uv | 最新版 | Python 包管理器 |
| Node.js | 18+ | lark-cli 运行要求 |
| lark-cli | 最新版 | Feishu API 命令行工具 |

## 第一步：安装 Hermes Agent

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
uv sync
```

## 第二步：安装 lark-cli

```bash
npm install -g @anthropic-ai/lark-cli
```

配置 lark-cli 飞书凭证：

```bash
lark-cli auth login --profile pilotflow-contest
```

按提示完成飞书应用授权。需要以下权限：
- `im:message:send` — 发送消息
- `docx:document:create` — 创建文档
- `bitable:record:create` — 写入多维表格
- `task:task:create` — 创建任务
- `im:message:pin` — 固定消息

## 第三步：安装 PilotFlow 插件

```bash
git clone https://github.com/DeliciousBuding/PilotFlow.git
cp -r PilotFlow/plugins/pilotflow hermes-agent/plugins/
```

## 第四步：配置环境变量

```bash
cp PilotFlow/.env.example hermes-agent/.env
```

编辑 `hermes-agent/.env`，填入以下内容：

```env
# LLM 配置
OPENAI_BASE_URL=https://api.vectorcontrol.tech/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=mimo-v2.5-pro

# PilotFlow 配置
PILOTFLOW_LARK_PROFILE=pilotflow-contest
PILOTFLOW_TEST_CHAT_ID=oc_xxxxxxxxxxxxxxxx
PILOTFLOW_BASE_TOKEN=your-bitable-token
PILOTFLOW_BASE_TABLE_ID=your-table-id
```

### 获取配置值

| 变量 | 获取方式 |
| --- | --- |
| `PILOTFLOW_TEST_CHAT_ID` | 飞书群设置 → 群号 → 以 `oc_` 开头 |
| `PILOTFLOW_BASE_TOKEN` | 飞书多维表格 URL 中的 token 部分 |
| `PILOTFLOW_BASE_TABLE_ID` | 飞书多维表格 URL 中的 table 部分 |

## 第五步：启动

```bash
cd hermes-agent
uv run hermes
```

启动后在飞书群里 @PilotFlow 发一条消息即可测试。

## 验证安装

```bash
# 检查 lark-cli 是否可用
lark-cli --version

# 检查 PilotFlow 插件是否加载
cd hermes-agent
uv run python -c "from plugins.pilotflow import register; print('PilotFlow loaded OK')"
```

## 常见问题

### lark-cli 找不到

```
FileNotFoundError: lark-cli not found
```

确认 npm global bin 目录在 PATH 中：`npm bin -g`

### 飞书 API 权限不足

检查 lark-cli profile 的授权范围，确保包含了所有必需权限。

### LLM 连接失败

确认 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 正确。测试：

```bash
curl $OPENAI_BASE_URL/models -H "Authorization: Bearer $OPENAI_API_KEY"
```
