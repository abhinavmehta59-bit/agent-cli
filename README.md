# Agent CLI — Deploy AI Agents from Your Terminal

<p align="center">
  <img src="https://img.shields.io/badge/Version-0.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Python-3.9+-orange.svg" alt="Python">
  <a href="https://github.com/abhinavmehta59-bit/agent-cli/actions"><img src="https://github.com/abhinavmehta59-bit/agent-cli/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
</p>

**Agent CLI** is a command-line platform for deploying autonomous AI agents. Think of it as "Hermes for everyone else" — launch, manage, and monitor AI agents with simple commands.

## Installation

```bash
pip install agent-cli
```

Or install from source:

```bash
git clone https://github.com/abhinavmehta59-bit/agent-cli.git
cd agent-cli
pip install -e .
```

## Quick Start

```bash
# Run setup wizard to configure your agent
python -m agent_cli setup-wizard

# Start an agent
agent-cli start email-agent

# Check status
agent-cli status

# Stop an agent
agent-cli stop email-agent

# Monitor (auto-restart crashed agents)
agent-cli monitor
```

## Commands

| Command | Description |
|---------|-------------|
| `agent-cli start <agent>` | Launch an agent via Hermes gateway |
| `agent-cli stop <agent>` | Stop a running agent |
| `agent-cli status` | Show dashboard with running agents |
| `agent-cli logs <agent>` | View agent logs |
| `agent-cli deploy <agent>` | Generate systemd service for production |
| `agent-cli monitor` | Run daemon with auto-restart on crash |
| `agent-cli monitor -r 5` | Monitor with max 5 restart retries |

### Status Dashboard Example

```
==================================================
🤖 AGENT CLI — STATUS DASHBOARD
==================================================

📈 Running: 1/4 agents

Agent                Status       PID      Uptime
--------------------------------------------------
email-agent          🟢 running   72393    5m
social-agent         ⚪ stopped   
research-agent       ⚪ stopped   
full-stack           ⚪ stopped   
--------------------------------------------------

💡 Commands:
   agent-cli start <agent>   — Start an agent
   agent-cli stop <agent>    — Stop an agent
   agent-cli logs <agent>    — View logs
   agent-cli deploy          — Deploy to production
```

## Agent Templates

| Template | Description |
|----------|-------------|
| **email-agent** | Gmail + CRM + auto-respond + follow-ups |
| **social-agent** | Content pipeline + scheduling + posting |
| **research-agent** | Web search + reports + knowledge base |
| **full-stack** | All of the above combined |

## Development

```bash
# Run tests
python -m pytest tests/

# Install in dev mode
pip install -e .

# Check syntax
python -m py_compile agent_cli/__main__.py
```

## Requirements

- Python 3.9+
- [Hermes](https://github.com/abhinavmehta59-bit/hermes) (installed at `~/.hermes/hermes-agent/venv/bin/hermes`)

## License

MIT License — Copyright (c) 2024

---

Built with ⚡ for solo founders and small agencies.