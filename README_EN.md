# ✈️ PilotFlow

**Hermes/OpenClaw Project Management Plugin for Feishu**

Turn project discussions in Feishu group chats into confirmed plans, documents, tasks, and status tracking — automatically.

[中文版](README.md)

[![Feishu](https://img.shields.io/badge/Feishu-Native-00A4FF)]()
[![Hermes](https://img.shields.io/badge/Hermes-Plugin-6f42c1)]()
[![GitHub stars](https://img.shields.io/github/stars/DeliciousBuding/PilotFlow?style=social)](https://github.com/DeliciousBuding/PilotFlow/stargazers)

---

## One-liner

**PilotFlow is an AI project operator living in your Feishu group chat.**

Mention @PilotFlow with a requirement in plain language. It extracts goals, members, deliverables, and deadlines, generates an execution plan, and — once confirmed — creates Feishu docs, bitable records, tasks, and a project entry message in one shot.

## Why PilotFlow

| Pain Point | How PilotFlow Solves It |
| --- | --- |
| Key decisions lost in chat threads | AI extracts goals, members, deliverables, deadlines |
| Setting up a project space takes 30 min | One sentence triggers the full Feishu artifact suite |
| AI output requires copy-paste | Calls Feishu API directly to create real docs, tables, tasks |
| AI actions are uncontrollable | Confirmation gate: nothing executes until you approve |
| No traceability when things go wrong | Full run log with every step recorded |

## Core Strengths

| Strength | Description |
| --- | --- |
| **Most Natural Entry Point** | @mention the bot in Feishu — no extra tools needed |
| **AI Does Real Work** | Creates real Feishu docs, tables, tasks via API — not just text |
| **Human Always in Control** | Plan preview before execution; nothing happens without confirmation |
| **Every Step Logged** | Full audit trail: which tool, what result, when |
| **Plug and Play** | Built on Hermes/OpenClaw runtime — no wheel reinvention |

## Architecture

```
Hermes/OpenClaw Runtime (Agent + Feishu Gateway + Tool Registry)
  └── PilotFlow Plugin (Project Management Workflow + Feishu Project Tools)
```

- **Base**: Hermes provides Agent runtime, Feishu gateway, session management, tool registry
- **Plugin**: PilotFlow provides project management workflow and Feishu project tools
- **No duplication**: Feishu messaging, docs, tasks — all provided by Hermes

## Installation

See [INSTALL.md](INSTALL.md) for detailed steps.

```bash
# 1. Install Hermes
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent && uv sync

# 2. Install PilotFlow plugin
git clone https://github.com/DeliciousBuding/PilotFlow.git
cp -r PilotFlow/plugins/pilotflow hermes-agent/plugins/

# 3. Configure environment
cp PilotFlow/.env.example hermes-agent/.env
# Edit .env with your Feishu credentials and LLM API key

# 4. Start
cd hermes-agent && uv run hermes
```

## Verified Feishu Capabilities

| Capability | Product Value |
| --- | --- |
| Feishu IM Messages | Project initiation and result delivery |
| Interactive Cards | Plan display and confirmation UI |
| Feishu Docs | Auto-generated project briefs |
| Feishu Bitable | Project status ledger |
| Feishu Tasks | Action items with assignee support |
| Project Entry Message | Pinned project navigation in group |
| Risk Decision Card | In-group risk identification and resolution |
| Run Log | Full-process logging and error tracing |

## Competitive Positioning

| Dimension | OpenClaw | Feishu Miaoji/Projects | PilotFlow |
| --- | --- | --- | --- |
| Positioning | General Agent infrastructure | Meeting notes / project space | Group chat project operator |
| Entry Point | Personal assistant | Meeting / workspace | Feishu group chat |
| Workflow | General flow, user self-orchestrates | Meeting → todo / project flow | Built-in project ops loop |
| Confirmation | Low-level command approval | None | Project-level semantic approval |
| Traceability | Engineering-level trace | None | Business-level audit |

## Documentation

| Document | Description |
| --- | --- |
| [Installation Guide](INSTALL.md) | Hermes/OpenClaw setup steps |
| [Product Spec](docs/PRODUCT_SPEC.md) | User commitments, feature tiers |
| [Architecture Design](docs/ARCHITECTURE.md) | Components, state model, tool routing |
| [Demo Materials](docs/demo/README.md) | Demo script, Q&A, screenshot checklist |

## Roadmap

| Phase | Goal | Status |
| --- | --- | --- |
| Phase 1 | Plugin foundation: Feishu tools + project workflow | Done |
| Phase 2 | LLM-driven intent understanding and plan generation | Done |
| Phase 3 | Confirmation gate + risk detection + run log | In Progress |
| Phase 4 | Multi-project spaces, Worker preview, self-evolution | Planned |

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=DeliciousBuding/PilotFlow&type=Date)](https://star-history.com/#DeliciousBuding/PilotFlow&Date)

## Acknowledgments

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Agent runtime base
- [OpenClaw](https://openclaw.ai) — Feishu Agent integration reference
- Feishu / Lark Open Platform
- Feishu AI Campus Challenge
