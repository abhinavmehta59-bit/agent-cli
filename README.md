# Agent CLI — Deploy AI Agents from Your Terminal

<p align="center">
  <img src="https://img.shields.io/badge/Version-0.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10+-orange.svg" alt="Python">
</p>

**Agent CLI** is a command-line platform for deploying autonomous AI agents. Think of it as "Hermes for everyone else" — launch, manage, and monitor AI agents with simple commands.

## Quick Start

```bash
# Install
cd ~/.hermes/agent-cli
pip install -e .

# Run setup wizard
python3 -m agent_cli setup-wizard

# Start an agent
agent-cli start email-agent

# Check status
agent-cli status

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

## Agent Templates

| Template | Description |
|----------|-------------|
| **email-agent** | Gmail + CRM + auto-respond + follow-ups |
| **social-agent** | Content pipeline + scheduling + posting |
| **research-agent** | Web search + reports + knowledge base |
| **full-stack** | All of the above combined |

## Architecture

```
agent-cli/
├── agent_cli/
│   ├── __init__.py
│   ├── __main__.py      # Main CLI entry point
│   └── templates.json   # Agent definitions
├── setup-wizard.py      # Interactive setup
├── pyproject.toml       # Package config
├── docs/
│   └── index.html       # Landing page
└── tests/
    └── test_cli.py      # Test suite
```

## Development

```bash
# Run tests
python -m pytest tests/

# Install in dev mode
pip install -e .

# Format code
ruff check .
```

## Requirements

- Python 3.10+
- Hermes (installed at `~/.hermes/hermes-agent/venv/bin/hermes`)

## License

MIT License — Copyright (c) 2024