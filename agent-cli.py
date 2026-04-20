#!/usr/bin/env python3
"""
Agent CLI — Main entry point for managing AI agent workflows.
Target: Solo founders and small agencies.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Constants
CONFIG_DIR = Path.home() / ".hermes" / "agent-cli" / "config"
AGENT_TEMPLATES = Path(__file__).parent / "agent-templates.json"
PID_DIR = CONFIG_DIR / "pids"
LOG_DIR = Path.home() / ".hermes" / "agent-cli" / "logs"

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PID_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_templates() -> dict:
    """Load agent templates from JSON."""
    with open(AGENT_TEMPLATES) as f:
        data = json.load(f)
    # Handle both flat structure and nested {"templates": {...}} structure
    if "templates" in data:
        return data["templates"]
    return data


def get_agent_config(agent_name: str) -> Optional[dict]:
    """Load config for a specific agent."""
    config_file = CONFIG_DIR / f"{agent_name}.json"
    if not config_file.exists():
        return None
    with open(config_file) as f:
        return json.load(f)


def get_pid_file(agent_name: str) -> Path:
    """Get PID file path for an agent."""
    return PID_DIR / f"{agent_name}.pid"


def get_log_file(agent_name: str) -> Path:
    """Get log file path for an agent."""
    return LOG_DIR / f"{agent_name}.log"


def is_running(agent_name: str) -> bool:
    """Check if an agent is currently running."""
    pid_file = get_pid_file(agent_name)
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        # Process dead or no permission - clean up stale PID file
        pid_file.unlink(missing_ok=True)
        return False


def cmd_start(args) -> int:
    """Start one or all agents."""
    templates = load_templates()
    
    # Determine which agents to start
    if args.agent == "all":
        agents_to_start = list(templates.keys())
    else:
        if args.agent not in templates:
            print(f"❌ Unknown agent: {args.agent}")
            print(f"   Available: {', '.join(templates.keys())}")
            return 1
        agents_to_start = [args.agent]
    
    started = []
    failed = []
    
    for agent_name in agents_to_start:
        if is_running(agent_name):
            print(f"⏭️  {agent_name}: already running")
            continue
        
        config = get_agent_config(agent_name)
        if not config:
            print(f"⚠️  {agent_name}: no config found. Run setup-wizard.py first.")
            failed.append(agent_name)
            continue
        
        # Build command to start agent
        # For now, we'll simulate agent startup with a simple background process
        # In production, this would spawn the actual agent process
        log_file = get_log_file(agent_name)
        
        # Create a simple mock agent process
        cmd = [
            sys.executable, "-c",
            f"import time; open('{log_file}', 'w').write(f'{agent_name} started at {{time.time()}}\\n'); "
            f"while True: time.sleep(3600)"
        ]
        
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=open(log_file, "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            pid_file = get_pid_file(agent_name)
            pid_file.write_text(str(proc.pid))
            print(f"✅ {agent_name}: started (PID {proc.pid})")
            started.append(agent_name)
        except Exception as e:
            print(f"❌ {agent_name}: failed to start — {e}")
            failed.append(agent_name)
    
    print(f"\n📊 Started: {len(started)}, Failed: {len(failed)}")
    return 0 if not failed else 1


def cmd_stop(args) -> int:
    """Stop one or all agents."""
    templates = load_templates()
    
    if args.agent == "all":
        agents_to_stop = [k for k in templates.keys() if is_running(k)]
    else:
        agents_to_stop = [args.agent] if is_running(args.agent) else []
    
    if not agents_to_stop:
        print("No agents running.")
        return 0
    
    stopped = []
    for agent_name in agents_to_stop:
        pid_file = get_pid_file(agent_name)
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            # Force kill if still running
            try:
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            pid_file.unlink(missing_ok=True)
            print(f"🛑 {agent_name}: stopped")
            stopped.append(agent_name)
        except Exception as e:
            print(f"❌ {agent_name}: {e}")
    
    print(f"\n📊 Stopped: {len(stopped)}")
    return 0


def cmd_status(args) -> int:
    """Show status dashboard for all agents."""
    templates = load_templates()
    
    print("\n" + "=" * 50)
    print("🤖 AGENT CLI — STATUS DASHBOARD")
    print("=" * 50)
    
    # Summary row
    running = sum(1 for k in templates.keys() if is_running(k))
    total = len(templates)
    print(f"\n📈 Running: {running}/{total} agents\n")
    
    # Agent details
    print(f"{'Agent':<20} {'Status':<12} {'PID':<10} {'Uptime'}")
    print("-" * 50)
    
    for agent_name in templates.keys():
        pid_file = get_pid_file(agent_name)
        log_file = get_log_file(agent_name)
        
        if is_running(agent_name):
            try:
                pid = int(pid_file.read_text().strip())
                # Try to get uptime from log
                uptime = "running"
                if log_file.exists():
                    content = log_file.read_text()
                    if "started at" in content:
                        try:
                            ts = float(content.split("started at ")[1].strip())
                            secs = int(time.time() - ts)
                            uptime = f"{secs}s"
                        except:
                            pass
                print(f"{agent_name:<20} {'🟢 running':<12} {pid:<10} {uptime}")
            except:
                print(f"{agent_name:<20} {'🟡 unknown':<12}")
        else:
            print(f"{agent_name:<20} {'⚪ stopped':<12}")
    
    print("-" * 50)
    
    # Quick actions hint
    print("\n💡 Commands:")
    print("   agent-cli.py start <agent>   — Start an agent")
    print("   agent-cli.py stop <agent>    — Stop an agent")
    print("   agent-cli.py logs <agent>    — View logs")
    print("   agent-cli.py deploy          — Deploy to production")
    
    return 0


def cmd_logs(args) -> int:
    """Show logs for an agent."""
    log_file = get_log_file(args.agent)
    
    if not log_file.exists():
        print(f"No logs found for {args.agent}")
        return 1
    
    lines = log_file.read_text().splitlines()
    if args.lines:
        lines = lines[-args.lines:]
    
    for line in lines:
        print(line)
    
    return 0


def cmd_deploy(args) -> int:
    """Deploy agent(s) to production."""
    templates = load_templates()
    
    if args.agent == "all":
        agents = list(templates.keys())
    else:
        agents = [args.agent]
    
    print("🚀 Deploying to production...")
    print(f"   Agents: {', '.join(agents)}")
    print("   (Production deployment not yet implemented)")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="agent-cli",
        description="Agent CLI — Manage AI agent workflows"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # start command
    start_parser = subparsers.add_parser("start", help="Start an agent")
    start_parser.add_argument(
        "agent",
        nargs="?",
        default="all",
        help="Agent name or 'all' (default: all)"
    )
    start_parser.set_defaults(func=cmd_start)
    
    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop an agent")
    stop_parser.add_argument(
        "agent",
        nargs="?",
        default="all",
        help="Agent name or 'all' (default: all)"
    )
    stop_parser.set_defaults(func=cmd_stop)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show status dashboard")
    status_parser.set_defaults(func=cmd_status)
    
    # logs command
    logs_parser = subparsers.add_parser("logs", help="View agent logs")
    logs_parser.add_argument("agent", help="Agent name")
    logs_parser.add_argument("-n", "--lines", type=int, default=None, help="Number of lines")
    logs_parser.set_defaults(func=cmd_logs)
    
    # deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to production")
    deploy_parser.add_argument(
        "agent",
        nargs="?",
        default="all",
        help="Agent name or 'all' (default: all)"
    )
    deploy_parser.set_defaults(func=cmd_deploy)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())