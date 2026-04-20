# Agent CLI — AI Agent Platform for Solo Founders & Small Agencies

<p align="center">
  <img src="https://img.shields.io/badge/Version-0.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platforms-Telegram%20%7C%20Discord%20%7C%20Slack-purple.svg" alt="Platforms">
</p>

## What is Agent CLI?

Agent CLI is a command-line platform that deploys autonomous AI agents to handle repetitive tasks for solo founders and small agencies. Think of it as having a team of virtual assistants that work 24/7 — handling emails, managing social media, conducting research, and more.

## Target Users

- **Solo Founders** — Bootstrap your productivity with AI assistants
- **Small Agencies** (2-10 people) — Scale operations without hiring
- **Freelancers** — Automate client communication and admin
- **Startup Teams** — Add AI capacity without overhead

## Quick Start

```bash
# Clone and enter directory
cd ~/.hermes/agent-cli

# Run the setup wizard
python3 setup-wizard.py

# Start your agent
python3 agent-cli.py start
```

## Features

### Pre-Built Agent Templates

| Template | Description | Capabilities |
|----------|-------------|--------------|
| **Email Agent** | Smart inbox management | Gmail integration, CRM sync, auto-respond, follow-ups |
| **Social Agent** | Content pipeline automation | Content creation, scheduling, multi-platform posting |
| **Research Agent** | Knowledge automation | Web search, report generation, knowledge base management |
| **Full-Stack** | Everything included | All of the above combined |

### Supported Platforms

- **Telegram** — Direct bot interface
- **Discord** — Server-based multi-agent
- **Slack** — Workspace integration

### Core Capabilities

- Encrypted API key storage
- Sandboxed execution environment
- Audit logging (no sensitive data)
- Easy configuration via JSON
- Extensible skill system

## Architecture

```
agent-cli/
├── agent-cli.py          # Main CLI entry point
├── setup-wizard.py       # Interactive setup
├── agent-templates.json  # Agent definitions
├── security.md           # Security documentation
├── config/               # Runtime configuration
├── agents/               # Agent implementations
└── skills/               # Reusable skill modules
```

## Configuration

Agents are configured via JSON profiles in `config/agents/`:

```json
{
  "name": "my-email-agent",
  "template": "email-agent",
  "platforms": ["telegram"],
  "skills": ["gmail", "crm", "auto-respond"],
  "schedule": "0 9-17 * * 1-5"
}
```

## Security

All sensitive data (API keys, credentials) is:
- Encrypted at rest using AES-256
- Never logged or exposed in audit trails
- Stored in sandboxed local storage

See [security.md](security.md) for full details.

## Requirements

- Python 3.10+
- Telegram Bot Token (for Telegram integration)
- Discord Bot Token (for Discord integration)
- Slack Bot Token (for Slack integration)
- Platform-specific API keys (Gmail, OpenAI, etc.)

## License

MIT License — Copyright (c) 2024

---

**Need help?** Open an issue on GitHub or reach out via the community Discord.